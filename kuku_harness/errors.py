"""Custom exceptions for kuku_harness."""

from __future__ import annotations

from pathlib import Path


class HarnessError(Exception):
    """하네스의 기저 예외."""


# --- 설정에러 ---
class ConfigNotFoundError(HarnessError):
    """.kuku/config.toml을 찾을 수 없다."""

    def __init__(self, start_dir: Path):
        self.start_dir = start_dir
        super().__init__(f".kuku/config.toml not found. Searched from {self.start_dir} to /.")


class ConfigLoadError(HarnessError):
    """.kuku/config.toml의 읽기·검증 에러."""

    def __init__(self, path: Path, reason: str):
        self.path = path
        self.reason = reason
        super().__init__(f"Error loading {path}: {reason}")


# --- 워크플로우 정의 에러 (기동 시 검출) ---
class WorkflowValidationError(HarnessError):
    """워크플로우 YAML의 정적 검증 에러."""

    def __init__(self, errors: list[str] | str):
        if isinstance(errors, list):
            self.errors = errors
            msg = f"{len(errors)} validation error(s): " + "; ".join(errors)
        else:
            self.errors = [errors]
            msg = errors
        super().__init__(msg)


# --- 스킬 해결 에러 ---
class SkillNotFound(HarnessError):
    """스킬 파일을 찾을 수 없다."""


class SecurityError(HarnessError):
    """경로 트래버설 등의 보안 위반."""


# --- CLI 실행에러 ---
class CLIExecutionError(HarnessError):
    """CLI 프로세스가 비정상 종료."""

    def __init__(self, step_id: str, returncode: int, stderr: str):
        self.step_id = step_id
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"Step '{step_id}' CLI exited with code {returncode}: {stderr[:200]}")


class CLINotFoundError(HarnessError):
    """CLI 명령어를 찾을 수 없다 (FileNotFoundError를 래핑)."""


class StepTimeoutError(HarnessError):
    """스텝이 타임아웃. SIGTERM → SIGKILL 후에 raise."""

    def __init__(self, step_id: str, timeout: int):
        self.step_id = step_id
        self.timeout = timeout
        super().__init__(f"Step '{step_id}' timed out after {timeout}s")


class MissingResumeSessionError(HarnessError):
    """resume 지정 스텝에서 계속 원래의 세션 ID를 찾을 수 없다."""

    def __init__(self, step_id: str, resume_target: str):
        self.step_id = step_id
        self.resume_target = resume_target
        super().__init__(
            f"Step '{step_id}' requires resume from '{resume_target}' but no session ID found"
        )


# --- Verdict 에러 ---
class VerdictNotFound(HarnessError):
    """출력에 ---VERDICT--- 블록이 없다. 회복 불능."""


class VerdictParseError(HarnessError):
    """필수 필드 결손. 회복 불능."""


class InvalidVerdictValue(HarnessError):
    """on에 미정의 status 값. 프롬프트 위반. 회복 불능·리트라이 불가."""


# --- 전이에러 ---
class InvalidTransition(HarnessError):
    """verdict.status에 대응하는 전이처가 on에 미정의."""

    def __init__(self, step_id: str, verdict_status: str):
        self.step_id = step_id
        self.verdict_status = verdict_status
        super().__init__(f"Step '{step_id}' has no transition for verdict '{verdict_status}'")
