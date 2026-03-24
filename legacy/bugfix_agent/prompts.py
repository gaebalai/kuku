"""Prompt management for Bugfix Agent v5

This module provides:
- PROMPT_DIR: Path to prompts directory
- COMMON_PROMPT_FILE: Path to common prompt file
- REVIEW_PREAMBLE_FILE: Path to Devil's Advocate preamble file
- FOOTER_VERDICT_FILE: Path to VERDICT footer file
- VERDICT_REQUIRED_STATES: States that require VERDICT output
- REVIEW_STATES: States that require Devil's Advocate preamble
- load_prompt: Load and render prompt templates
"""

from pathlib import Path
from string import Template
from typing import Any

# 프롬프트디렉토리의정의
PROMPT_DIR = Path(__file__).parent.parent / "prompts"
COMMON_PROMPT_FILE = PROMPT_DIR / "_common.md"
REVIEW_PREAMBLE_FILE = PROMPT_DIR / "_review_preamble.md"
FOOTER_VERDICT_FILE = PROMPT_DIR / "_footer_verdict.md"

# VERDICT출력이필요な스테이트(REVIEW스테이트 + INIT)
VERDICT_REQUIRED_STATES = {
 "init",
 "investigate_review",
 "detail_design_review",
 "implement_review",
}

# REVIEW스테이트(Devil's Advocate적용대상)
# NOTE: qa_review 는 v5 로 IMPLEMENT_REVIEW 에 통합된위해제외
# prompts/qa_review.md 는 하위 호환性때문残存(DEPRECATED)
REVIEW_STATES = {
 "investigate_review",
 "detail_design_review",
 "implement_review",
}


def load_prompt(
 state_name: str,
 *,
 include_common: bool | None = None,
 include_review_preamble: bool | None = None,
 include_footer: bool | None = None,
 **kwargs: Any,
) -> str:
 """스테이트用프롬프트를 로드하여템플릿변수를전개

 Args:
 state_name: 스테이트名(小문자, 예: "investigate_review")
 include_common: 공통프롬프트를 포함하다인가
 - None: VERDICT_REQUIRED_STATES에 포함된다경우만자동추가
 - True/False: 강제지정
 include_review_preamble: Devil's Advocateプリアンブル를 포함하다인가
 - None: REVIEW_STATES에 포함된다경우만자동추가
 - True/False: 강제지정
 include_footer: VERDICT푸터를 포함하다인가
 - None: VERDICT_REQUIRED_STATES에 포함된다경우만자동추가
 - True/False: 강제지정
 **kwargs: 템플릿변수

 Returns:
 전개후의 프롬프트문자열

 Raises:
 FileNotFoundError: 프롬프트파일이존재하지 않는다경우
 KeyError: 필수템플릿변수이부족하고 있다경우
 """
 prompt_file = PROMPT_DIR / f"{state_name}.md"
 if not prompt_file.exists():
 raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

 state_lower = state_name.lower()

 # 자동판정
 if include_common is None:
 include_common = state_lower in VERDICT_REQUIRED_STATES
 if include_review_preamble is None:
 include_review_preamble = state_lower in REVIEW_STATES
 if include_footer is None:
 include_footer = state_lower in VERDICT_REQUIRED_STATES

 parts: list[str] = []

 # 1. 공통프롬프트(선두)
 if include_common and COMMON_PROMPT_FILE.exists():
 parts.append(COMMON_PROMPT_FILE.read_text(encoding="utf-8"))
 parts.append("\n---\n\n")

 # 2. REVIEWプリアンブル(Devil's Advocate)
 if include_review_preamble and REVIEW_PREAMBLE_FILE.exists():
 parts.append(REVIEW_PREAMBLE_FILE.read_text(encoding="utf-8"))
 parts.append("\n---\n\n")

 # 3. 메인프롬프트
 parts.append(prompt_file.read_text(encoding="utf-8"))

 # 4. 푸터(말미)
 if include_footer and FOOTER_VERDICT_FILE.exists():
 parts.append("\n\n")
 parts.append(FOOTER_VERDICT_FILE.read_text(encoding="utf-8"))

 template = Template("".join(parts))
 return template.substitute(**kwargs)
