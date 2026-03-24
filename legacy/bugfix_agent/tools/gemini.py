"""Gemini CLI tool wrapper for Bugfix Agent v5

This module provides:
- GeminiTool: Analyzer for issue analysis, documentation, long-context tasks
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ..cli import run_cli_streaming
from ..config import get_config_value
from ..context import build_context


class GeminiTool:
 """Gemini CLI 래퍼(분석·문서생성담당)

 長文컨텍스트에강한 AI.조사분석나 문서생성를담당.
 """

 def __init__(self, model: str | None = None):
 """
 Args:
 model: 모델명(None 로 config.toml 부터취득, "auto" でCLI기본값)
 """
 self.model = model or get_config_value("tools.gemini.model", "auto")
 self.timeout = get_config_value("tools.gemini.timeout", 300)

 def run(
 self,
 prompt: str,
 context: str | list[str] = "",
 session_id: str | None = None,
 log_dir: Path | None = None,
 ) -> tuple[str, str | None]:
 """Gemini CLI 를 실행한다

 Args:
 prompt: 실행한다指示/질문
 context: str 라면직접추가, list[str] 라면파일경로로서읽기
 session_id: 계속한다세션의 ID
 log_dir: 로그저장디렉토리(None 로 저장하지 않는다)
 logger: 실행ロガー

 Returns:
 (응답텍스트, 새로운세션 ID)
 """
 print("🔵 [Gemini] Thinking...")

 # 컨텍스트를구축(공통유틸리티사용)
 context_data = build_context(context, max_chars=0) # Gemini 는 제한없음
 full_prompt = f"{prompt}\n\nContext:\n{context_data}" if context_data else prompt

 # CLI 인수를구축
 args = ["gemini", "-o", "stream-json"]
 if self.model != "auto":
 args += ["-m", self.model]
 if session_id:
 args += ["-r", session_id]
 # Enable tools for gh/shell operations and web fetching in non-interactive mode
 # Note: Gemini CLI restricts tools by default in non-interactive mode for security.
 # Using --allowed-tools whitelist is the recommended approach.
 # - run_shell_command: for gh/shell operations
 # - web_fetch: for fetching Issue content from GitHub URLs
 args += ["--allowed-tools", "run_shell_command,web_fetch"]
 # Skip all approval prompts (WSL closed development environment)
 args += ["--approval-mode", "yolo"]
 args.append(full_prompt)

 # CLI 실행(스트리밍)
 timeout = self.timeout if self.timeout > 0 else None
 try:
 stdout, stderr, returncode = run_cli_streaming(
 args, timeout=timeout, log_dir=log_dir, tool_name="gemini"
 )
 if returncode != 0:
 print(f"❌ Gemini Error: {stderr}")
 return "ERROR", session_id
 except FileNotFoundError:
 print("❌ Gemini CLI not found. Is 'gemini' installed and in PATH?")
 return "ERROR", session_id
 except subprocess.TimeoutExpired:
 print(f"❌ Gemini timeout after {self.timeout}s")
 return "ERROR", session_id

 # JSON Lines 파싱
 new_session_id = session_id
 assistant_reply = ""
 for line in stdout.splitlines():
 line = line.strip()
 if not line:
 continue

 try:
 payload = json.loads(line)
 except json.JSONDecodeError:
 continue

 # 세션 ID 취득(신규세션시만)
 if payload.get("type") == "init" and not new_session_id:
 new_session_id = payload.get("session_id", new_session_id)

 # アシスタント응답취득
 if payload.get("role") == "assistant":
 assistant_reply = payload.get("content", assistant_reply)

 return assistant_reply.strip(), new_session_id
