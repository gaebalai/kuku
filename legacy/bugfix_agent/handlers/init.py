"""INIT state handler for Bugfix Agent v5

This module provides:
- handle_init: Check Issue requirements and validate VERDICT
"""

from ..agent_context import AgentContext
from ..errors import AgentAbortError, check_tool_result
from ..prompts import load_prompt
from ..state import SessionState, State
from ..verdict import Verdict, create_ai_formatter, handle_abort_verdict, parse_verdict


def handle_init(ctx: AgentContext, state: SessionState) -> State:
 """INIT: Issue 本文의 필수정보존재확인

 Issue #194 Protocol: VERDICT형식로판정결과를출력.
 ABORT의 경우는AgentAbortErrorがraise된다.

 Args:
 ctx: Agent 컨텍스트
 state: 세션상태

 Returns:
 PASS → INVESTIGATE

 Raises:
 AgentAbortError: ABORTが返된경우(정보부족)
 """
 print("📋 Checking Issue requirements...")

 log_dir = ctx.artifacts_state_dir("init")
 prompt = load_prompt("init", issue_url=ctx.issue_url)

 result, _ = ctx.reviewer.run(prompt=prompt, context=ctx.issue_url, log_dir=log_dir)
 check_tool_result(result, "reviewer")

 # VERDICT형식로파싱(Issue #292: ハイブリッド폴백대응)
 ai_formatter = create_ai_formatter(ctx.reviewer, context=ctx.issue_url, log_dir=log_dir)
 verdict = parse_verdict(result, ai_formatter=ai_formatter)

 # ABORT의 경우는코멘트를投稿하여부터예외를送出
 if verdict == Verdict.ABORT:
 try:
 handle_abort_verdict(verdict, result)
 except AgentAbortError as e:
 comment_body = (
 f"## INIT Check Result\n\n{result}\n\n"
 "---\n"
 f"**INIT ABORT**: {e.reason}\n\n"
 f"**Suggestion**: {e.suggestion}"
 )
 ctx.issue_provider.add_comment(comment_body)
 raise

 # INITではPASS만허가(Issue #194 VERDICT대응表: RETRY/BACK_DESIGN는 사용불가)
 if verdict != Verdict.PASS:
 raise AgentAbortError(
 reason=f"Invalid VERDICT '{verdict.value}' for INIT state (only PASS allowed)",
 suggestion="INIT state only accepts PASS or ABORT. Check reviewer prompt.",
 )

 print(f">>> ✅ Judgment: {Verdict.PASS.value}")
 comment_body = f"## INIT Check Result\n\n{result}"
 ctx.issue_provider.add_comment(comment_body)

 state.completed_states.append("INIT")
 return State.INVESTIGATE
