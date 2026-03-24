"""Codex CLI tool wrapper for Bugfix Agent v5

This module provides:
- CodexTool: Reviewer for code review, judgment, web search tasks
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ..cli import run_cli_streaming
from ..config import get_config_value, get_workdir
from ..context import build_context


class CodexTool:
 """Codex CLI 래퍼(리뷰·판단담당)

 논리적思考와 외부정보수집에강한 AI.리뷰와 판단를담당.
 """

 def __init__(
 self,
 model: str | None = None,
 workdir: str | None = None,
 sandbox: str | None = None,
 ):
 """
 Args:
 model: 모델명(None 로 config.toml 부터취득)
 workdir: 작업디렉토리(None 로 자동検出)
 sandbox: 샌드박스모드(None 로 config.toml 부터취득)
 """
 self.model = model or get_config_value("tools.codex.model", "gpt-5.1-codex")
 self.workdir = workdir or str(get_workdir())
 self.sandbox = sandbox or get_config_value("tools.codex.sandbox", "workspace-write")
 self.timeout = get_config_value("tools.codex.timeout", 300)

 def run(
 self,
 prompt: str,
 context: str | list[str] = "",
 session_id: str | None = None,
 log_dir: Path | None = None,
 ) -> tuple[str, str | None]:
 """Codex CLI 를 실행한다

 Args:
 prompt: 실행한다指示/질문
 context: 컨텍스트정보(config 의 context_max_chars 까지)
 session_id: 계속한다세션의 ID(thread_id)
 log_dir: 로그저장디렉토리(None 로 저장하지 않는다)
 logger: 실행ロガー

 Returns:
 (응답텍스트, 새로운세션 ID)
 """
 print("🟢 [Codex] Judging...")

 # 컨텍스트를구축(공통유틸리티사용, max_chars 는 config 부터)
 context_str = build_context(context)
 full_prompt = f"{prompt}\n\nTarget Content to Review:\n{context_str}"

 # CLI 인수를구축
 # Note: --json 는 codex exec resume 로 지원되지 않는다때문에,
 # resume 모드로는텍스트출력를 사용
 if session_id:
 # resume 모드(--json 없음)
 # Note: --dangerously-bypass-approvals-and-sandbox is global; --skip-git-repo-check is exec subcommand option
 # Note: -s 옵션는 resume 로 사용불가때문, -c sandbox_mode= 로 오버라이드
 # Ref: docs/technical/shared/tools/codex-cli-reference.md section 3.4
 args = [
 "codex",
 "--dangerously-bypass-approvals-and-sandbox",
 "exec",
 "--skip-git-repo-check",
 "resume",
 session_id,
 "-c",
 'sandbox_mode="danger-full-access"',
 "-c",
 "sandbox_workspace_write.network_access=true",
 ]
 else:
 # 신규세션
 # Note: --dangerously-bypass-approvals-and-sandbox is global; --skip-git-repo-check is exec subcommand option
 args = [
 "codex",
 "--dangerously-bypass-approvals-and-sandbox",
 "exec",
 "--skip-git-repo-check",
 "-m",
 self.model,
 "-C",
 self.workdir,
 "-s",
 self.sandbox,
 "--enable",
 "web_search_request",
 "--json",
 ]
 args.append(full_prompt)

 # CLI 실행(스트리밍)
 timeout = self.timeout if self.timeout > 0 else None
 try:
 stdout, stderr, returncode = run_cli_streaming(
 args, timeout=timeout, log_dir=log_dir, tool_name="codex"
 )
 if returncode != 0:
 print(f"❌ Codex Error: {stderr}")
 return "ERROR", session_id
 except FileNotFoundError:
 print("❌ Codex CLI not found. Is 'codex' installed and in PATH?")
 return "ERROR", session_id
 except subprocess.TimeoutExpired:
 print(f"❌ Codex timeout after {self.timeout}s")
 return "ERROR", session_id

 # JSON Lines 파싱(신규세션시)/ 텍스트파싱(resume時)
 new_session_id = session_id
 assistant_replies: list[str] = [] # 모두의 agent_message 를 수집

 for line in stdout.splitlines():
 line = line.strip()
 if not line:
 continue

 try:
 payload = json.loads(line)
 except json.JSONDecodeError:
 # JSON이외의텍스트행(VERDICT를 포함가능性)를수집
 # Note: mcp_tool_call모드로는VERDICT이 플레인텍스트로서출력된다
 assistant_replies.append(line)
 continue

 # 세션 ID 취득(신규세션시만)
 if payload.get("type") == "thread.started" and not new_session_id:
 new_session_id = payload.get("thread_id", new_session_id)

 # アシスタント응답취득(모두의 agent_message 를 수집)
 if payload.get("type") == "item.completed":
 item = payload.get("item", {})
 if item.get("type") == "agent_message":
 text = item.get("text", "")
 if text:
 assistant_replies.append(text)

 # 모두의 응답를결합(VERDICT이 도중에あっても検出가능)
 assistant_reply = "\n\n".join(assistant_replies) if assistant_replies else ""

 # JSON が取れなかった경우는素의 stdout 를 반환하다
 if not assistant_reply:
 assistant_reply = stdout.strip()

 return assistant_reply, new_session_id
