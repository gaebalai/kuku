"""IMPLEMENT state handlers for Bugfix Agent v5

This module provides:
- handle_implement: Create branch, implement fix, run tests
- handle_implement_review: Review implementation results (QA integrated)
"""

from ..agent_context import AgentContext
from ..errors import check_tool_result
from ..prompts import load_prompt
from ..state import SessionState, State
from ..verdict import Verdict, create_ai_formatter, handle_abort_verdict, parse_verdict


def handle_implement(ctx: AgentContext, state: SessionState) -> State:
 """IMPLEMENT: 브랜치생성, 구현, 테스트실행

 Args:
 ctx: Agent 컨텍스트
 state: 세션상태

 Returns:
 다음스테이트 (IMPLEMENT_REVIEW)
 """
 print("🔨 Implementing the fix...")

 impl_session = state.active_conversations["Implement_Loop_conversation_id"]
 artifacts_dir = ctx.artifacts_state_dir("implement")
 artifacts_dir.mkdir(parents=True, exist_ok=True)

 prompt = load_prompt(
 "implement",
 issue_url=ctx.issue_url,
 issue_number=ctx.issue_number,
 artifacts_dir=artifacts_dir,
 )

 result, new_session = ctx.implementer.run(
 prompt=prompt,
 context=ctx.issue_url,
 session_id=impl_session,
 log_dir=artifacts_dir,
 )
 check_tool_result(result, "implementer")

 if not impl_session and new_session:
 state.active_conversations["Implement_Loop_conversation_id"] = new_session

 state.loop_counters["Implement_Loop"] += 1
 state.completed_states.append("IMPLEMENT")
 return State.IMPLEMENT_REVIEW


def handle_implement_review(ctx: AgentContext, state: SessionState) -> State:
 """IMPLEMENT_REVIEW: 구현결과의리뷰(QA통합版)

 Issue #194 Protocol: QA/QA_REVIEW를 통합한새로운리뷰스테이트.
 구현리뷰に加え, QA관점로의검증도동시에 행う.

 Args:
 ctx: Agent 컨텍스트
 state: 세션상태

 Returns:
 PASS → PR_CREATE(QA관점도含めて문제없음)
 RETRY → IMPLEMENT (구현수정)
 BACK_DESIGN → DETAIL_DESIGN (설계見直し)

 Raises:
 AgentAbortError: ABORTが返된경우
 """
 print("👀 Reviewing IMPLEMENT results (QA integrated)...")

 log_dir = ctx.artifacts_state_dir("implement_review")
 # Issue #312: 3원칙(읽지 않는다·渡さ없다·저장하지 않는다)
 # REVIEW 스테이트는 산출물ベース로 리뷰한다때문에, session_id 는 불필요
 # Implement_Loop_conversation_id 로의접근는一切행わ없다

 prompt = load_prompt("implement_review", issue_url=ctx.issue_url)

 decision, _ = ctx.reviewer.run(
 prompt=prompt,
 context=ctx.issue_url,
 session_id=None,
 log_dir=log_dir,
 )
 check_tool_result(decision, "reviewer")

 # VERDICT형식로파싱(Issue #292: ハイブリッド폴백대응)
 ai_formatter = create_ai_formatter(ctx.reviewer, context=ctx.issue_url, log_dir=log_dir)
 verdict = parse_verdict(decision, ai_formatter=ai_formatter)

 # ABORT의 경우는예외를送出(Issue #292 책무분리)
 handle_abort_verdict(verdict, decision)

 if verdict == Verdict.RETRY:
 print(f">>> 🛑 Judgment: {Verdict.RETRY.value} (Re-implement)")
 return State.IMPLEMENT
 elif verdict == Verdict.BACK_DESIGN:
 print(f">>> 🛑 Judgment: {Verdict.BACK_DESIGN.value} (Back to design)")
 return State.DETAIL_DESIGN
 else:
 print(f">>> ✅ Judgment: {Verdict.PASS.value}")
 state.completed_states.append("IMPLEMENT_REVIEW")
 return State.PR_CREATE
