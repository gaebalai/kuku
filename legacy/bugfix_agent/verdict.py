"""Verdict parsing and constants for Bugfix Agent v5 (Issue #194 Protocol)

This module provides VERDICT handling with hybrid fallback parsing (Issue #292):
- Verdict: Enum with 4 verdict types (PASS, RETRY, BACK_DESIGN, ABORT)
- parse_verdict: Hybrid fallback parser (Step 1-3)
- ReviewResult: Legacy alias for backward compatibility (deprecated)

Hybrid Fallback Strategy:
- Step 1: Strict Parse - "Result: <STATUS>" pattern
- Step 2: Relaxed Parse - Multiple patterns (Status:, **Status**:, 스테이터스: etc.)
- Step 3: AI Formatter Retry - Uses AI to reformat malformed output

Design Principle (Issue #292 Review):
- Parser returns Verdict enum only (including ABORT)
- AgentAbortError is raised by the orchestrator, not the parser
- InvalidVerdictValueError is raised immediately (no fallback for invalid values)
- This separation ensures single responsibility and reusability
"""

import re
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from .errors import ( # noqa: I001
 AgentAbortError,
 InvalidVerdictValueError,
 VerdictParseError,
)

if TYPE_CHECKING:
 from .tools.base import AIToolProtocol

# Type alias for AI formatter function
AIFormatterFunc = Callable[[str], str]

# Constants (Issue #292: Magic number elimination)
AI_FORMATTER_MAX_INPUT_CHARS: int = 8000
"""AI Formatter 에 전달하다최대입력문자수.
約2000토큰상당.모델의컨텍스트長와 코스트를 고려한값.
"""


class Verdict(Enum):
 """VERDICT판정키ワード (Issue #194 統一프로토콜)

 4종류의판정결과를정의:
 - PASS: 성공·次스테이트へ進행
 - RETRY: 同스테이트再실행(軽微な문제)
 - BACK_DESIGN: 설계見直し이 필요 → DETAIL_DESIGN
 - ABORT: 속행不能·即座에 종료(환경/외부要因)
 """

 PASS = "PASS"
 RETRY = "RETRY"
 BACK_DESIGN = "BACK_DESIGN"
 ABORT = "ABORT"


# Step 2: Relaxed Parse Patterns (Issue #292)
# All patterns explicitly match only valid Verdict values (no wildcards)
# Note: After #293, Result: is the standard format. Status: patterns kept for legacy/edge cases.
RELAXED_PATTERNS: list[str] = [
 # VERDICT 표준포맷(#293 で統一)
 r"Result:\s*(PASS|RETRY|BACK_DESIGN|ABORT)",
 # 리스트형식 (- Result: PASS)
 r"-\s*Result:\s*(PASS|RETRY|BACK_DESIGN|ABORT)",
 # Legacy: Status 형식(旧 Review Result 포맷)
 r"Status:\s*(PASS|RETRY|BACK_DESIGN|ABORT)",
 r"-\s*Status:\s*(PASS|RETRY|BACK_DESIGN|ABORT)",
 r"\*\*Status\*\*:\s*(PASS|RETRY|BACK_DESIGN|ABORT)",
 # 日本語
 r"스테이터스:\s*(PASS|RETRY|BACK_DESIGN|ABORT)",
 # 대입형식 (Status = PASS / Result = PASS)
 r"Status\s*=\s*(PASS|RETRY|BACK_DESIGN|ABORT)",
 r"Result\s*=\s*(PASS|RETRY|BACK_DESIGN|ABORT)",
]

# Step 3: AI Formatter Prompt (Issue #292)
# Note: Output format uses "Result:" to match _parse_verdict_strict()
FORMATTER_PROMPT: str = """이하의출력부터VERDICT를 추출し, 정확한 포맷로출력해 주세요.

## 입력
{raw_output}

## 출력포맷(엄밀에 따라ください)
## VERDICT
- Result: <PASS|RETRY|BACK_DESIGN|ABORT のいずれか1つ>
- Reason: <1행의要約>
- Evidence: <상세>
- Suggestion: <다음アクション>

중요: Result행는必ず "- Result: " で始め, 4つ의 값의いずれか를 출력해 주세요.
"""


def _parse_verdict_strict(text: str) -> Verdict:
 """Step 1: 엄밀파싱 - "Result: <STATUS>" 패턴만

 Args:
 text: 파싱대상의텍스트

 Returns:
 Verdict: 파싱된판정결과

 Raises:
 VerdictParseError: Result행를 찾를 찾을 수 없다, 또는부정한 값
 """
 match = re.search(r"Result:\s*(\w+)", text, re.IGNORECASE)
 if not match:
 raise VerdictParseError("No VERDICT Result found in output")

 result_str = match.group(1).upper()

 try:
 return Verdict(result_str)
 except ValueError as e:
 valid_values = [v.value for v in Verdict]
 # InvalidVerdictValueError is NOT recoverable - indicates prompt violation
 raise InvalidVerdictValueError(
 f"Invalid VERDICT value: {result_str}. Valid values: {valid_values}"
 ) from e


def _parse_verdict_relaxed(text: str) -> Verdict:
 """Step 2: 완화파싱 - 복수패턴로탐색

 All patterns are restricted to valid Verdict values only.
 No wildcards - prevents matching invalid values like "PENDING".

 Args:
 text: 파싱대상의텍스트

 Returns:
 Verdict: 파싱된판정결과

 Raises:
 VerdictParseError: 전패턴로見つ를 찾을 수 없다경우
 """
 for pattern in RELAXED_PATTERNS:
 match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
 if match:
 result_str = match.group(1).upper()
 # Pattern guarantees valid value, no ValueError possible
 return Verdict(result_str)

 raise VerdictParseError("No valid verdict found (relaxed patterns exhausted)")


def parse_verdict(
 text: str,
 ai_formatter: AIFormatterFunc | None = None,
 max_retries: int = 2,
) -> Verdict:
 """VERDICT/Review Result를 파싱(ハイブリッド폴백대응)

 3스텝의폴백전략:
 - Step 1: Strict Parse - "Result: <STATUS>" 패턴
 - Step 2: Relaxed Parse - 복수패턴(Status:, **Status**:, 스테이터스: 등)
 - Step 3: AI Formatter Retry - 최대 max_retries 회

 Design Note (Issue #292 Review):
 - 파서ー는 Verdict enum 를 반환하다만.Verdict.ABORT が返된경우,
 AgentAbortError の送出는 호출원(오케스트레이터ー)의 책무.
 - InvalidVerdictValueError(부정한 값)는即座에 raise され, 폴백대상외.
 이것는 포맷문제이 아니라프롬프트위반/구현버그를示す위해.

 Expected formats:
 ## VERDICT / ## Review Result
 - Result/Status: PASS | RETRY | BACK_DESIGN | ABORT
 - Reason/Summary: <판정이유>
 - Evidence/Details: <판정근거>
 - Suggestion/Next Action: <다음アクション提案>

 Args:
 text: 파싱대상의텍스트
 ai_formatter: AI정형함수 (optional, Step 3用)
 max_retries: Step 3 최대리트라이회수 (default: 2, must be >= 1)

 Returns:
 Verdict: 파싱된판정결과(ABORT포함하다)

 Raises:
 InvalidVerdictValueError: 부정한 VERDICT 값(폴백대상외)
 VerdictParseError: 전스텝실패시
 ValueError: max_retries < 1 의 경우
 """
 # Validate max_retries
 if max_retries < 1:
 raise ValueError(f"max_retries must be >= 1, got {max_retries}")

 # Step 1: Strict Parse
 try:
 return _parse_verdict_strict(text)
 except InvalidVerdictValueError:
 raise # Invalid value is NOT recoverable - re-raise immediately
 except VerdictParseError:
 pass # No Result found - continue to Step 2

 # Step 2: Relaxed Parse
 try:
 return _parse_verdict_relaxed(text)
 except VerdictParseError:
 pass # Continue to Step 3

 # Step 3: AI Formatter Retry
 if ai_formatter is None:
 raise VerdictParseError(
 "All parse attempts failed (Step 1-2). Provide ai_formatter for Step 3 retry."
 )

 # Truncate input for AI formatter using head+tail strategy
 # VERDICT is often at the end, so tail is important
 truncate_delimiter = "\n...[truncated]...\n"
 # Ensure head + delimiter + tail <= MAX (Issue #292 Review: guarantee upper bound)
 usable_chars = AI_FORMATTER_MAX_INPUT_CHARS - len(truncate_delimiter)
 if usable_chars <= 0:
 raise ValueError(
 f"AI_FORMATTER_MAX_INPUT_CHARS ({AI_FORMATTER_MAX_INPUT_CHARS}) "
 f"must be > delimiter length ({len(truncate_delimiter)})"
 )
 half_limit = usable_chars // 2
 if len(text) > AI_FORMATTER_MAX_INPUT_CHARS:
 truncated_text = text[:half_limit] + truncate_delimiter + text[-half_limit:]
 else:
 truncated_text = text

 last_error: VerdictParseError | None = None
 for _attempt in range(max_retries):
 try:
 formatted = ai_formatter(truncated_text)
 # Try strict first, then relaxed (Issue #292 Review: LLM may use Status: format)
 try:
 return _parse_verdict_strict(formatted)
 except InvalidVerdictValueError:
 raise # Invalid value is NOT recoverable
 except VerdictParseError:
 return _parse_verdict_relaxed(formatted)
 except InvalidVerdictValueError:
 raise # Invalid value is NOT recoverable
 except VerdictParseError as e:
 last_error = e
 continue
 # Note: ai_formatter communication errors propagate to caller

 raise VerdictParseError(
 f"All {max_retries} AI formatter attempts failed. Last error: {last_error}"
 )


def _extract_verdict_field(text: str, field_name: str) -> str | None:
 """VERDICT섹션부터지정필드를추출

 Args:
 text: 파싱대상의텍스트
 field_name: 필드명 (e.g., "Reason", "Evidence", "Suggestion",
 "Summary", "Details", "Next Action")

 Returns:
 필드값.見つ를 찾을 수 없다경우는None
 """
 pattern = rf"{field_name}:\s*(.+?)(?=\n-|\n##|\Z)"
 match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
 if match:
 return match.group(1).strip()
 return None


def handle_abort_verdict(verdict: Verdict, raw_output: str) -> Verdict:
 """ABORT verdict 를 처리し, 예외를送出 (Issue #292 책무분리)

 파서ー는 Verdict enum 를 반환하다만로, AgentAbortError の送出は
 이함수(오케스트레이터ー側)의 책무.

 Args:
 verdict: parse_verdict() 의 반환값
 raw_output: 파싱元の生텍스트(reason/suggestion추출용)

 Returns:
 Verdict: ABORT이외의 경우는그まま반환하다

 Raises:
 AgentAbortError: verdict 이 ABORT 의 경우
 """
 if verdict == Verdict.ABORT:
 reason = (
 _extract_verdict_field(raw_output, "Summary")
 or _extract_verdict_field(raw_output, "Reason")
 or "No reason provided"
 )
 suggestion = (
 _extract_verdict_field(raw_output, "Next Action")
 or _extract_verdict_field(raw_output, "Suggestion")
 or ""
 )
 raise AgentAbortError(reason, suggestion)
 return verdict


def create_ai_formatter(
 tool: "AIToolProtocol",
 *,
 context: str = "",
 log_dir: Path | None = None,
) -> AIFormatterFunc:
 """AI 도구를 사용한 formatter 함수를 생성

 Step 3 は"最後の砦"なので, 로그와문맥를보유한다것이중요.

 Args:
 tool: AI 도구(reviewer 등).run() 메서드를 가진다것.
 context: AI 도구에 전달하다컨텍스트(예: ctx.issue_url)
 log_dir: 로그출력선디렉토리(감사·再現性때문)

 Returns:
 AIFormatterFunc: parse_verdict 의 ai_formatter 인수에전달하다함수
 """

 def formatter(raw_output: str) -> str:
 prompt = FORMATTER_PROMPT.format(raw_output=raw_output)
 result: str
 result, _ = tool.run(prompt=prompt, context=context, log_dir=log_dir)
 return result

 return formatter


# Legacy alias for backward compatibility (will be removed in Phase 3)
class ReviewResult(Enum):
 """[DEPRECATED] Use Verdict instead. Will be removed in Phase 3."""

 PASS = "PASS"
 BLOCKED = "BLOCKED" # → Verdict.RETRY
 FIX_REQUIRED = "FIX_REQUIRED" # → Verdict.RETRY
 DESIGN_FIX = "DESIGN_FIX" # → Verdict.BACK_DESIGN

 @classmethod
 def contains(cls, text: str, result: "ReviewResult") -> bool:
 """텍스트에리뷰결과이포함된다か판정"""
 return result.value in text
