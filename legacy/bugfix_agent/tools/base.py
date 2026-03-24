"""Base tool definitions for Bugfix Agent v5

This module provides:
- AIToolProtocol: Interface for all AI tools
- MockTool: Test mock implementation
"""

from pathlib import Path
from typing import Protocol


class AIToolProtocol(Protocol):
 """AI CLI 도구의統一인터페이스

 모두의 AI 도구(Gemini, Codex, Claude)이구현해야 할인터페이스.
 테스트시는 MockTool で差し替え가능.
 """

 def run(
 self,
 prompt: str,
 context: str | list[str] = "",
 session_id: str | None = None,
 log_dir: Path | None = None,
 ) -> tuple[str, str | None]:
 """AI 도구를 실행한다.

 Args:
 prompt: 실행한다指示/질문
 context: 컨텍스트정보
 - str: 텍스트로서전달하다(Codex 용)
 - list[str]: 파일경로리스트(Gemini 용)
 - 각구현로적절에처리
 session_id: 계속한다세션의 ID(None 로 신규)
 log_dir: 로그저장디렉토리(None 로 저장하지 않는다)
 logger: 실행ロガー

 Returns:
 tuple[str, str | None]: (응답텍스트, 새로운세션 ID)
 """
 ...


class MockTool:
 """테스트용목도구

 予め설정한응답를順番에 반환하다.세션 ID 는 자동생성.
 """

 def __init__(self, responses: list[str]):
 """
 Args:
 responses: 반환하다응답의리스트(順番に消費된다)
 """
 self._responses = iter(responses)
 self._session_counter = 0

 def run(
 self,
 prompt: str, # noqa: ARG002 - interface compatibility
 context: str | list[str] = "", # noqa: ARG002 - interface compatibility
 session_id: str | None = None,
 log_dir: Path | None = None, # noqa: ARG002 - interface compatibility
 ) -> tuple[str, str | None]:
 """설정된응답를順番에 반환하다(prompt, context, log_dir 는 interface 호환때문받다이사용하지 않는다)"""
 del prompt, context, log_dir # Explicitly mark as unused (Pylance)
 response = next(self._responses, "MOCK_RESPONSE")
 self._session_counter += 1
 new_session = session_id or f"mock-session-{self._session_counter}"
 return (response, new_session)
