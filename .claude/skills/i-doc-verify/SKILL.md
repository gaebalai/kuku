---
description: docs review의 지적이 적절하게 수정되었는지를 확인한다. 신규 지적은 수행하지 않는다.
name: i-doc-verify
---

# I Doc Verify

> **중요**: 이 스킬은 업데이트/수정을 수행한 세션과는 별도의 세션으로 실행하는 것을 추천합니다.

docs 수정 후의 확인을 수행한다.
**신규 지적은 수행하지 않고, 이전 레뷰의 지적이 해소되었는지만 확인한다.**

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| `i-doc-fix` 후의 확인 | ✅ 필수 |

**워크플로우 내 위치**: review-doc → fix-doc → **verify-doc** → pr

## 입력

### 하네스 경유(컨텍스트 변수)

| 변수 | 타입 | 설명 |
|------|-----|------|
| `issue_number` | int | GitHub Issue 번호 |
| `step_id` | str | 현재 스텝 ID |
| `cycle_count` | int | 현재 이터레이션 |
| `max_iterations` | int | 상한 횟수 |
| `previous_verdict` | str | 이전 스텝의 verdict |

### 수동실행(슬래시 커맨드)

```
$ARGUMENTS = <issue-number>
```

### 해결 규칙

컨텍스트 변수 `issue_number`가 존재하면 그쪽을 사용.
없으면 `$ARGUMENTS`의 제1인수를 `issue_number`로 하여 사용.

## 실행절차

1. 이전의 `i-doc-review` / `i-doc-fix` 코멘트를 확인
2. 지적 사항별로 OK / NG를 판정
3. 필요 최소한으로 근거가 되는 구현 / docs / workflow / CLAUDE.md를 재확인
4. 변경 파일로 좁힌 링크 체크 결과를 확인
5. 신규 발견 사항이 있어도 이번 판정에는 포함하지 않는다
6. 결과를 Issue에 코멘트

## Verdict 출력

```text
---VERDICT---
status: PASS
reason: |
  이전의 docs review 지적은 적절하게 수정되어 있다
evidence: |
  Must Fix 항목의 해소를 확인했다. 신규 지적은 판정에 포함하지 않았다
suggestion: |
---END_VERDICT---
```

### status의 선택 기준

| status | 조건 |
|--------|------|
| PASS | 이전 지적이 해소 |
| RETRY | 수정 부족 |
| ABORT | 계속이 위험 |
