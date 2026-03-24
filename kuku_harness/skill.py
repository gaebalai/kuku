"""Skill validation for kuku_harness."""

from pathlib import Path

from .errors import SecurityError, SkillNotFound


def validate_skill_exists(skill_name: str, workdir: Path, skill_dir: str) -> None:
    """CLI 기동 전 스킬 존재 확인 (pre-flight check).

    Args:
        skill_name: 스킬명
        workdir: 프로젝트 루트 디렉토리
        skill_dir: 스킬 디렉토리 (workdir에서의 상대 경로)

    Raises:
        SkillNotFound: 스킬 파일을 찾을 수 없다
        SecurityError: 경로 트래버설 검출
    """
    # 경로 트래버설 방어 (resolve 전에 체크)
    if ".." in skill_name.split("/"):
        raise SecurityError(f"Skill name contains path traversal: {skill_name}")

    base = workdir / skill_dir / skill_name / "SKILL.md"
    resolved = base.resolve()

    if not resolved.is_relative_to(workdir.resolve()):
        raise SecurityError(f"Skill path escapes workdir: {resolved}")

    if not resolved.exists():
        raise SkillNotFound(f"{base} not found")
