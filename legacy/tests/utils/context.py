"""Test context utilities for Bugfix Agent v5.

This module provides:
- create_test_context: Create test context with mock tools and MockIssueProvider
"""

from pathlib import Path

from bugfix_agent.agent_context import AgentContext
from bugfix_agent.run_logger import RunLogger
from bugfix_agent.tools import MockTool

from .providers import MockIssueProvider


def create_test_context(
 analyzer_responses: list[str] | None = None,
 reviewer_responses: list[str] | None = None,
 implementer_responses: list[str] | None = None,
 issue_url: str = "https://github.com/test/repo/issues/999",
 run_timestamp: str = "2511281430",
 issue_provider: MockIssueProvider | None = None,
 artifacts_base: Path | None = None,
) -> AgentContext:
 """테스트용의 컨텍스트를 생성

 Args:
 analyzer_responses: アナライザー(Gemini)의 응답리스트
 reviewer_responses: 리뷰어(Codex)의 응답리스트
 implementer_responses: 구현者(Claude)의 응답리스트
 issue_url: Issue URL(기본값: 테스트用ダミー)
 run_timestamp: 실행타임스탬프(기본값: 테스트용고정값)
 issue_provider: MockIssueProvider 인스턴스
 (None 라면자동생성)
 artifacts_base: 산출물ベース디렉토리(테스트로tmp_path를 지정)

 Returns:
 MockTool 과 MockIssueProvider 를 주입한 AgentContext
 """
 issue_number = int(issue_url.rstrip("/").split("/")[-1])

 # 기본값응답
 if analyzer_responses is None:
 analyzer_responses = []
 if reviewer_responses is None:
 reviewer_responses = []
 if implementer_responses is None:
 implementer_responses = []

 # Issue プロバイダー(MockIssueProvider 를 사용)
 if issue_provider is None:
 issue_provider = MockIssueProvider(
 issue_number=issue_number,
 repo_url=issue_url.rsplit("/issues/", 1)[0],
 )

 # 테스트시는 /tmp/pytest-of-hoge/pytest-current/testname/
 # 등에생성된다
 if artifacts_base is None:
 artifacts_base = Path("test-artifacts/bugfix-agent")

 artifacts_dir = artifacts_base / str(issue_number) / run_timestamp
 logger = RunLogger(artifacts_dir / "run.log")

 return AgentContext(
 analyzer=MockTool(analyzer_responses),
 reviewer=MockTool(reviewer_responses),
 implementer=MockTool(implementer_responses),
 issue_url=issue_url,
 issue_number=issue_number,
 issue_provider=issue_provider,
 run_timestamp=run_timestamp,
 artifacts_base=artifacts_base,
 logger=logger,
 )
