# 워크플로우 가이드

## 워크플로우 선택 기준

| Issue 종류 | 사용할 워크플로우 |
|-------------|---------------------|
| 기능 추가·버그 수정·리팩터 | feature-development |
| 문서 수정만 | docs-maintenance |

## feature-development

코드 변경을 수반하는 Issue의 워크플로우. 설계 → 구현 → 코드 리뷰 → 문서 체크 → PR.

상세: [workflow_feature_development.md](workflow_feature_development.md)

## docs-maintenance

문서 수정만의 Issue 워크플로우. 코드·설정·테스트는 변경하지 않고, 현행 구현과의 정합성을 감사하면서 docs를 업데이트한다.

상세: [workflow_docs_maintenance.md](workflow_docs_maintenance.md)
