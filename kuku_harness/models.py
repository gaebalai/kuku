"""Data models for kuku_harness."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CostInfo:
    """CLI 실행 코스트 정보."""

    usd: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass
class Verdict:
    """스텝출력부터추출한판정결과."""

    status: str
    reason: str
    evidence: str
    suggestion: str


@dataclass
class CLIResult:
    """CLI 프로세스의실행결과."""

    full_output: str
    session_id: str | None = None
    cost: CostInfo | None = None
    stderr: str = ""


@dataclass
class Step:
    """워크플로우 내 1스텝 정의."""

    id: str
    skill: str
    agent: str
    model: str | None = None
    effort: str | None = None
    max_budget_usd: float | None = None
    max_turns: int | None = None
    timeout: int | None = None
    resume: str | None = None
    inject_verdict: bool = False
    on: dict[str, str] = field(default_factory=dict)


@dataclass
class CycleDefinition:
    """루프 사이클 정의."""

    name: str
    entry: str
    loop: list[str]
    max_iterations: int
    on_exhaust: str


@dataclass
class Workflow:
    """워크플로우전체의정의."""

    name: str
    description: str
    execution_policy: str
    steps: list[Step]
    cycles: list[CycleDefinition] = field(default_factory=list)
    default_timeout: int | None = None

    def find_step(self, step_id: str) -> Step | None:
        """ID로 스텝을 검색. 찾지 못하면 None."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def find_start_step(self) -> Step:
        """첫 번째 스텝을 반환한다."""
        return self.steps[0]

    def find_cycle_for_step(self, step_id: str) -> CycleDefinition | None:
        """스텝이 속한 사이클을 검색. 찾지 못하면 None."""
        for cycle in self.cycles:
            if step_id in cycle.loop or step_id == cycle.entry:
                return cycle
        return None
