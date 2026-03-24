"""Context building utilities for Bugfix Agent v5

This module provides context data construction:
- build_context: Build context from text or file paths with security checks
"""

from pathlib import Path

from .config import get_config_value, get_workdir


def build_context(
 context: str | list[str],
 max_chars: int | None = None,
 allowed_root: Path | None = None,
) -> str:
 """컨텍스트データ를 구축한다(공통유틸리티)

 Args:
 context: 컨텍스트정보
 - str: 텍스트로서그まま반환하다(max_chars 로 절단)
 - list[str]: 파일경로리스트로서각파일를읽기
 max_chars: 최대문자수(None 로 config 부터취득, 0 で無제한)
 allowed_root: 읽기허가한다루트디렉토리(Path Traversal 대책)
 None 의 경우는 get_workdir() 를 사용
 logger: 실행ロガー

 Returns:
 구축된컨텍스트문자열

 Raises:
 ValueError: 허가되어 있지 않다경로로의접근試행시
 """

 # 문자열입력의 경우도max_chars적용
 if isinstance(context, str):
 if max_chars is None:
 max_chars = get_config_value("tools.context_max_chars", 4000)
 if max_chars and len(context) > max_chars:
 return context[:max_chars]
 return context

 # 파일경로리스트의 경우
 if allowed_root is None:
 allowed_root = get_workdir()
 allowed_root = allowed_root.resolve()

 result_parts: list[str] = []
 for path_str in context:
 path = Path(path_str)
 if not path.exists():
 continue

 # Path Traversal 대책: 허가된루트하위か체크
 try:
 resolved = path.resolve()
 resolved.relative_to(allowed_root)
 except ValueError:
 # allowed_root 하위로없다경우는스킵(경고출력)
 print(f"⚠️ Skipping path outside allowed_root: {path_str}")
 continue

 try:
 content = resolved.read_text(encoding="utf-8")
 result_parts.append(f"\n--- {path_str} ---\n{content}\n")
 except (PermissionError, OSError) as e:
 print(f"⚠️ Failed to read {path_str}: {e}")
 continue

 result = "".join(result_parts)

 # 최대문자수제한
 if max_chars is None:
 max_chars = get_config_value("tools.context_max_chars", 4000)
 if max_chars and len(result) > max_chars:
 result = result[:max_chars]

 return result
