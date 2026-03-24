---
description: docs review의 지적에 대응하고, 문서만을 수정한다. 코드나 테스트는 변경하지 않는다.
name: i-doc-fix
---

# I Doc Fix

docs review의 지적 사항에 대응한다. 이 스킬에서도 **코드, 설정, 테스트는 변경하지 않는다**.

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| `i-doc-review` 또는 `i-doc-verify`가 RETRY일 때 | ✅ 필수 |

**워크플로우 내 위치**: update-doc → review-doc → **fix-doc** → verify-doc

## 입력

### 하네스 경유(컨텍스트 변수)

| 변수 | 타입 | 설명 |
|------|-----|------|
| `issue_number` | int | GitHub Issue 번호 |
| `step_id` | str | 현재 스텝 ID |
| `previous_verdict` | str | 이전 스텝의 verdict |

### 수동실행(슬래시 커맨드)

```
$ARGUMENTS = <issue-number>
```

### 해결 규칙

컨텍스트 변수 `issue_number`가 존재하면 그쪽을 사용.
없으면 `$ARGUMENTS`의 제1인수를 `issue_number`로 하여 사용.

## 실행절차

1. `previous_verdict` 또는 Issue 코멘트에서 최신 레뷰 결과를 취득
2. Must Fix를 1건씩 검토
3. docs만 수정
4. 구현 / CLI / CLAUDE.md / 관련 docs와의 정합을 재확인
5. 수정 대상 파일로 좁혀서 이하를 실행:
   ```bash
   cd [worktree-absolute-path] && python3 scripts/check_doc_links.py [changed-markdown-files...]
   ```
6. docs만 커밋
7. 대응 내용을 Issue에 코멘트

## Verdict 출력

```text
---VERDICT---
status: PASS
reason: |
  docs review의 지적에 대응했다
evidence: |
  Must Fix 항목을 수정하고, 관련 docs와 구현의 정합을 재확인했다
suggestion: |
---END_VERDICT---
```

### status의 선택 기준

| status | 조건 |
|--------|------|
| PASS | 수정 완료 |
| ABORT | docs 수정만으로는 해결 불가 |
