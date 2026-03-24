"""Workflow YAML loader and validator for kuku_harness."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .errors import WorkflowValidationError
from .models import CycleDefinition, Step, Workflow


def load_workflow(path: Path) -> Workflow:
    """YAML 파일에서 워크플로우 정의를 로드한다.

    Args:
        path: 워크플로우 정의 파일의 경로

    Returns:
        Workflow: 파싱된 워크플로우 정의

    Raises:
        WorkflowValidationError: YAML 파싱 에러 또는 밸리데이션 에러
    """
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise WorkflowValidationError(f"YAML parse error: {e}") from e
    return _parse_workflow(data)


def load_workflow_from_str(yaml_str: str) -> Workflow:
    """YAML 문자열에서 워크플로우 정의를 로드한다.

    Args:
        yaml_str: 워크플로우 정의의 YAML 문자열

    Returns:
        Workflow: 파싱된 워크플로우 정의

    Raises:
        WorkflowValidationError: YAML 파싱 에러 또는 밸리데이션 에러
    """
    try:
        data = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        raise WorkflowValidationError(f"YAML parse error: {e}") from e
    return _parse_workflow(data)


VALID_EXECUTION_POLICIES = {"auto", "sandbox", "interactive"}

_STEP_REQUIRED_KEYS = ("id", "skill", "agent")


def _parse_workflow(data: dict[str, Any]) -> Workflow:
    """YAML data dict를 워크플로우 오브젝트로 변환한다."""
    if not isinstance(data, dict):
        raise WorkflowValidationError("Workflow definition must be a YAML mapping")

    raw_steps = data.get("steps", [])
    if raw_steps is None:
        raise WorkflowValidationError("'steps' must be a list, got null")
    if not isinstance(raw_steps, list):
        raise WorkflowValidationError(f"'steps' must be a list, got {type(raw_steps).__name__}")

    steps = []
    for i, step_data in enumerate(raw_steps):
        if not isinstance(step_data, dict):
            raise WorkflowValidationError(
                f"Step at index {i} must be a mapping, got {type(step_data).__name__}"
            )
        missing = [k for k in _STEP_REQUIRED_KEYS if k not in step_data]
        if missing:
            raise WorkflowValidationError(
                f"Step at index {i} missing required key(s): {', '.join(missing)}"
            )
        if "on" in step_data:
            raw_on = step_data["on"]
        elif True in step_data:
            # YAML 1.1 interprets bare `on` as boolean True
            raw_on = step_data[True]
        else:
            raise WorkflowValidationError(f"Step '{step_data['id']}' missing required key 'on'")
        if not isinstance(raw_on, dict):
            raise WorkflowValidationError(
                f"Step '{step_data['id']}' 'on' must be a mapping, got {type(raw_on).__name__}"
            )
        if not raw_on:
            raise WorkflowValidationError(f"Step '{step_data['id']}' 'on' must not be empty")
        raw_inject_verdict = step_data.get("inject_verdict", False)
        if not isinstance(raw_inject_verdict, bool):
            raise WorkflowValidationError(
                f"Step '{step_data['id']}' 'inject_verdict' must be a boolean, "
                f"got {type(raw_inject_verdict).__name__}"
            )
        raw_timeout = step_data.get("timeout")
        if raw_timeout is not None:
            if not isinstance(raw_timeout, int) or isinstance(raw_timeout, bool):
                raise WorkflowValidationError(
                    f"Step '{step_data['id']}' 'timeout' must be an integer, "
                    f"got {type(raw_timeout).__name__}"
                )
            if raw_timeout <= 0:
                raise WorkflowValidationError(
                    f"Step '{step_data['id']}' 'timeout' must be a positive integer, "
                    f"got {raw_timeout}"
                )
        steps.append(
            Step(
                id=step_data["id"],
                skill=step_data["skill"],
                agent=step_data["agent"],
                model=step_data.get("model"),
                effort=step_data.get("effort"),
                max_budget_usd=step_data.get("max_budget_usd"),
                max_turns=step_data.get("max_turns"),
                timeout=raw_timeout,
                resume=step_data.get("resume"),
                inject_verdict=raw_inject_verdict,
                on=raw_on,
            )
        )

    raw_cycles = data.get("cycles", {})
    if raw_cycles is None:
        raw_cycles = {}
    if not isinstance(raw_cycles, dict):
        raise WorkflowValidationError(
            f"'cycles' must be a mapping, got {type(raw_cycles).__name__}"
        )

    cycles = []
    for cycle_name, cycle_data in raw_cycles.items():
        if not isinstance(cycle_data, dict):
            raise WorkflowValidationError(
                f"Cycle '{cycle_name}' must be a mapping, got {type(cycle_data).__name__}"
            )
        cycle_required = ("entry", "loop", "max_iterations", "on_exhaust")
        missing_cycle = [k for k in cycle_required if k not in cycle_data]
        if missing_cycle:
            raise WorkflowValidationError(
                f"Cycle '{cycle_name}' missing required key(s): {', '.join(missing_cycle)}"
            )
        raw_loop = cycle_data["loop"]
        if not isinstance(raw_loop, list):
            raise WorkflowValidationError(
                f"Cycle '{cycle_name}' 'loop' must be a list, got {type(raw_loop).__name__}"
            )
        raw_max_iter = cycle_data["max_iterations"]
        if not isinstance(raw_max_iter, int) or isinstance(raw_max_iter, bool):
            raise WorkflowValidationError(
                f"Cycle '{cycle_name}' 'max_iterations' must be an integer, "
                f"got {type(raw_max_iter).__name__}"
            )
        if raw_max_iter < 1:
            raise WorkflowValidationError(
                f"Cycle '{cycle_name}' 'max_iterations' must be >= 1, got {raw_max_iter}"
            )
        cycles.append(
            CycleDefinition(
                name=cycle_name,
                entry=cycle_data["entry"],
                loop=raw_loop,
                max_iterations=raw_max_iter,
                on_exhaust=cycle_data["on_exhaust"],
            )
        )

    execution_policy = data.get("execution_policy", "auto")
    if execution_policy not in VALID_EXECUTION_POLICIES:
        raise WorkflowValidationError(
            f"execution_policy must be one of {sorted(VALID_EXECUTION_POLICIES)}, "
            f"got '{execution_policy}'"
        )

    raw_default_timeout = data.get("default_timeout")
    if raw_default_timeout is not None:
        if not isinstance(raw_default_timeout, int) or isinstance(raw_default_timeout, bool):
            raise WorkflowValidationError(
                f"'default_timeout' must be an integer, got {type(raw_default_timeout).__name__}"
            )
        if raw_default_timeout <= 0:
            raise WorkflowValidationError(
                f"'default_timeout' must be a positive integer, got {raw_default_timeout}"
            )

    return Workflow(
        name=data.get("name", ""),
        description=data.get("description", ""),
        execution_policy=execution_policy,
        steps=steps,
        cycles=cycles,
        default_timeout=raw_default_timeout,
    )


def validate_workflow(workflow: Workflow) -> None:
    """워크플로우 정의의 정적 검증.

    Args:
        workflow: 검증 대상 워크플로우

    Raises:
        WorkflowValidationError: 검증 에러가 있는 경우
    """
    errors: list[str] = []
    valid_verdicts = {"PASS", "RETRY", "BACK", "ABORT"}
    # on이 부정한 step id를 수집. cycle 전이 체크(.on.get() 호출)에서 제외하기 위해 사용
    invalid_on_step_ids: set[str] = set()

    # ---- 스키마 레벨 밸리데이션 ----
    # default_timeout 검증 (_parse_workflow()를 경유하지 않는 경우도 담보)
    if workflow.default_timeout is not None:
        if (
            not isinstance(workflow.default_timeout, int)
            or isinstance(workflow.default_timeout, bool)
            or workflow.default_timeout <= 0
        ):
            errors.append(
                f"'default_timeout' must be a positive integer, got {workflow.default_timeout!r}"
            )

    # execution_policy의 enum 검증 (_parse_workflow()를 경유하지 않는 경우도 담보)
    if workflow.execution_policy not in VALID_EXECUTION_POLICIES:
        errors.append(
            f"execution_policy must be one of {sorted(VALID_EXECUTION_POLICIES)}, "
            f"got '{workflow.execution_policy}'"
        )

    # 워크플로우 레벨 검증
    if not workflow.steps:
        errors.append("Workflow must have at least one step")

    # 스텝 레벨 검증
    for step in workflow.steps:
        # 스키마: step.timeout 검증 (_parse_workflow()를 경유하지 않는 경우도 담보)
        if step.timeout is not None:
            if (
                not isinstance(step.timeout, int)
                or isinstance(step.timeout, bool)
                or step.timeout <= 0
            ):
                errors.append(
                    f"Step '{step.id}' 'timeout' must be a positive integer, got {step.timeout!r}"
                )

        # 스키마: step.on은 비어있지 않은 dict일 것
        if not isinstance(step.on, dict) or not step.on:
            errors.append(f"Step '{step.id}' 'on' must be a non-empty mapping")
            invalid_on_step_ids.add(step.id)
            # on이 부정한 경우, 이후 전이 검증은 스킵
            if step.resume:
                target = workflow.find_step(step.resume)
                if not target:
                    errors.append(f"Step '{step.id}' resumes unknown step '{step.resume}'")
                elif target.agent != step.agent:
                    errors.append(
                        f"Step '{step.id}' resumes '{step.resume}' but agents differ "
                        f"({step.agent} != {target.agent})"
                    )
            continue

        # 1. resume 대상이 존재하고, 동일 agent일 것
        if step.resume:
            target = workflow.find_step(step.resume)
            if not target:
                errors.append(f"Step '{step.id}' resumes unknown step '{step.resume}'")
            elif target.agent != step.agent:
                errors.append(
                    f"Step '{step.id}' resumes '{step.resume}' but agents differ "
                    f"({step.agent} != {target.agent})"
                )

        # 2. on의 전이처가 존재할 것
        for verdict, next_id in step.on.items():
            if next_id != "end" and not workflow.find_step(next_id):
                errors.append(
                    f"Step '{step.id}' transitions to unknown step '{next_id}' on {verdict}"
                )

        # 3. verdict 값이 유효할 것
        for verdict in step.on:
            if verdict not in valid_verdicts:
                errors.append(f"Step '{step.id}' has invalid verdict '{verdict}'")

    # 사이클레벨의검증
    for cycle in workflow.cycles:
        # 스키마: cycle.loop는 list일 것
        if not isinstance(cycle.loop, list):
            errors.append(
                f"Cycle '{cycle.name}' 'loop' must be a list, got {type(cycle.loop).__name__}"
            )
            continue

        # 스키마: cycle.max_iterations는 양의 정수일 것
        if (
            not isinstance(cycle.max_iterations, int)
            or isinstance(cycle.max_iterations, bool)
            or cycle.max_iterations < 1
        ):
            errors.append(
                f"Cycle '{cycle.name}' 'max_iterations' must be an integer >= 1, "
                f"got {cycle.max_iterations!r}"
            )

        # 4. loop가 비어있지 않을 것
        if not cycle.loop:
            errors.append(f"Cycle '{cycle.name}' loop must not be empty")
            continue

        # 5. entry 스텝이 존재할 것
        if not workflow.find_step(cycle.entry):
            errors.append(f"Cycle '{cycle.name}' entry step '{cycle.entry}' not found")

        # 6. loop 내 스텝이 존재할 것
        for step_id in cycle.loop:
            if not workflow.find_step(step_id):
                errors.append(f"Cycle '{cycle.name}' loop step '{step_id}' not found")

        # 7. loop 말미 스텝이 RETRY 시 loop 선두로 전이할 것
        # step.on이 부정한 경우는 .get()을 호출하지 않고, 이 검증을 스킵
        tail_step = workflow.find_step(cycle.loop[-1])
        if (
            tail_step
            and tail_step.id not in invalid_on_step_ids
            and tail_step.on.get("RETRY") != cycle.loop[0]
        ):
            errors.append(
                f"Cycle '{cycle.name}' loop tail '{cycle.loop[-1]}' RETRY should "
                f"transition to loop head '{cycle.loop[0]}'"
            )

        # 8. entry/loop 내 스텝이 PASS 시 사이클 외부로 전이할 것
        # step.on이 부정한 스텝은 exit 판정에서 제외
        all_cycle_steps = {cycle.entry} | set(cycle.loop)
        has_exit = False
        for cycle_step_id in all_cycle_steps:
            if cycle_step_id in invalid_on_step_ids:
                continue
            cycle_step = workflow.find_step(cycle_step_id)
            if cycle_step and cycle_step.on.get("PASS") not in all_cycle_steps:
                has_exit = True
                break
        if not has_exit:
            errors.append(f"Cycle '{cycle.name}' has no exit (PASS never leaves the cycle)")

        # 9. on_exhaust가 유효한 verdict일 것
        if cycle.on_exhaust not in valid_verdicts:
            errors.append(f"Cycle '{cycle.name}' on_exhaust '{cycle.on_exhaust}' is invalid")

    if errors:
        raise WorkflowValidationError(errors)
