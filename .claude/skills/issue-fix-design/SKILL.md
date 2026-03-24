---
description: 설계 리뷰의 지적 사항에 기반하여, 설계문서를 수정 또는 논의한다.
name: issue-fix-design
---

# Issue Fix Design

설계 리뷰에서 지적된 내용에 대해, 논리적인 타당성을 검토한 후에, 설계문서를 업데이트합니다.

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| `/issue-review-design`에서 Changes Requested 후 | ✅ 필수 |
| 1차 정보의 기재를 요청받은 후 | ✅ 필수 |

**워크플로우 내의 위치**: design → review-design → (**fix** → verify) → implement

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
| `previous_verdict` | str | resume 지정 스텝만 | 이전 스텝의 verdict |
| `cycle_count` | int | 사이클 내 스텝만 | 현재의 이터레이션 번호 |
| `max_iterations` | int | 사이클 내 스텝만 | 사이클의 상한 횟수 |

### 수동실행(슬래시 커맨드)

```
$ARGUMENTS = <issue-number>
```

### 해결 룰

컨텍스트 변수 `issue_number`가 존재하면 그것을 사용.
없으면 `$ARGUMENTS`의 제1인수를 `issue_number`로 하여 사용.

## 전제 지식의 읽기

이하의 문서를 Read 도구로 읽어들인 후 작업을 시작할 것.

1. **개발 워크플로우**: `docs/dev/workflow_feature_development.md`
2. **테스트 규약**: `docs/dev/testing-convention.md`

## 공통 룰

- [_shared/report-unrelated-issues.md](../_shared/report-unrelated-issues.md) — 작업 중에 발견한 무관계한 문제의 보고 룰

## 실행절차

### Step 1: 컨텍스트 취득

1. [_shared/worktree-resolve.md](../_shared/worktree-resolve.md)의 절차에 따라, Worktree의 절대 경로를 취득.

2. **리뷰 결과의 취득**:
   1. 컨텍스트 변수 `previous_verdict`가 존재하는 경우는 그것을 확인(하네스 경유)
   2. 존재하지 않는 경우는 Issue 코멘트에서 최신의 리뷰 결과를 취득(수동실행 시)
   ```bash
   gh issue view [issue-number] --comments
   ```
   최신의 「설계 리뷰 결과」를 취득.

3. **설계서의 현상 확인**:
   ```bash
   cat [worktree-absolute-path]/draft/design/issue-[number]-*.md
   ```

### Step 2: 대응 방침의 검토

각 지적 사항에 대해 검토합니다.

#### 1차 정보의 추가 기재를 요청받은 경우

설계서에 「참조 정보(Primary Sources)」섹션을 추가：

```markdown
## 참조 정보(Primary Sources)

| 정보원 | URL/경로 | 근거(인용/요약) |
|--------|----------|-------------------|
| (공식 문서명) | (URL) | (설계 판정의 뒷받침이 되는 인용 또는 요약) |
```

#### 기타 지적 사항

- **A: 수정한다 (Agree)**
  - 지적에 의해 설계가 보다 명확하게 되거나, 모순이 해소되는 경우.

- **B: 반론한다/논의한다 (Discuss)**
  - 지적이 요건 정의에서 벗어나거나, 구현 비용이 과대하게 되는 경우.
  - 설계에는 「정답」이 없는 경우가 많기 때문에, **Rationale(근거)**을 명확히 하여 회답한다.

### Step 3: 설계서의 업데이트

지적을 수용하는 경우, 설계서를 수정합니다.

### Step 4: 커밋

```bash
cd [worktree-absolute-path] && git add draft/design/ && git commit -m "docs: update design for #[issue-number]"
```

### Step 5: 결과 보고

```bash
gh issue comment [issue-number] --body-file - <<'EOF'
# 설계 수정 보고

## 대응 완료

- **(지적 내용)**
  - 수정: (어떻게 설계를 변경했는가)

## 논의/보류

- **(지적 내용)**
  - 이유: (왜 그 설계를 유지하는가, 트레이드오프의 설명)

## 다음 스텝

`/issue-verify-design [issue-number]`로 수정 확인을 부탁합니다.
EOF
```

### Step 6: 완료 보고

```
## 설계 수정 완료

| 항목 | 값 |
|------|-----|
| Issue | #[issue-number] |
| 대응 완료 | N 건 |
| 보류 | M 건 |

### 다음 스텝

`/issue-verify-design [issue-number]`로 수정 확인을 실시해주세요.
```

## Verdict 출력

실행 완료 후, 이하의 형식으로 verdict를 출력할 것:

---VERDICT---
status: PASS
reason: |
  수정 완료
evidence: |
  전 지적 사항에 대응 완료
suggestion: |
---END_VERDICT---

### status의 선택 기준

| status | 조건 |
|--------|------|
| PASS | 수정 완료 |
| ABORT | 수정 불가능 |
