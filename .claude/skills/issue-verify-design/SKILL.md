---
description: 설계 수정이 적절히 이루어졌는지를 확인한다. 신규 지적은 수행하지 않는다(리뷰 수렴을 위해).
name: issue-verify-design
---

# Issue Verify Design

> **중요**: 이 스킬은 설계/수정을 수행한 세션과는 **별도의 세션**에서 실행하는 것을 추천합니다.

설계 수정 후의 확인을 수행합니다.

**중요**: 이 커맨드는 「지적 사항이 적절히 수정되었는가」만을 확인합니다.
**신규 지적은 수행하지 않습니다**. 이는 리뷰 사이클의 수렴을 보장하기 위해서입니다.

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| `/issue-fix-design` 후의 수정 확인 | ✅ 필수 |
| 신규 리뷰가 필요한 경우 | ❌ `/issue-review-design`을 사용 |

**워크플로우 내의 위치**: design → review-design → (fix → **verify**) → implement

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
| `cycle_count` | int | 사이클 내 스텝만 | 현재의 이터레이션 번호 |
| `max_iterations` | int | 사이클 내 스텝만 | 사이클의 상한 횟수 |

### 수동실행(슬래시 커맨드)

```
$ARGUMENTS = <issue-number>
```

### 해결 룰

컨텍스트 변수 `issue_number`가 존재하면 그것을 사용.
없으면 `$ARGUMENTS`의 제1인수를 `issue_number`로 하여 사용.

## verify와 review의 차이

| 항목 | review | verify |
|------|--------|--------|
| 목적 | 전체 리뷰 | 수정 확인만 |
| 신규 지적 | 한다 | **하지 않는다** |
| 확인 범위 | 설계 전체 | 이전 지적 부분만 |
| 사용 타이밍 | 설계 완료 후 | fix 후 |

## 공통 룰

- [_shared/report-unrelated-issues.md](../_shared/report-unrelated-issues.md) — 작업 중에 발견한 무관계한 문제의 보고 룰

## 실행절차

### Step 1: 컨텍스트 취득

1. [_shared/worktree-resolve.md](../_shared/worktree-resolve.md)의 절차에 따라, Worktree의 절대 경로를 취득.

2. **이전의 지적 내용을 취득**:
   ```bash
   gh issue view [issue-number] --comments
   ```
   「설계 리뷰 결과」와 「설계 수정 보고」를 확인.

3. **현재의 설계서를 확인**:
   ```bash
   cat [worktree-absolute-path]/draft/design/issue-[number]-*.md
   ```

### Step 2: 수정 확인

#### 2.1 수정 항목의 확인

**확인할 것:**
- 이전의 「지적 사항 (Must Fix)」이 적절히 수정되어 있는가
- 1차 정보의 추가 기재를 요청받은 경우：「참조 정보(Primary Sources)」섹션이 추가되어 있는가

#### 2.2 반론(보류 항목)의 검토

「보류」또는 「논의」로 된 항목에 대해, 이하의 관점에서 **철저하게 검토**한다：

1. **반론의 논리적 타당성** — 근거가 명확한가?
2. **트레이드오프의 평가** — 지적을 수용한 경우의 비용/리스크는 타당한가?
3. **판정**:
   - **수용한다**: 반론에 납득할 수 있다 → 지적을 철회
   - **재반론한다**: 반론에 문제가 있다 → 이유를 명기하여 다시 수정을 요구한다
   - **일부 수용**: 부분적으로 납득 → 타협점을 제시

#### 2.3 신규 발견 사항의 기록(임의)

- **판정에는 포함하지 않는다**(verify의 수렴 보장을 위해)
- **보고는 수행한다**(정보 손실을 방지하기 위해)

### Step 3: 확인 결과의 코멘트

```bash
gh issue comment [issue-number] --body-file - <<'EOF'
# 설계 수정 확인 결과

## 수정 항목의 확인

| 지적 항목 | 상태 | 이유・근거 |
|----------|------|------------|
| (항목1) | ✅ OK | (수정 내용이 지적 의도를 충족하고 있다 등) |
| (항목2) | ❌ 재수정 필요 | (수정이 불충분한 구체적 이유) |

## 반론에의 검토 결과

| 보류 항목 | 검토 결과 | 이유 |
|------------|----------|------|
| (항목A) | ✅ 수용 | (논리적으로 타당) |
| (항목B) | ❌ 재수정을 요구 | (근거가 불충분) |
| (항목C) | ⚠️ 일부 수용 | (타협점) |

## 신규 발견 사항(참고 정보)

> **주의**: 이하는 이번 판정에는 영향하지 않습니다.

| 발견 사항 | 중요도 | 추천 대응 |
|----------|--------|----------|
| (문제의 개요) | 고/중/저 | 별도 Issue 기표 / 다음 페이즈로 대응 |

## 판정

[ ] Approve (구현 착수 가)
[ ] Changes Requested (재수정이 필요)

## 다음 스텝

(Approve의 경우)
`/issue-implement [issue-number]`로 구현을 시작해주세요.

(Changes Requested의 경우)
`/issue-fix-design [issue-number]`로 다시 수정해주세요.
EOF
```

### Step 4: 완료 보고

```
## 설계 수정 확인 완료

| 항목 | 값 |
|------|-----|
| Issue | #[issue-number] |
| 판정 | Approve / Changes Requested |

### 다음 스텝

- Approve: `/issue-implement [issue-number]`로 구현 시작
- Changes Requested: `/issue-fix-design [issue-number]`로 재수정
```

## Verdict 출력

실행 완료 후, 이하의 형식으로 verdict를 출력할 것:

---VERDICT---
status: PASS
reason: |
  수정 확인 완료
evidence: |
  전 수정 항목이 적절히 대응되어 있다
suggestion: |
---END_VERDICT---

### status의 선택 기준

| status | 조건 |
|--------|------|
| PASS | Approve |
| RETRY | 수정 불충분 |
| ABORT | 중대한 문제 |
