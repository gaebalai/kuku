# IMPLEMENT Review Prompt (QA통합版)

Issue ${issue_url} 의 `## Bugfix agent IMPLEMENT` 섹션를리뷰し, QA관점로의검증를행ってください.

## 역할

IMPLEMENT_REVIEW는 종래의QA/QA_REVIEW를 통합한스테이트입니다.
구현결과의리뷰に加え, QA관점로의검증도동시에 행い합니다.

## 태스크

1. **독립테스트실행**: レビュワー自身이 이하를 실행し, 결과를기록한다
 ```
 ruff check bugfix_agent/ tests/ && ruff format bugfix_agent/ tests/ && mypy bugfix_agent/ && pytest
 ```
2. `gh issue view` 로 최신의 Issue 本文를 취득
3. IMPLEMENT 섹션의필수아웃풋를확인
4. PR_CREATE 스테이트に移행가능か판정

## 완료조건체크리스트

### 구현리뷰관점

| # | 항목 | 확인내용 |
|---|------|----------|
| 1 | **브랜치정보** | 작업브랜치名이 기재되어 있다 |
| 2 | **구현내용** | 변경파일·함수이기재され, 설계通り에 구현되어 있다 |
| 3 | **테스트결과** | DETAIL_DESIGN의테스트케이스이실행され, 결과이기재되어 있다 |

### QA관점(통합)

| # | 항목 | 확인내용 |
|---|------|----------|
| 4 | **소스리뷰** | 변경전체의소스리뷰(diff + 周辺코드)에문제이 없다 |
| 5 | **リグレッション** | 기존기능로의영향이 없다것이확인되어 있다 |
| 6 | **테스트 S/M/L 망라性(PASSED)** | S·M·L 각サイズ의 테스트이구현され, 모두 PASSED 이다こ과 |
| 7 | **독립테스트실행** | レビュワー自身이 pytest 를 실행し, PASS 를 확인하고 있다 |

## 금지事項

**次스테이트이후의책무를신규에실행하지 않는다**
- 예：PR생성, 머지

**既에 완료한책무를재실행하지 않는다**
- 예：설계를作り直す, 조사를재실행

※ 기재내용의검증(품질 체크, 정합성확인)는**허가**されてい합니다.

## 출력형식

```markdown
### IMPLEMENT Review Result (QA통합)

#### 검증내용
- <실시한검증와결과를구체적에기재>

#### 독립테스트실행결과
```
<ruff check / ruff format / mypy / pytest 의 실행로그를貼り付ける>
```

#### 체크리스트
- 브랜치정보: <OK/NG + 구체적근거>
- 구현내용: <OK/NG + 구체적근거>
- 테스트결과: <OK/NG + 구체적근거>
- 테스트 S/M/L 망라性(PASSED): <OK/NG + 각サイズ의 건数>
- 독립테스트실행(PASSED): <OK/NG + pytest サマリー>
- 소스리뷰: <OK/NG + 구체적근거>
- リグレッション: <OK/NG + 구체적근거>

## VERDICT
- Result: PASS | RETRY | BACK_DESIGN
- Reason: <판정이유>
- Evidence: <구체적한 판단근거>
- Suggestion: <RETRY/BACK_DESIGN時: 구체적한 수정指示>
```

## 판정가이드ラ인

| 상황 | VERDICT | 다음스테이트 |
|------|---------|-------------|
| 구현완료, 모순·문제이 없다 | PASS | PR_CREATE |
| 구현에軽微な문제가 있り수정이필요 | RETRY | IMPLEMENT |
| pytest 출력이 Issue 코멘트에기재되어 있지 않다 | RETRY | IMPLEMENT |
| 테스트 S/M/L いずれかが欠如또는 FAILED | RETRY | IMPLEMENT |
| 설계레벨의문제가 있り설계부터やり直す필요이 있다 | BACK_DESIGN | DETAIL_DESIGN |

### BACK_DESIGN의판단기준

이하의 경우는 BACK_DESIGN 를 선택:
- 구현中에 설계上의 모순이発見된
- 테스트케이스自体에 문제이 있다
- 아키텍처레벨의변경이필요

## レポート방법

1. `gh issue comment` 로 Issue 에 코멘트投稿(VERDICT판정)
2. **PASS판정시만**: 공통규칙에 따라 `gh issue edit` 로 Issue 本文를 업데이트
