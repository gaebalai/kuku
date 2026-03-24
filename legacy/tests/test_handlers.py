"""Tests for handler functions.

Issue #312: IMPLEMENT_REVIEW session_id handling tests.
"""

from unittest.mock import MagicMock

import pytest

from bugfix_agent.agent_context import AgentContext
from bugfix_agent.handlers.implement import handle_implement_review
from bugfix_agent.state import SessionState
from tests.utils.providers import MockIssueProvider


class TestImplementReviewSessionHandling:
 """Issue #312: IMPLEMENT_REVIEW 이 session_id を使わ없다것을검증.

 3원칙: 읽지 않는다·渡さ없다·저장하지 않는다
 """

 @pytest.fixture
 def mock_reviewer(self) -> MagicMock:
 """MagicMock reviewer for spy verification."""
 mock = MagicMock()
 # decision 를 strict 에 하여 fallback が走ら없다전제
 mock.run.return_value = (
 "## VERDICT\n- Result: PASS\n- Reason: All checks passed\n- Evidence: OK",
 "codex-thread-123",
 )
 return mock

 @pytest.fixture
 def context_with_mock_reviewer(self, mock_reviewer: MagicMock) -> AgentContext:
 """AgentContext with MagicMock reviewer for spy verification."""
 provider = MockIssueProvider(initial_body="# Test Issue")
 return AgentContext(
 analyzer=MagicMock(),
 reviewer=mock_reviewer,
 implementer=MagicMock(),
 issue_url=provider.issue_url,
 issue_number=provider.issue_number,
 issue_provider=provider,
 run_timestamp="2512181200",
 logger=MagicMock(),
 )

 def test_implement_review_calls_reviewer_with_session_id_none(
 self, context_with_mock_reviewer: AgentContext, mock_reviewer: MagicMock
 ):
 """IMPLEMENT_REVIEW 이 session_id=None 로 reviewer を呼ぶ것을검증.

 spy검증: 最初의 호출로 session_id=None 이다것.
 """
 state = SessionState()
 # 기존의 Claude 세션이존재한다상황를再現
 state.active_conversations["Implement_Loop_conversation_id"] = "existing-claude-session"

 handle_implement_review(context_with_mock_reviewer, state)

 # spy검증: 最初의 호출로 session_id=None 이다것(fallback時も壊れ없다)
 assert mock_reviewer.run.call_count >= 1
 first_call_kwargs = mock_reviewer.run.call_args_list[0].kwargs
 assert first_call_kwargs.get("session_id") is None

 def test_implement_review_does_not_update_implement_loop_conversation_id(
 self, context_with_mock_reviewer: AgentContext, mock_reviewer: MagicMock
 ):
 """IMPLEMENT_REVIEW 이 Implement_Loop_conversation_id 를 업데이트하지 않는다것을검증.

 불변조건: 기존의 Claude 세션ID이 변경되지 않는다.
 """
 state = SessionState()
 original_session = "existing-claude-session"
 state.active_conversations["Implement_Loop_conversation_id"] = original_session

 handle_implement_review(context_with_mock_reviewer, state)

 # 불변조건: Implement_Loop_conversation_id 이 변경되어 있지 않다것
 assert state.active_conversations["Implement_Loop_conversation_id"] == original_session

 def test_implement_review_does_not_save_codex_session_to_implement_loop(
 self, context_with_mock_reviewer: AgentContext, mock_reviewer: MagicMock
 ):
 """IMPLEMENT_REVIEW 이 Codex 의 session_id 를 Implement_Loop 에 저장하지 않는다것을검증.

 逆방향クロス도구事故의 방지: Codex 의 thread_id 이 저장되지 않는다.
 """
 state = SessionState()
 # Implement_Loop_conversation_id 이 None 의 상황(初회실행)
 state.active_conversations["Implement_Loop_conversation_id"] = None

 handle_implement_review(context_with_mock_reviewer, state)

 # 저장하지 않는다: Codex 의 session_id (codex-thread-123) 이 저장되어 있지 않다것
 assert state.active_conversations["Implement_Loop_conversation_id"] is None

 def test_implement_review_returns_correct_state_on_pass(
 self, context_with_mock_reviewer: AgentContext, mock_reviewer: MagicMock
 ):
 """PASS 시에 PR_CREATE 에 전이한다것을검증."""
 from bugfix_agent.state import State

 state = SessionState()

 result = handle_implement_review(context_with_mock_reviewer, state)

 assert result == State.PR_CREATE

 def test_implement_review_returns_implement_on_retry(
 self, context_with_mock_reviewer: AgentContext, mock_reviewer: MagicMock
 ):
 """RETRY 시에 IMPLEMENT 에 전이한다것을검증."""
 from bugfix_agent.state import State

 mock_reviewer.run.return_value = (
 "## VERDICT\n- Result: RETRY\n- Reason: Fix needed\n- Suggestion: Fix X",
 "codex-thread-456",
 )
 state = SessionState()

 result = handle_implement_review(context_with_mock_reviewer, state)

 assert result == State.IMPLEMENT

 def test_implement_review_returns_detail_design_on_back_design(
 self, context_with_mock_reviewer: AgentContext, mock_reviewer: MagicMock
 ):
 """BACK_DESIGN 시에 DETAIL_DESIGN 에 전이한다것을검증."""
 from bugfix_agent.state import State

 mock_reviewer.run.return_value = (
 "## VERDICT\n- Result: BACK_DESIGN\n- Reason: Design issue\n- Suggestion: Redesign Y",
 "codex-thread-789",
 )
 state = SessionState()

 result = handle_implement_review(context_with_mock_reviewer, state)

 assert result == State.DETAIL_DESIGN
