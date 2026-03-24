# docs-maintenance 워크플로우

docs-only Issue를 위한 문서 수정 워크플로우.

## 플로우 개요

issue-start → i-doc-update → i-doc-review → (i-doc-fix → i-doc-verify) → issue-pr

## 실행 제약

- 코드, 설정, 테스트는 변경하지 않는다
- 사실 확인을 위한 read / search / 명령어 실행은 허가
- docs만으로는 안전하게 흡수할 수 없는 문제는 ABORT

## 각 스킬의 책무

| 스킬 | 책무 | 에이전트 |
|--------|------|-------------|
| i-doc-update | 문서 업데이트 | claude |
| i-doc-review | 정합성 리뷰 (신규 지적 가능) | codex |
| i-doc-fix | 리뷰 지적 대응 | claude |
| i-doc-verify | 수정 확인 (신규 지적 불가) | codex |

## 정합성 감사의 관점

- 현행 코드와의 정합
- CLAUDE.md의 운용 규칙과의 정합
- workflow / skill 구성과의 정합
- 링크 끊김·오래된 명령어 예의 유무

## 링크 체크

- i-doc-update의 초회: `python3 scripts/check_doc_links.py` (전체 체크)
- i-doc-review / i-doc-fix / i-doc-verify: `python3 scripts/check_doc_links.py <변경 파일...>` (한정 체크)

## 리뷰 사이클

- 최대 3 이터레이션 (doc-review cycle)
- 초과 시 ABORT
- BACK은 사용하지 않는다 (PASS / RETRY / ABORT만)
