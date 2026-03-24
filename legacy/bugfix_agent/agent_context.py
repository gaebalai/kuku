"""Agent context for Bugfix Agent v5

This module provides:
- AgentContext: Context dataclass passed to state handlers
- create_default_context: Create production context with real AI tools

For testing, use create_test_context from tests.utils.context.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from .providers import GitHubIssueProvider, IssueProvider
from .run_logger import RunLogger
from .tools import AIToolProtocol, ClaudeTool, CodexTool


@dataclass
class AgentContext:
 """스테이트핸들러에전달하다컨텍스트"""

 # AI 도구(의존性주입)
 analyzer: AIToolProtocol # Gemini: 분석·문서생성
 reviewer: AIToolProtocol # Codex: 리뷰·판단
 implementer: AIToolProtocol # Claude: 구현·조작

 # Issue 정보
 issue_url: str # https://github.com/apokamo/kamo2/issues/182
 issue_number: int # 182

 # Issue プロバイダー(GitHub API추상화)
 issue_provider: IssueProvider

 # 실행ロガー
 logger: RunLogger

 # 証跡ベース경로
 artifacts_base: Path = field(default_factory=lambda: Path("test-artifacts/bugfix-agent"))
 run_timestamp: str = "" # YYMMDDhhmm 형식(실행시작時에 설정)

 @property
 def artifacts_dir(self) -> Path:
 """실행단위의証跡디렉토리"""
 return self.artifacts_base / str(self.issue_number) / self.run_timestamp

 def artifacts_state_dir(self, state: str) -> Path:
 """스테이트별의証跡디렉토리"""
 return self.artifacts_dir / state.lower()


def _create_tool(
 tool_name: str,
 model: str | None = None,
) -> AIToolProtocol:
 """도구명부터도구인스턴스를 생성

 Args:
 tool_name: 도구명 (codex, gemini, claude)
 model: 모델명(None 로 기본값)

 Returns:
 AIToolProtocol 구현
 """
 # Note: GeminiTool is imported only when needed to avoid unnecessary dependency
 if tool_name == "codex":
 return CodexTool(model=model) if model else CodexTool()
 elif tool_name == "gemini":
 from .tools import GeminiTool

 return GeminiTool(model=model) if model else GeminiTool()
 elif tool_name == "claude":
 return ClaudeTool(model=model) if model else ClaudeTool()
 else:
 raise ValueError(f"Unknown tool: {tool_name}")


def create_default_context(
 issue_url: str,
 tool_override: str | None = None,
 model_override: str | None = None,
 issue_provider: IssueProvider | None = None,
) -> AgentContext:
 """본번용의 컨텍스트를 생성

 Args:
 issue_url: Issue URL (예: https://github.com/apokamo/kamo2/issues/182)
 tool_override: 도구지정(전롤로동일도구를 사용)
 model_override: 모델지정(tool_override 과 병용)
 issue_provider: Issue プロバイダー(None 라면 GitHubIssueProvider 를 생성)

 Returns:
 본번용 AI 도구를 주입한 AgentContext
 """
 # issue_url 부터 issue_number 를 추출
 issue_number = int(issue_url.rstrip("/").split("/")[-1])

 # 실행타임스탬프를 생성(YYMMDDhhmm 형식)
 run_timestamp = datetime.now(UTC).strftime("%y%m%d%H%M")

 # 証跡디렉토리
 artifacts_base = Path("test-artifacts/bugfix-agent")
 artifacts_dir = artifacts_base / str(issue_number) / run_timestamp

 # ロガー
 logger = RunLogger(artifacts_dir / "run.log")

 # Issue プロバイダー(기본값는 GitHub API)
 if issue_provider is None:
 issue_provider = GitHubIssueProvider(issue_url)

 # 도구오버라이드이 있다경우는전롤로동일도구를 사용
 if tool_override:
 tool = _create_tool(tool_override, model_override)
 return AgentContext(
 analyzer=tool,
 reviewer=tool,
 implementer=tool,
 issue_url=issue_url,
 issue_number=issue_number,
 issue_provider=issue_provider,
 logger=logger,
 run_timestamp=run_timestamp,
 artifacts_base=artifacts_base,
 )

 # 기본값: 각롤에전용도구
 # Note: analyzer 를 Gemini → Claude 에 변경 (Issue #194 테스트설계)
 # Note: 코스트삭감때문 sonnet / codex-mini 를 사용 (E2E Test 11)
 return AgentContext(
 analyzer=ClaudeTool(model="sonnet"),
 reviewer=CodexTool(model="gpt-5.1-codex-mini"),
 implementer=ClaudeTool(model="sonnet"),
 issue_url=issue_url,
 issue_number=issue_number,
 issue_provider=issue_provider,
 logger=logger,
 run_timestamp=run_timestamp,
 artifacts_base=artifacts_base,
 )
