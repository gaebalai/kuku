"""CLI execution utilities for Bugfix Agent v5

This module provides CLI streaming execution and output formatting:
- run_cli_streaming: Execute CLI with real-time output streaming
- format_jsonl_line: Extract content from JSONL output lines
"""

import json
import subprocess
import sys
import threading
from pathlib import Path

from .config import get_config_value


def format_jsonl_line(line: str, tool_name: str) -> str | None:
 """JSONL 행부터콘텐츠를추출한다

 Args:
 line: JSONL 형식의1행
 tool_name: 도구명 ("gemini", "codex", "claude")

 Returns:
 추출한콘텐츠.추출불가의 경우는 None
 """
 try:
 data = json.loads(line)
 except json.JSONDecodeError:
 # JSON 로 없다경우는, 空でなければ그まま반환하다
 stripped = line.strip()
 return stripped if stripped else None

 # Gemini 형식: {"type":"response","response":{"content":[{"type":"text","text":"..."}]}}
 if tool_name == "gemini" and data.get("type") == "response":
 content = data.get("response", {}).get("content", [])
 texts = [c.get("text", "") for c in content if c.get("type") == "text"]
 return "\n".join(texts) if texts else None

 # Codex 형식: {"type":"item.completed","item":{"type":"reasoning|agent_message","text":"..."}}
 # {"type":"item.completed","item":{"type":"command_execution","aggregated_output":"..."}}
 if tool_name == "codex":
 if data.get("type") == "item.completed":
 item = data.get("item", {})
 item_type = item.get("type")
 # reasoning 또는 agent_message 는 text 를 반환하다
 if item_type in ("reasoning", "agent_message"):
 text = item.get("text", "")
 return text if text else None
 # command_execution: 명령어 + 출력의선두행를표시
 if item_type == "command_execution":
 command = item.get("command", "")
 output = item.get("aggregated_output", "")
 exit_code = item.get("exit_code")
 # 명령어부분를정형(/bin/bash -lc 'cd ... && cmd' 부터 cmd 부분를추출)
 if " && " in command:
 command = command.split(" && ", 1)[-1].rstrip("'")
 elif command.startswith("/bin/bash") and "'" in command:
 # 폴백: シングルクォート内를 추출
 command = command.split("'", 1)[-1].rstrip("'")
 # 출력를선두3행에제한
 max_lines = 3
 lines = output.strip().split("\n") if output else []
 if len(lines) > max_lines:
 truncated = "\n > ".join(lines[:max_lines])
 result = f"$ {command}\n > {truncated}\n > ... ({len(lines) - max_lines} more lines)"
 elif lines:
 result = f"$ {command}\n > " + "\n > ".join(lines)
 else:
 result = f"$ {command}"
 # exit_code 이 비0의 경우는표시
 if exit_code and exit_code != 0:
 result += f" [exit: {exit_code}]"
 return result
 return None

 # Claude stream-json 형식:
 # {"type":"result",...,"result":"text string"} - 최종결과(문자열)
 # {"type":"assistant","message":{"content":[{"type":"text","text":"..."}]}} - 응답
 # {"type":"system",...} - 초기화정보(스킵)
 if tool_name == "claude":
 msg_type = data.get("type")

 # msg_type: result - 최종결과(result 는 문자열)
 if msg_type == "result":
 result = data.get("result")
 if isinstance(result, str) and result:
 return result
 return None

 # msg_type: assistant - 응답메시지(content 配列부터텍스트추출)
 if msg_type == "assistant":
 message = data.get("message", {})
 if isinstance(message, dict):
 content = message.get("content", [])
 texts = [c.get("text", "") for c in content if c.get("type") == "text"]
 return "\n".join(texts) if texts else None
 return None

 # msg_type: system 등는스킵
 return None

 return None


def run_cli_streaming(
 args: list[str],
 timeout: int | None = None,
 verbose: bool | None = None,
 env: dict[str, str] | None = None,
 log_dir: Path | None = None,
 tool_name: str | None = None,
) -> tuple[str, str, int]:
 """CLI 를 스트리밍실행し, (stdout, stderr, returncode) 를 반환하다

 リアルタイム로 출력를표시しながら, JSON 파싱用에 출력를버퍼リング한다.
 log_dir 이 지정된경우, stdout.log / stderr.log / cli_console.log 를 저장한다.
 로그파일는即座에 flush 된다때문에, tail -f でリアルタイム감시가능.

 Args:
 args: 실행한다명령어와인수의리스트
 timeout: 타임아웃초수(None で無제한)
 verbose: 출력를リアルタイム표시한다か(None 로 config 부터취득)
 env: 환경변수(None 로 현재의환경를상속)
 log_dir: 로그저장디렉토리(None 로 저장하지 않는다)
 tool_name: 도구명 ("gemini", "codex", "claude").지정時는 콘텐츠추출

 Returns:
 tuple[str, str, int]: (stdout, stderr, returncode)

 Raises:
 FileNotFoundError: 명령어를 찾를 찾을 수 없다경우
 subprocess.TimeoutExpired: 타임아웃한 경우

 Example:
 リアルタイム로그감시:
 $ tail -f /path/to/log_dir/cli_console.log
 """
 if verbose is None:
 verbose = get_config_value("agent.verbose", True)

 process = subprocess.Popen(
 args,
 stdout=subprocess.PIPE,
 stderr=subprocess.PIPE,
 text=True,
 env=env,
 )

 stdout_lines: list[str] = []
 stderr_lines: list[str] = []
 console_lines: list[str] = [] # 정형완료콘솔출력

 # 타임아웃용타이머(案B: threading.Timer)
 # stdout 읽기ループ이 블록하여도 확실에프로세스를종료한다
 timeout_occurred = threading.Event()
 timer: threading.Timer | None = None

 def kill_on_timeout() -> None:
 """타임아웃時에 프로세스를강제종료"""
 timeout_occurred.set()
 process.kill()

 if timeout is not None:
 timer = threading.Timer(timeout, kill_on_timeout)
 timer.start()

 # 로그파일를事前에 열다(即時 flush 用)
 stdout_file = None
 stderr_file = None
 console_file = None
 if log_dir is not None:
 log_dir.mkdir(parents=True, exist_ok=True)
 stdout_file = open(log_dir / "stdout.log", "w") # noqa: SIM115
 stderr_file = open(log_dir / "stderr.log", "w") # noqa: SIM115
 # tool_name 지정시만콘솔로그를 생성
 if tool_name:
 console_file = open(log_dir / "cli_console.log", "w") # noqa: SIM115

 try:
 # stdout をリアルタイム읽기
 assert process.stdout is not None # for type checker
 for line in process.stdout:
 stdout_lines.append(line)

 # 로그파일에即時쓰기
 if stdout_file:
 stdout_file.write(line)
 stdout_file.flush()

 # 정형출력(tool_name 이 지정되어 있다경우)
 if tool_name:
 formatted = format_jsonl_line(line, tool_name)
 if formatted:
 console_lines.append(formatted)
 # 콘솔로그에即時쓰기
 if console_file:
 console_file.write(formatted + "\n")
 console_file.flush()
 if verbose:
 print(formatted, flush=True)
 elif verbose:
 # 포맷할 수 없다행도표시(진척확인때문)
 print(line, end="", flush=True)
 elif verbose:
 print(line, end="", flush=True)

 # stderr 를 읽기
 assert process.stderr is not None # for type checker
 for line in process.stderr:
 if verbose:
 print(line, end="", file=sys.stderr, flush=True)
 stderr_lines.append(line)

 # 로그파일에即時쓰기
 if stderr_file:
 stderr_file.write(line)
 stderr_file.flush()

 returncode = process.wait()

 # 타임아웃이발생하여いた경우는예외를送出
 if timeout_occurred.is_set():
 raise subprocess.TimeoutExpired(args, timeout or 0)

 finally:
 # 타이머를취소(정상완료시)
 if timer is not None:
 timer.cancel()
 # 파일를확실에クローズ
 if stdout_file:
 stdout_file.close()
 if stderr_file:
 stderr_file.close()
 if console_file:
 console_file.close()

 stdout = "".join(stdout_lines)
 stderr = "".join(stderr_lines)

 return stdout, stderr, returncode
