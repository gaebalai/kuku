"""Run logger for kuku_harness.

JSONL format execution logger with immediate flush.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import CostInfo, Verdict


@dataclass
class RunLogger:
    """JSONL 형식의실행로그를출력한다클래스."""

    log_path: Path

    def __post_init__(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _write(self, event: str, **kwargs: Any) -> None:
        """이벤트를 JSONL 형식로출력."""
        entry: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "event": event,
            **kwargs,
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            f.flush()

    def log_workflow_start(self, issue: int, workflow: str) -> None:
        """워크플로우시작이벤트를기록."""
        self._write("workflow_start", issue=issue, workflow=workflow)

    def log_step_start(
        self,
        step_id: str,
        agent: str,
        model: str | None,
        effort: str | None,
        session_id: str | None,
    ) -> None:
        """스텝시작이벤트를기록."""
        self._write(
            "step_start",
            step_id=step_id,
            agent=agent,
            model=model,
            effort=effort,
            session_id=session_id,
        )

    def log_step_end(
        self,
        step_id: str,
        verdict: Verdict,
        duration_ms: int,
        cost: CostInfo | None,
    ) -> None:
        """스텝종료이벤트를기록."""
        self._write(
            "step_end",
            step_id=step_id,
            verdict=asdict(verdict),
            duration_ms=duration_ms,
            cost=asdict(cost) if cost else None,
        )

    def log_cycle_iteration(self, cycle_name: str, iteration: int, max_iter: int) -> None:
        """사이클 이터레이션 이벤트를 기록."""
        self._write(
            "cycle_iteration",
            cycle_name=cycle_name,
            iteration=iteration,
            max_iterations=max_iter,
        )

    def log_workflow_end(
        self,
        status: str,
        cycle_counts: dict[str, int],
        total_duration_ms: int,
        total_cost: float | None,
        error: str | None = None,
    ) -> None:
        """워크플로우종료이벤트를기록."""
        kwargs: dict[str, Any] = {
            "status": status,
            "cycle_counts": cycle_counts,
            "total_duration_ms": total_duration_ms,
            "total_cost": total_cost,
        }
        if error is not None:
            kwargs["error"] = error
        self._write("workflow_end", **kwargs)
