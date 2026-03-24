"""Bugfix Agent v5 Orchestrator

Note: Python 3.11+ required
"""

import time
from collections.abc import Callable

from bugfix_agent.agent_context import (
 AgentContext,
 create_default_context,
)

# Phase 3: Import CLI utilities, context, and tools
from bugfix_agent.cli import format_jsonl_line, run_cli_streaming

# Phase 2: Import from separated modules
from bugfix_agent.config import get_config_value
from bugfix_agent.context import build_context
from bugfix_agent.errors import (
 AgentAbortError,
 InvalidVerdictValueError, # Issue #292: 부정값는即 raise
 LoopLimitExceeded,
 ToolError,
 VerdictParseError,
 check_tool_result, # Re-exported for backward compatibility
)
from bugfix_agent.github import post_issue_comment

# Phase 5: Import state handlers
from bugfix_agent.handlers import (
 handle_detail_design,
 handle_detail_design_review,
 handle_implement,
 handle_implement_review,
 handle_init,
 handle_investigate,
 handle_investigate_review,
 handle_pr_create,
)
from bugfix_agent.prompts import load_prompt
from bugfix_agent.run_logger import RunLogger

# Phase 4: Import state machine, workflow, and context
from bugfix_agent.state import (
 ExecutionConfig,
 ExecutionMode,
 SessionState,
 State,
 infer_result_label,
)
from bugfix_agent.tools import (
 AIToolProtocol,
 ClaudeTool,
 CodexTool,
 GeminiTool,
 MockTool,
)
from bugfix_agent.verdict import (
 # Constants (Issue #292)
 AI_FORMATTER_MAX_INPUT_CHARS,
 FORMATTER_PROMPT,
 RELAXED_PATTERNS,
 # Types
 AIFormatterFunc,
 ReviewResult,
 Verdict,
 _extract_verdict_field, # Re-export for backward compatibility
 # Functions
 create_ai_formatter, # Issue #292: Step 3 用 formatter 생성
 handle_abort_verdict,
 parse_verdict,
)

# Note: All components imported from bugfix_agent package (Phase 2-5)

# Explicit re-exports for backward compatibility (ruff F401)
__all__ = [
 # Errors
 "AgentAbortError",
 "InvalidVerdictValueError",
 "LoopLimitExceeded",
 "ToolError",
 "VerdictParseError",
 "check_tool_result",
 # Verdict
 "AI_FORMATTER_MAX_INPUT_CHARS",
 "FORMATTER_PROMPT",
 "RELAXED_PATTERNS",
 "AIFormatterFunc",
 "ReviewResult",
 "Verdict",
 "create_ai_formatter",
 "handle_abort_verdict",
 "parse_verdict",
 "_extract_verdict_field",
 # CLI
 "format_jsonl_line",
 "run_cli_streaming",
 # Context
 "build_context",
 # Tools
 "AIToolProtocol",
 "ClaudeTool",
 "CodexTool",
 "GeminiTool",
 "MockTool",
 # State
 "ExecutionConfig",
 "ExecutionMode",
 "SessionState",
 "State",
 "infer_result_label",
 # Core
 "RunLogger",
 "load_prompt",
 "post_issue_comment",
 "AgentContext",
 "create_default_context",
 # Handlers
 "handle_init",
 "handle_investigate",
 "handle_investigate_review",
 "handle_detail_design",
 "handle_detail_design_review",
 "handle_implement",
 "handle_implement_review",
 "handle_pr_create",
 # Orchestrator
 "STATE_HANDLERS",
 "parse_args",
 "run",
 "list_states",
]


# ==========================================
# 1. State Handler Dispatch
# ==========================================

StateHandler = Callable[[AgentContext, SessionState], State]

STATE_HANDLERS: dict[State, StateHandler] = {
 State.INIT: handle_init,
 State.INVESTIGATE: handle_investigate,
 State.INVESTIGATE_REVIEW: handle_investigate_review,
 State.DETAIL_DESIGN: handle_detail_design,
 State.DETAIL_DESIGN_REVIEW: handle_detail_design_review,
 State.IMPLEMENT: handle_implement,
 State.IMPLEMENT_REVIEW: handle_implement_review,
 State.PR_CREATE: handle_pr_create,
}


# ==========================================
# 2. CLI Parser
# ==========================================


def parse_args() -> ExecutionConfig:
 """CLI인수를파싱하여실행설정를 생성

 Returns:
 ExecutionConfig: 실행설정

 Raises:
 SystemExit: 인수에러시
 """
 import argparse

 parser = argparse.ArgumentParser(
 prog="bugfix_agent_orchestrator",
 description="Bugfix Agent v5 Orchestrator - AI-driven bug fixing workflow automation",
 formatter_class=argparse.RawDescriptionHelpFormatter,
 epilog="""
Examples:
 # 통상실행(FULL 모드)
 %(prog)s --issue https://github.com/apokamo/kamo2/issues/182

 # 단일스테이트실행(SINGLE 모드)
 %(prog)s -i https://github.com/apokamo/kamo2/issues/182 --state INVESTIGATE
 %(prog)s -i https://github.com/apokamo/kamo2/issues/182 --state DETAIL_DESIGN_REVIEW

 # 범위실행(FROM_END 모드)
 %(prog)s -i https://github.com/apokamo/kamo2/issues/182 --from IMPLEMENT
 %(prog)s -i https://github.com/apokamo/kamo2/issues/182 --from QA

 # 도구지정(기본값모델)
 %(prog)s -i https://github.com/apokamo/kamo2/issues/182 -s INIT --tool codex
 %(prog)s -i https://github.com/apokamo/kamo2/issues/182 -s INIT -t gemini

 # 도구＆모델지정
 %(prog)s -i https://github.com/apokamo/kamo2/issues/182 -s INIT --tool-model codex:o4-mini
 %(prog)s -i https://github.com/apokamo/kamo2/issues/182 -s INIT -tm gemini:gemini-2.5-flash

 # 스테이트목록표시
 %(prog)s --list-states
 """,
 )

 # --issue 옵션
 parser.add_argument(
 "--issue",
 "-i",
 type=str,
 help="Target issue URL (예: https://github.com/apokamo/kamo2/issues/182)",
 )

 # --state 옵션 (SINGLE 모드)
 parser.add_argument(
 "--state",
 "-s",
 type=str,
 help="Run single state only (예: INVESTIGATE, DETAIL_DESIGN_REVIEW)",
 )

 # --from 옵션 (FROM_END 모드)
 parser.add_argument(
 "--from",
 "-f",
 dest="from_state",
 type=str,
 help="Run from state to COMPLETE (예: IMPLEMENT, QA)",
 )

 # --list-states 옵션
 parser.add_argument(
 "--list-states", "-l", action="store_true", help="List available states and exit"
 )

 # --tool 옵션 (도구지정)
 parser.add_argument(
 "--tool",
 "-t",
 type=str,
 choices=["codex", "gemini", "claude"],
 help="Override tool for single state execution (codex, gemini, claude)",
 )

 # --tool-model 옵션 (도구:모델지정)
 parser.add_argument(
 "--tool-model",
 "-tm",
 type=str,
 metavar="TOOL:MODEL",
 help="Override tool and model (e.g., codex:o4-mini, gemini:gemini-2.5-flash)",
 )

 args = parser.parse_args()

 # --list-states 의 경우는特별처리(後続로 구현)
 if args.list_states:
 # main() 로 처리한다를 위한마커
 return ExecutionConfig(mode=ExecutionMode.FULL, issue_url="__LIST_STATES__")

 # --issue 이 필수(--list-states 이외)
 if not args.issue:
 parser.error("--issue is required (except for --list-states)")

 # --state 과 --from 의 배타제약
 if args.state and args.from_state:
 parser.error("--state and --from are mutually exclusive")

 # --tool 과 --tool-model 의 배타제약
 if args.tool and args.tool_model:
 parser.error("--tool and --tool-model are mutually exclusive")

 # --tool-model 의 파싱(tool:model 형식)
 tool_override: str | None = None
 model_override: str | None = None

 if args.tool:
 tool_override = args.tool
 elif args.tool_model:
 if ":" not in args.tool_model:
 parser.error("--tool-model must be in format TOOL:MODEL (e.g., codex:o4-mini)")
 parts = args.tool_model.split(":", 1)
 tool_override = parts[0]
 model_override = parts[1]
 if tool_override not in ("codex", "gemini", "claude"):
 parser.error(f"Invalid tool: {tool_override}. Must be codex, gemini, or claude")

 # issue_number 를 추출
 issue_number = int(args.issue.rstrip("/").split("/")[-1])

 # 모드판정
 if args.state:
 # SINGLE 모드
 try:
 target_state = State[args.state]
 except KeyError:
 parser.error(f"Invalid state: {args.state}. Use --list-states to see valid states.")
 return ExecutionConfig(
 mode=ExecutionMode.SINGLE,
 target_state=target_state,
 issue_url=args.issue,
 issue_number=issue_number,
 tool_override=tool_override,
 model_override=model_override,
 )
 elif args.from_state:
 # FROM_END 모드
 try:
 target_state = State[args.from_state]
 except KeyError:
 parser.error(
 f"Invalid state: {args.from_state}. Use --list-states to see valid states."
 )
 return ExecutionConfig(
 mode=ExecutionMode.FROM_END,
 target_state=target_state,
 issue_url=args.issue,
 issue_number=issue_number,
 tool_override=tool_override,
 model_override=model_override,
 )
 else:
 # FULL 모드(기본값)
 return ExecutionConfig(
 mode=ExecutionMode.FULL,
 issue_url=args.issue,
 issue_number=issue_number,
 tool_override=tool_override,
 model_override=model_override,
 )


# ==========================================
# 3. Main Orchestrator
# ==========================================


def run(config: ExecutionConfig, ctx: AgentContext | None = None) -> None:
 """오케스트레이터ー의 메인엔트리 포인트(Phase 2 대응)

 Args:
 config: 실행설정(모드, 대상스테이트, Issue URL)
 ctx: AgentContext(None 라면 create_default_context 로 생성)
 테스트시는 tests.utils.context.create_test_context() 로 생성한도의를전달하다

 Raises:
 ToolError: AI 도구이 에러를返한 경우
 TypeError: ctx 이 AgentContext 로 없는 경우
 ValueError: 핸들러를 찾를 찾을 수 없다경우
 """
 # 컨텍스트초기화(의존性주입대응)
 if ctx is not None and not isinstance(ctx, AgentContext):
 raise TypeError(f"ctx must be AgentContext, got {type(ctx).__name__}")
 if ctx is None:
 ctx = create_default_context(
 config.issue_url,
 tool_override=config.tool_override,
 model_override=config.model_override,
 )
 session_state = SessionState()
 logger = ctx.logger

 # JSONL ロガー초기화
 logger.log_run_start(config.issue_url, ctx.run_timestamp)

 print(f"=== 🚀 Bugfix Agent v5 Started (mode={config.mode.name}) ===")
 print(f"Issue: {config.issue_url}")
 if config.tool_override:
 tool_info = config.tool_override
 if config.model_override:
 tool_info += f":{config.model_override}"
 print(f"Tool Override: {tool_info}")
 print(f"Artifacts: {ctx.artifacts_dir}")

 # 시작스테이트결정
 if config.mode == ExecutionMode.FULL:
 current = State.INIT
 else:
 # SINGLE / FROM_END 모드
 if config.target_state is None:
 raise ValueError(f"target_state is required for mode {config.mode.name}")
 current = config.target_state
 print(f"Starting from: {current.name}")

 # Circuit Breaker 의 설정
 max_loop_count = get_config_value("agent.max_loop_count", 5)
 state_transition_delay = get_config_value("agent.state_transition_delay", 1.0)

 # 메인ループ
 try:
 while current != State.COMPLETE:
 print(f"\n📍 State: {current.name}")
 time.sleep(state_transition_delay)

 # Circuit Breaker: ループ회수제한체크
 for loop_name, count in session_state.loop_counters.items():
 if count >= max_loop_count:
 raise LoopLimitExceeded(
 f"{loop_name} exceeded max limit ({count} >= {max_loop_count})"
 )

 # 핸들러취득
 handler = STATE_HANDLERS.get(current)
 if handler is None:
 raise ValueError(f"No handler for state: {current}")

 # 핸들러실행(로그출력)
 logger.log_state_enter(current.name)
 next_state = handler(ctx, session_state)
 result_label = infer_result_label(current, next_state)
 logger.log_state_exit(current.name, result_label, next_state.name)

 # SINGLE 모드는1회로종료
 if config.mode == ExecutionMode.SINGLE:
 print(f">>> SINGLE mode: stopping after {current.name}")
 break

 # 다음스테이트へ전이
 current = next_state

 # 정상완료
 logger.log_run_end("COMPLETE", session_state.loop_counters)
 print("\n=== ✨ Workflow Completed Successfully! ===")
 print(f"Loop counters: {session_state.loop_counters}")

 except LoopLimitExceeded as e:
 # ループ제한초과時는 정지하여로그출력
 logger.log_state_exit(current.name, "LOOP_LIMIT", current.name)
 logger.log_run_end("LOOP_LIMIT", session_state.loop_counters, error=str(e))
 print(f"\n=== ⚠️ Workflow Stopped (Circuit Breaker): {e} ===")
 raise

 except ToolError as e:
 # 도구에러時는 정지하여로그출력(정지스테이트를 기록)
 logger.log_state_exit(current.name, "ERROR", current.name)
 logger.log_run_end("ERROR", session_state.loop_counters, error=str(e))
 print(f"\n=== ❌ Workflow Failed: {e} ===")
 raise


def list_states() -> None:
 """스테이트목록를표시하여종료"""
 print("\nAvailable States:")
 print(" INIT Issue 필수항목확인(再現환경/절차/期待挙動)")
 print(" INVESTIGATE 再現실행, 期待값와의差, 원인임시説 → Issue 追記")
 print(" INVESTIGATE_REVIEW INVESTIGATE 산출물리뷰")
 print(" DETAIL_DESIGN 상세설계·테스트케이스목록 → Issue 追記")
 print(" DETAIL_DESIGN_REVIEW DETAIL_DESIGN 산출물리뷰")
 print(" IMPLEMENT 브랜치생성, 구현, 테스트실행 → Issue 追記")
 print(" IMPLEMENT_REVIEW IMPLEMENT 산출물리뷰(QA통합)")
 print(" PR_CREATE gh pr create 실행, PR URL 공유")
 print(" COMPLETE 워크플로우완료")
 print("\nOutput: Issue 本文追記 + <STATE> Update 코멘트")
 print("Artifacts: test-artifacts/bugfix-agent/<issue-number>/<YYMMDDhhmm>/<state>/")
 print("\nUsage:")
 print(" --state <STATE> Run single state only")
 print(" --from <STATE> Run from state to COMPLETE")
 print(" --issue <URL> Target issue URL (required)")


if __name__ == "__main__":
 import sys

 # CLI인수를파싱
 config = parse_args()

 # --list-states 의 경우는목록표시하여종료
 if config.issue_url == "__LIST_STATES__":
 list_states()
 sys.exit(0)

 # 통상실행
 run(config)
