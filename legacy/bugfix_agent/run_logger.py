"""Run logger for Bugfix Agent v5

This module provides:
- RunLogger: JSONL format execution logger
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class RunLogger:
 """JSONL 형식의실행로그를출력한다클래스

 출력先: test-artifacts/bugfix-agent/<issue-number>/<YYMMDDhhmm>/run.log
 """

 def __init__(self, log_path: Path):
 """ロガー를 초기화

 Args:
 log_path: 로그파일의 경로
 """
 self.log_path = log_path
 self.log_path.parent.mkdir(parents=True, exist_ok=True)

 def _log(self, event: str, **kwargs: Any) -> None:
 """이벤트를 JSONL 형식로출력"""
 entry = {
 "ts": datetime.now(UTC).isoformat(),
 "event": event,
 **kwargs,
 }
 with open(self.log_path, "a", encoding="utf-8") as f:
 f.write(json.dumps(entry, ensure_ascii=False) + "\n")

 def log_run_start(self, issue_url: str, run_id: str) -> None:
 """실행시작이벤트를기록"""
 self._log("run_start", issue_url=issue_url, run_id=run_id)

 def log_state_enter(self, state: str, session_id: str | None = None) -> None:
 """스테이트시작이벤트를기록"""
 kwargs: dict[str, Any] = {"state": state}
 if session_id:
 kwargs["session_id"] = session_id
 self._log("state_enter", **kwargs)

 def log_state_exit(self, state: str, result: str, next_state: str) -> None:
 """스테이트종료이벤트를기록"""
 self._log("state_exit", state=state, result=result, next=next_state)

 def log_run_end(
 self,
 status: str,
 loop_counters: dict[str, int],
 error: str | None = None,
 ) -> None:
 """실행종료이벤트를기록"""
 kwargs: dict[str, Any] = {"status": status, "loop_counters": loop_counters}
 if error:
 kwargs["error"] = error
 self._log("run_end", **kwargs)

 def log_warning(self, message: str, **kwargs: Any) -> None:
 """경고이벤트를기록"""
 self._log("warning", message=message, **kwargs)
