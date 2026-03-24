"""Workflow execution runner for kuku_harness.

Main loop that executes workflow steps sequentially,
manages state transitions, and handles cycle limits.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .cli import execute_cli
from .config import kukuConfig
from .errors import (
    InvalidTransition,
    MissingResumeSessionError,
    WorkflowValidationError,
)
from .logger import RunLogger
from .models import CostInfo, Verdict, Workflow
from .prompt import build_prompt
from .skill import validate_skill_exists
from .state import SessionState
from .verdict import create_verdict_formatter, parse_verdict
from .workflow import validate_workflow


@dataclass
class WorkflowRunner:
    """워크플로우 실행 엔진."""

    workflow: Workflow
    issue_number: int
    project_root: Path
    artifacts_dir: Path
    config: kukuConfig
    from_step: str | None = None
    single_step: str | None = None
    verbose: bool = True

    def run(self) -> SessionState:
        """워크플로우를 실행하고 최종 상태를 반환한다.

        Returns:
            SessionState: 실행 후 세션 상태

        Raises:
            WorkflowValidationError: 워크플로우 정의 에러
            MissingResumeSessionError: resume 대상의 세션 ID를 찾을 수 없다
            InvalidTransition: verdict에 대응하는 전이처가 없다
        """
        execution_policy = self.workflow.execution_policy or "auto"

        # 0. 전 스텝의 스킬 존재를 사전 검증
        for step in self.workflow.steps:
            validate_skill_exists(step.skill, self.project_root, self.config.paths.skill_dir)

        # 1. 워크플로우정의의밸리데이션
        validate_workflow(self.workflow)

        # 2. issue 단위 상태를 로드
        state = SessionState.load_or_create(self.issue_number, self.artifacts_dir)

        # 3. run 로그디렉토리를 생성
        run_dir = (
            self.artifacts_dir
            / str(self.issue_number)
            / "runs"
            / datetime.now().strftime("%y%m%d%H%M")
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        logger = RunLogger(log_path=run_dir / "run.log")
        logger.log_workflow_start(self.issue_number, self.workflow.name)

        # 4. 시작스텝의결정
        if self.single_step:
            current_step = self.workflow.find_step(self.single_step)
            if not current_step:
                raise WorkflowValidationError(f"Step '{self.single_step}' not found")
        elif self.from_step:
            current_step = self.workflow.find_step(self.from_step)
            if not current_step:
                raise WorkflowValidationError(f"Step '{self.from_step}' not found")
        else:
            current_step = self.workflow.find_start_step()

        total_cost = 0.0
        workflow_start = time.monotonic()
        end_status = "COMPLETE"
        end_error: str | None = None
        last_verdict: Verdict | None = None

        # 5. 메인 루프
        try:
            while current_step and current_step.id != "end":
                start_time = time.monotonic()
                cycle = self.workflow.find_cycle_for_step(current_step.id)

                # 사이클상한체크
                if cycle and state.cycle_iterations(cycle.name) >= cycle.max_iterations:
                    verdict = Verdict(
                        status=cycle.on_exhaust,
                        reason=f"Cycle '{cycle.name}' exhausted",
                        evidence=f"{cycle.max_iterations} iterations reached",
                        suggestion="수동로확인해 주세요",
                    )
                    cost: CostInfo | None = None
                else:
                    # 프롬프트구축
                    prompt = build_prompt(current_step, self.issue_number, state, self.workflow)

                    # 세션 ID 취득
                    session_id = (
                        state.get_session_id(current_step.resume) if current_step.resume else None
                    )
                    if current_step.resume and session_id is None:
                        raise MissingResumeSessionError(current_step.id, current_step.resume)

                    # 로그디렉토리
                    step_log_dir = run_dir / current_step.id
                    step_log_dir.mkdir(parents=True, exist_ok=True)

                    logger.log_step_start(
                        current_step.id,
                        current_step.agent,
                        current_step.model,
                        current_step.effort,
                        session_id,
                    )

                    # 타임아웃해결: workflow.default_timeout → config.execution.default_timeout
                    default_timeout = (
                        self.workflow.default_timeout
                        if self.workflow.default_timeout is not None
                        else self.config.execution.default_timeout
                    )

                    # CLI 실행
                    result = execute_cli(
                        step=current_step,
                        prompt=prompt,
                        workdir=self.project_root,
                        session_id=session_id,
                        log_dir=step_log_dir,
                        execution_policy=execution_policy,
                        verbose=self.verbose,
                        default_timeout=default_timeout,
                    )

                    # 세션 ID 저장
                    if result.session_id:
                        state.save_session_id(current_step.id, result.session_id)
                    cost = result.cost

                    # verdict 파싱 (3-stage fallback: strict → relaxed → AI formatter)
                    valid = set(current_step.on.keys())
                    formatter = create_verdict_formatter(
                        agent=current_step.agent,
                        valid_statuses=valid,
                        model=current_step.model,
                        workdir=self.project_root,
                    )
                    verdict = parse_verdict(
                        result.full_output,
                        valid_statuses=valid,
                        ai_formatter=formatter,
                    )

                # 로그기록 + 상태업데이트
                duration_ms = int((time.monotonic() - start_time) * 1000)
                logger.log_step_end(current_step.id, verdict, duration_ms, cost)
                state.record_step(current_step.id, verdict)
                last_verdict = verdict

                if cost and cost.usd:
                    total_cost += cost.usd

                # 사이클 카운트
                if cycle and current_step.id == cycle.loop[-1] and verdict.status == "RETRY":
                    state.increment_cycle(cycle.name)
                    logger.log_cycle_iteration(
                        cycle.name,
                        state.cycle_iterations(cycle.name),
                        cycle.max_iterations,
                    )

                # 다음스텝를결정
                if self.single_step:
                    break

                next_step_id = current_step.on.get(verdict.status)
                if next_step_id is None:
                    raise InvalidTransition(current_step.id, verdict.status)
                current_step = self.workflow.find_step(next_step_id)

            # 정상 종료 시 스테이터스 판정
            if last_verdict and last_verdict.status == "ABORT":
                end_status = "ABORT"
        except Exception as exc:
            end_status = "ERROR"
            end_error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            total_duration_ms = int((time.monotonic() - workflow_start) * 1000)
            logger.log_workflow_end(
                end_status,
                state.cycle_counts,
                total_duration_ms=total_duration_ms,
                total_cost=total_cost if total_cost > 0 else None,
                error=end_error,
            )
        return state
