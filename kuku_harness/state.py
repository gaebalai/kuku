"""Session state management for kuku_harness.

Issue-scoped state that persists across workflow executions.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from .models import Verdict

STATE_FILE = "session-state.json"


@dataclass
class StepRecord:
    """스텝실행기록."""

    step_id: str
    verdict_status: str
    verdict_reason: str
    verdict_evidence: str
    verdict_suggestion: str
    timestamp: str


@dataclass
class SessionState:
    """Issue 단위의세션상태."""

    issue_number: int
    artifacts_dir: Path
    sessions: dict[str, str] = field(default_factory=dict)
    step_history: list[StepRecord] = field(default_factory=list)
    cycle_counts: dict[str, int] = field(default_factory=dict)
    last_completed_step: str | None = None
    last_transition_verdict: Verdict | None = None

    @classmethod
    def load_or_create(cls, issue: int, artifacts_dir: Path) -> SessionState:
        """상태를 로드또는신규생성한다."""
        path = artifacts_dir / str(issue) / STATE_FILE
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            data["step_history"] = [StepRecord(**r) for r in data.get("step_history", [])]
            ltv = data.pop("last_transition_verdict", None)
            if ltv:
                data["last_transition_verdict"] = Verdict(**ltv)
            return cls(artifacts_dir=artifacts_dir, **data)
        return cls(issue_number=issue, artifacts_dir=artifacts_dir)

    @property
    def _state_dir(self) -> Path:
        return self.artifacts_dir / str(self.issue_number)

    def save_session_id(self, step_id: str, session_id: str) -> None:
        """스텝의 세션 ID를 저장하고 즉시 영속화한다."""
        self.sessions[step_id] = session_id
        self._persist()

    def get_session_id(self, resume_target: str | None) -> str | None:
        """resume 대상의 세션 ID를 취득한다."""
        if resume_target is None:
            return None
        return self.sessions.get(resume_target)

    def cycle_iterations(self, cycle_name: str) -> int:
        """사이클의 이터레이션 횟수를 취득한다."""
        return self.cycle_counts.get(cycle_name, 0)

    def increment_cycle(self, cycle_name: str) -> None:
        """사이클의 이터레이션 횟수를 증가시키고 즉시 영속화한다."""
        self.cycle_counts[cycle_name] = self.cycle_iterations(cycle_name) + 1
        self._persist()

    def record_step(self, step_id: str, verdict: Verdict) -> None:
        """스텝 실행 결과를 기록하고 영속화한다."""
        self.step_history.append(
            StepRecord(
                step_id=step_id,
                verdict_status=verdict.status,
                verdict_reason=verdict.reason,
                verdict_evidence=verdict.evidence,
                verdict_suggestion=verdict.suggestion,
                timestamp=datetime.now(UTC).isoformat(),
            )
        )
        self.last_completed_step = step_id
        self.last_transition_verdict = verdict
        self._persist()

    def _persist(self) -> None:
        """JSON + progress.md에 영속화한다."""
        self._state_dir.mkdir(parents=True, exist_ok=True)
        path = self._state_dir / STATE_FILE
        data = {
            "issue_number": self.issue_number,
            "sessions": self.sessions,
            "step_history": [asdict(r) for r in self.step_history],
            "cycle_counts": self.cycle_counts,
            "last_completed_step": self.last_completed_step,
            "last_transition_verdict": asdict(self.last_transition_verdict)
            if self.last_transition_verdict
            else None,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self._write_progress_md()

    def _write_progress_md(self) -> None:
        """사람이 읽을 수 있는 진척 파일을 업데이트한다."""
        lines = [f"# Progress: Issue #{self.issue_number}\n"]
        for record in self.step_history:
            mark = "x" if record.verdict_status == "PASS" else " "
            lines.append(
                f"- [{mark}] {record.step_id}: {record.verdict_status} — {record.verdict_reason}"
            )
        if self.cycle_counts:
            lines.append("\n## 사이클")
            for name, count in self.cycle_counts.items():
                lines.append(f"- {name}: {count} iterations")
        path = self._state_dir / "progress.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
