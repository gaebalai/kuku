"""Prompt builder for kuku_harness.

Builds prompts with context variables for CLI execution.
"""

from __future__ import annotations

from .models import Step, Workflow
from .state import SessionState


def build_prompt(step: Step, issue: int, state: SessionState, workflow: Workflow) -> str:
    """스텝 실행용 프롬프트를 구축한다.

    Args:
        step: 실행할 스텝
        issue: GitHub Issue 번호
        state: 현재 세션 상태
        workflow: 워크플로우 정의

    Returns:
        CLI에 전달할 프롬프트 문자열
    """
    variables: dict[str, object] = {
        "issue_number": issue,
        "step_id": step.id,
    }

    # 사이클 변수 (사이클 내 스텝만)
    cycle = workflow.find_cycle_for_step(step.id)
    if cycle:
        variables["cycle_count"] = state.cycle_iterations(cycle.name) + 1
        variables["max_iterations"] = cycle.max_iterations

    # 전이원의 verdict (resume 또는 inject_verdict 지정 스텝)
    if (step.resume or step.inject_verdict) and state.last_transition_verdict:
        v = state.last_transition_verdict
        variables["previous_verdict"] = (
            f"reason: {v.reason}\nevidence: {v.evidence}\nsuggestion: {v.suggestion}"
        )

    valid_statuses = list(step.on.keys())
    header = "\n".join(f"- {k}: {v}" for k, v in variables.items())

    return f"""스킬 `{step.skill}`을 실행해 주세요.

## 세션 시작 프로토콜
1. GitHub Issue #{issue}를 읽고, 현재 진척을 파악한다
2. git log --oneline -10으로 최근 변경을 확인한다
3. 이하의 컨텍스트 변수를 확인한다
4. 상기를 근거로 스킬의 지시에 따라 작업을 실행한다

## 컨텍스트 변수
{header}

## 출력 요건
실행 완료 후, 이하의 YAML 형식으로 verdict를 출력해 주세요:

---VERDICT---
status: {" | ".join(valid_statuses)}
reason: "판정 이유"
evidence: |
  구체적 근거 (복수 행 가능. 추상 표현 금지)
suggestion: "다음 액션 제안" (ABORT/BACK 시 필수)
---END_VERDICT---
"""
