"""Claude Code CLI tool wrapper for Bugfix Agent v5

This module provides:
- ClaudeTool: Implementer for file operations, command execution tasks
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from ..cli import run_cli_streaming
from ..config import get_config_value
from ..context import build_context


class ClaudeTool:
 """Claude Code CLI 래퍼(구현·조작담당)

 파일조작·명령어실행이가능한 AI.구현와조작를담당.
 """

 def __init__(
 self,
 model: str | None = None,
 permission_mode: str | None = None,
 ):
 """
 Args:
 model: 모델명(None 로 config.toml 부터취득)
 permission_mode: 권한모드(None 로 config.toml 부터취득)
 """
 self.model = model or get_config_value("tools.claude.model", "opus")
 self.permission_mode = permission_mode or get_config_value(
 "tools.claude.permission_mode", "default"
 )
 self.timeout = get_config_value("tools.claude.timeout", 600)

 def run(
 self,
 prompt: str,
 context: str | list[str] = "",
 session_id: str | None = None,
 log_dir: Path | None = None,
 ) -> tuple[str, str | None]:
 """Claude Code CLI 를 실행한다

 Args:
 prompt: 실행한다指示/질문
 context: 컨텍스트정보
 session_id: 계속한다세션의 ID
 log_dir: 로그저장디렉토리(None 로 저장하지 않는다)
 logger: 실행ロガー

 Returns:
 (응답텍스트, 새로운세션 ID)
 """
 print("🟠 [Claude] Acting...")

 # 컨텍스트를구축(공통유틸리티를 사용, Claude 는 max_chars=0 で無제한)
 context_str = build_context(context, max_chars=0)
 full_prompt = f"{prompt}\n\nContext:\n{context_str}" if context_str else prompt

 # CLI 인수를구축
 # Use stream-json for real-time output display (requires --verbose)
 args = ["claude", "-p", "--output-format", "stream-json", "--verbose"]
 if self.model:
 args += ["--model", self.model]
 if self.permission_mode != "default":
 args += ["--permission-mode", self.permission_mode]
 if session_id:
 args += ["-r", session_id]

 # Note: Non-interactive mode requires tools to be allowed via:
 # 1. ~/.claude/settings.json "permissions.allow" (recommended, system-wide)
 # 2. CLI --allowedTools flag (per-session override)
 # 3. CLI --dangerously-skip-permissions flag (skips all permission checks)
 # Current setup uses --dangerously-skip-permissions for WSL closed environment.
 # Skip all permission checks (WSL closed development environment)
 args.append("--dangerously-skip-permissions")

 args.append(full_prompt)

 # 환경변수설정(디버그/캐시디렉토리)
 env = os.environ.copy()
 debug_dir = env.get("CLAUDE_DEBUG_DIR", "/tmp/claude-debug")
 cache_dir = env.get("CLAUDE_CACHE_DIR", "/tmp/claude-cache")
 Path(debug_dir).mkdir(parents=True, exist_ok=True)
 Path(cache_dir).mkdir(parents=True, exist_ok=True)
 env["CLAUDE_DEBUG_DIR"] = debug_dir
 env["CLAUDE_CACHE_DIR"] = cache_dir

 # CLI 실행(스트리밍)
 timeout = self.timeout if self.timeout > 0 else None
 try:
 stdout, stderr, returncode = run_cli_streaming(
 args, timeout=timeout, env=env, log_dir=log_dir, tool_name="claude"
 )
 if returncode != 0:
 print(f"❌ Claude Error: {stderr}")
 if stdout:
 print(stdout.strip())
 return "ERROR", session_id
 except FileNotFoundError:
 print("❌ Claude CLI not found. Is 'claude' installed and in PATH?")
 return "ERROR", session_id
 except subprocess.TimeoutExpired:
 print(f"❌ Claude timeout after {self.timeout}s")
 return "ERROR", session_id

 # JSON 파싱(노이즈혼입대책: 정규表現로 JSON 부분를추출)
 response, new_session_id = self._parse_json_output(stdout, session_id)

 return response, new_session_id

 def _parse_json_output(self, stdout: str, session_id: str | None) -> tuple[str, str | None]:
 """CLI의출력부터JSON부분를추출하여파싱한다

 stream-json형식(복수행JSON)とjson형식(단일JSON)의両方에 대응.
 """
 # stream-json형식: 복수행의JSON부터 "type":"result" 의 행를探す
 for line in stdout.strip().split("\n"):
 line = line.strip()
 if not line:
 continue
 try:
 payload = json.loads(line)
 if payload.get("type") == "result":
 return self._extract_from_payload(payload, stdout, session_id)
 except json.JSONDecodeError:
 continue

 # 종래의json형식: 전체를단일JSON로서파싱
 try:
 payload = json.loads(stdout)
 return self._extract_from_payload(payload, stdout, session_id)
 except json.JSONDecodeError:
 pass

 # 실패한 경우, 정규表現でJSON부분를추출
 json_match = re.search(r'\{[^{}]*"result"[^{}]*\{.*?\}[^{}]*\}', stdout, re.DOTALL)
 if json_match:
 try:
 payload = json.loads(json_match.group())
 return self._extract_from_payload(payload, stdout, session_id)
 except json.JSONDecodeError:
 pass

 # 그것でも실패한 경우는素의 출력를 반환하다
 return stdout.strip(), session_id

 def _extract_from_payload(
 self, payload: dict[str, Any], stdout: str, session_id: str | None
 ) -> tuple[str, str | None]:
 """파싱완료ペイ로드부터응답와세션ID를 추출

 stream-json형식: {"type":"result","result":"text","session_id":"uuid"}
 json형식: {"result":{"text":"...","session_id":"..."}}
 """
 result_data = payload.get("result", {})

 # stream-json 형식: result 는 문자열, session_id 는 탑레벨
 if isinstance(result_data, str):
 response = result_data if result_data else stdout
 new_session_id = session_id or payload.get("session_id")
 # json 형식: result は辞書
 elif isinstance(result_data, dict):
 response = result_data.get("text", stdout)
 new_session_id = session_id or result_data.get("session_id")
 else:
 response = stdout
 new_session_id = session_id

 return response, new_session_id
