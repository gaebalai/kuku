# QA Review Prompt

Issue ${issue_url} 의 `## Bugfix agent QA` 섹션를리뷰해 주세요.

## 태스크

1. `gh issue view` 로 최신의 Issue 本文를 취득
2. QA 섹션의필수아웃풋를확인
3. PR_CREATE 스테이트に移행가능か판정

## 완료조건체크리스트

| # | 항목 | 확인내용 |
|---|---|---|
| 1 | **소스리뷰** | 소스리뷰의 관점와결과이타당이다 |
| 2 | **추가테스트결과** | 추가테스트이실행され, 결과이기재되어 있다 |
| 3 | **전체품질** | 구현품질이PR생성에進む위해十분한 레벨에達하고 있다 |

## 금지事項

**次스테이트이후의책무를신규에실행하지 않는다**
- 예：PR생성, 머지

**既에 완료한책무를재실행하지 않는다**
- 예：설계를作り直す, 조사를재실행

※ 기재내용의검증(품질 체크, 정합성확인)는**허가**されてい합니다.

## 출력형식

```markdown
### QA Review Result

#### 검증내용
- <실시한검증와결과를구체적에기재>

#### 체크리스트
- 소스리뷰: <OK/NG + 구체적근거>
- 추가테스트결과: <OK/NG + 구체적근거>
- 전체품질: <OK/NG + 구체적근거>

## VERDICT
- Result: PASS | RETRY_QA | RETRY_IMPLEMENT | BACK_DESIGN
- Reason: <판정이유>
- Evidence: <구체적한 판단근거>
- Suggestion: <RETRY/BACK時: 구체적한 수정指示>
```

## 판정가이드ラ인

| 상황 | VERDICT | 다음스테이트 |
|---|---|---|
| QA완료, 모순·문제이 없다 | PASS | PR_CREATE |
| QAに軽微な문제가 있り수정이필요 | RETRY_QA | QA |
| 구현에문제가 있り수정이필요 | RETRY_IMPLEMENT | IMPLEMENT |
| 설계레벨의문제가 있り설계부터やり直す필요이 있다 | BACK_DESIGN | DETAIL_DESIGN |

### BACK_DESIGN의판단기준

이하의 경우는 BACK_DESIGN 를 선택:
- QA中에 설계上의 모순이発見된
- 테스트케이스自体에 문제이 있다
- 아키텍처레벨의변경이필요

## レポート방법

1. `gh issue comment` 로 Issue 에 코멘트投稿(VERDICT판정)
2. **PASS판정시만**: 공통규칙에 따라 `gh issue edit` 로 Issue 本文를 업데이트