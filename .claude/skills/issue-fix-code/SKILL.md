---
description: 리뷰 지적 사항에 대해, 기술적 타당성을 검토한 후 수정 대응(또는 반론)을 행한다
name: issue-fix-code
---

# Issue Fix Code

구현에 대한 리뷰 지적 사항에 기반하여, 수정 대응을 행합니다.
지적을 맹목적으로 받아들이는 것이 아니라, 기술적인 타당성을 검토하고, 필요한 수정과 반론을 구분하여 사용합니다.

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| `/issue-review-code`에서 Changes Requested 후 | ✅ 필수 |
| 사람의 리뷰 코멘트에 대한 대응 | ✅ 사용 가능 |

**워크플로우 내의 위치**: implement → review-code → (**fix** → verify) → doc-check → pr → close

## 입력

### 하네스 경유(컨텍스트 변수)

**항상 주입되는 변수:**

| 변수 | 타입 | 설명 |
|------|-----|------|
| `issue_number` | int | GitHub Issue 번호 |
| `step_id` | str | 현재의 스텝 ID |

**조건부로 주입되는 변수:**

| 변수 | 타입 | 조건 | 설명 |
|------|-----|------|------|
| `previous_verdict` | str | resume 지정 스텝만 | 전 스텝의 verdict |
| `cycle_count` | int | 사이클 내 스텝만 | 현재의 이터레이션 번호 |
| `max_iterations` | int | 사이클 내 스텝만 | 사이클의 상한 횟수 |

### 수동 실행(슬래시 커맨드)

```
$ARGUMENTS = <issue-number>
```

### 해결 규칙

컨텍스트 변수 `issue_number`가 존재하면 그쪽을 사용.
없으면 `$ARGUMENTS`의 제1인수를 `issue_number`로서 사용.

## 전제 지식의 읽기

이하의 문서를 Read 도구로 읽어들인 후 작업을 시작할 것.

1. **개발 워크플로우**: `docs/dev/workflow_feature_development.md`
2. **테스트 규약**: `docs/dev/testing-convention.md`

## 공통 규칙

- [_shared/report-unrelated-issues.md](../_shared/report-unrelated-issues.md) — 작업 중에 발견한 무관한 문제의 보고 규칙

## 실행절차

### Step 1: 컨텍스트 취득

1. [_shared/worktree-resolve.md](../_shared/worktree-resolve.md)의 절차에 따라, Worktree의 절대 경로를 취득.

2. **리뷰 결과의 취득**:
   1. 컨텍스트 변수 `previous_verdict`가 존재하는 경우 그것을 확인(하네스 경유)
   2. 존재하지 않는 경우 Issue 코멘트에서 최신의 리뷰 결과를 취득(수동 실행 시)

3. **리뷰 내용의 취득**:
   ```bash
   gh issue view [issue-number] --comments
   ```
   최신의 「코드 리뷰결과」를 취득.

4. **현상 파악**:
   지적된 해당 코드 주변을 확인.

### Step 2: 대응 방침의 검토

각 지적 사항에 대해, 이하의 기준으로 **하나씩** 검토해주세요.

- **A: 대응한다 (Agree)**
  - 지적이 올바르고, 수정에 의해 품질・안전성이 향상되는 경우.
  - 개선 제안 (Should Fix)의 경우: 장점이 명확하면 적극적으로 채용

- **B: 대응하지 않는다/반론한다 (Disagree/Discuss)**
  - 지적이 오해에 기반하고 있는 경우
  - 수정에 의한 부작용이나 비용이 장점을 상회하는 경우
  - CLAUDE.md의 방침이나 기존의 설계 사상과 모순되는 경우
  - **필수**: 반론하는 경우는, 명확한 논리적 근거를 준비

### Step 3: 수정의 실행

1. **코드 수정**: 채용한 지적 사항에 기반하여 코드를 수정

2. **품질 체크(커밋 전 필수)**:

   이하를 실행하고, **모두 패스할 때까지 커밋해서는 안 된다**. 실패한 경우는 원인을 수정하여 재실행할 것.

   CLAUDE.md의 「Pre-Commit (REQUIRED)」섹션에 기재된 커맨드를 실행할 것.

### Step 4: 커밋

```bash
cd [worktree-absolute-path] && git add . && git commit -m "fix: address review feedback for #[issue-number]"
```

### Step 5: 결과 보고

```bash
gh issue comment [issue-number] --body "$(cat <<'EOF'
# 리뷰 지적에 대한 대응 보고

리뷰 감사합니다. 이하와 같이 검토・대응을 수행했습니다.

## 대응완료

- **(지적 내용의 요약)**
  - 수정 내용: (어떻게 수정했는가, 파일명 등)

## 보류・반론

- **(지적 내용의 요약)**
  - 이유: (왜 대응하지 않았는가. 근거가 되는 로직)

## 다음스텝

`/issue-verify-code [issue-number]`로 수정 확인을 부탁드립니다.
EOF
)"
```

### Step 6: 완료 보고

```
## 코드 수정완료

| 항목 | 값 |
|------|-----|
| Issue | #[issue-number] |
| 대응완료 | N 건 |
| 보류 | M 건 |

### 다음스텝

`/issue-verify-code [issue-number]`로 수정 확인을 실시해주세요.
```

## Verdict 출력

실행완료 후, 이하의 형식으로 verdict를 출력할 것:

---VERDICT---
status: PASS
reason: |
  수정완료
evidence: |
  전 지적 사항에 대응완료
suggestion: |
---END_VERDICT---

### status의 선택 기준

| status | 조건 |
|--------|------|
| PASS | 수정완료 |
| ABORT | 수정 불가능 |
