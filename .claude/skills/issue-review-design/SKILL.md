---
description: 설계문서에 대해, 범용적인 소프트웨어 설계 원칙에 기반하여 리뷰를 수행한다.
name: issue-review-design
---

# Issue Review Design

> **중요**: 이 스킬은 구현/설계를 수행한 세션과는 **별도의 세션**에서 실행하는 것을 추천합니다.
> 동일 세션으로 실행하면, 구현 시의 바이어스가 리뷰 판정에 영향하는 가능성이 있습니다.

구현 페이즈에 들어가기 전에, 설계문서의 품질을 검증합니다.

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| 설계완료 후, 구현시작 전 | ✅ 필수 |
| 사양 변경 시의 재리뷰 | ⚠️ 추천 |

**워크플로우 내의 위치**: design → **review-design** → (fix → verify) → implement

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

## 전제 지식의 읽기

이하의 문서를 Read 도구로 읽어들인 후 작업을 시작할 것.

1. **개발 워크플로우**: `docs/dev/workflow_feature_development.md`
2. **테스트 규약**: `docs/dev/testing-convention.md`

## 공통 룰

- [_shared/report-unrelated-issues.md](../_shared/report-unrelated-issues.md) — 작업 중에 발견한 무관계한 문제의 보고 룰

## 실행절차

### Step 1: Worktree 정보의 취득

[_shared/worktree-resolve.md](../_shared/worktree-resolve.md)의 절차에 따라,
Worktree의 절대 경로를 취득할 것. 이후의 스텝에서는 이 경로를 사용한다.

### Step 1.5: 설계서의 읽기와 1차 정보의 확인(Gate Check)

1. **설계서의 읽기**:
   ```bash
   cat [worktree-absolute-path]/draft/design/issue-[number]-*.md
   ```

2. **1차 정보의 기재를 확인**:

설계서에 이하가 명기되어 있는지 확인：

- [ ] **참조한 1차 정보의 일람**(공식 문서, RFC, API 사양서, 라이브러리의 소스코드 등)
- [ ] **각 1차 정보에의 URL/경로**(검증 가능한 형식)

#### 1차 정보가 없는 경우 → 조기 리턴

설계서에 1차 정보의 기재가 없거나, 불충분한 경우는, **리뷰 본체에 들어가지 않고** 이하의 코멘트를 투고하여 종료：

```bash
gh issue comment [issue-number] --body-file - <<'EOF'
# 설계 리뷰：1차 정보의 기재가 필요

## 지적 사항

설계서에 **1차 정보(Primary Sources)의 기재가 없습니다**.

설계 리뷰를 수행하려면, 이하를 설계서에 추가 기재해주세요：

### 필요한 정보

1. **참조한 1차 정보의 일람**
   - 공식 문서, RFC, API 사양서, 라이브러리의 소스코드 등
   - URL 또는 파일 경로를 명기

2. **1차 정보로부터 얻은 근거**
   - 설계 판정의 뒷받침이 되는 정보를 인용 또는 요약

### 예

\`\`\`markdown
## 참조 정보(Primary Sources)

| 정보원 | URL/경로 | 근거(인용/요약) |
|--------|----------|------------------------|
| Python 공식 문서 | https://docs.python.org/... | 「~를 사용하는 것으로...」(해당 부분의 인용) |
\`\`\`

## 판정

❌ **Changes Requested** - 1차 정보를 추가 기재 후, 다시 리뷰를 의뢰해주세요.

### 다음 스텝

`/issue-fix-design [issue-number]`로 1차 정보를 추가 기재
EOF
```

**이 시점에서 리뷰 종료. Step 2 이후는 실행하지 않는다.**

---

### Step 2: 설계 리뷰(1차 정보를 참조)

1차 정보가 기재되어 있는 경우만, 이 스텝으로 진행합니다.

**중요**: 리뷰 시에는 설계서의 기술뿐만 아니라, **1차 정보를 실제로 참조**하여 정합성을 확인해주세요.

#### 리뷰 기준

이하의 범용적인 원칙에 기반하여 리뷰해주세요.

1. **추상화와 책임의 분리 (Abstraction & Scope)**:
   - **What & Why**: 「무엇을 만드는가」와 「왜 만드는가」가 명확한가?
   - **No Implementation Details**: 특정 언어나 라이브러리의 내부 구현(How)에 과도하게 깊이 들어가고 있지 않은가? (의사 코드는 OK)
   - **Constraints**: 시스템의 제약조건(성능, 보안, 의존관계)이 명기되어 있는가?

2. **인터페이스 설계 (Interface Design)**:
   - **Usage Sample**: 이용자가 실제로 사용할 때의 코드 예가 포함되어 있는가?
   - **Idiomatic**: 그 인터페이스는, 대상 언어의 관습(Idioms)에 적합한가?
   - **Naming**: 직관적이고 의도가 전달되는 명명이 이루어져 있는가?

3. **신뢰성과 엣지 케이스 (Reliability)**:
   - **Source of Truth**: 1차 정보의 내용과 설계가 정합하고 있는가?
   - **Error Handling**: 정상계뿐만 아니라, 이상계(에러, 경계값)의 동작이 정의되어 있는가?
   - **1차 정보와의 괴리**: 1차 정보에 기재되어 있지만 설계에서 고려되지 않은 점은 없는가?

4. **검증 가능성 (Testability)**:
   - 테스트 케이스의 나열이 아니라, **「검증해야 할 관점」**이 언어화되어 있는가?
   - **S/M/L 망라성 체크(필수)**:
     - [ ] Small 테스트의 검증 대상이 정의되어 있는가
     - [ ] Medium 테스트의 검증 대상이 정의되어 있는가
     - [ ] Large 테스트의 검증 대상이 정의되어 있는가
     - [ ] 스킵하는 사이즈가 있는 경우, 이유는 타당한가(`docs/dev/testing-convention.md` 참조)

5. **영향 문서**:
   - 「영향 문서」섹션이 존재하며, 영향 범위가 적절히 평가되어 있는가?

### Step 3: 리뷰 결과의 코멘트

```bash
gh issue comment [issue-number] --body-file - <<'EOF'
# 설계 리뷰 결과

## 참조한 1차 정보

| 정보원 | 확인 결과 |
|--------|----------|
| [URL] | ✅ 설계와 정합 / ⚠️ 차이 있음 |

## 개요

(설계의 명확함과, 구현 착수의 가부 판정)

## 지적 사항 (Must Fix)

- [ ] **항목**: 지적 내용
  - (요건의 누락, 논리적인 모순, 불명확한 인터페이스 등)

## 개선 제안 (Should Fix)

- **항목**: 제안 내용

## 판정

[ ] Approve (구현 착수 가)
[ ] Changes Requested (설계 수정이 필요)
EOF
```

### Step 4: 완료 보고

```
## 설계 리뷰 완료

| 항목 | 값 |
|------|-----|
| Issue | #[issue-number] |
| 판정 | Approve / Changes Requested |

### 다음 스텝

- Approve: `/issue-implement [issue-number]`로 구현을 시작
- Changes Requested: `/issue-fix-design [issue-number]`로 수정
```

## Verdict 출력

실행 완료 후, 이하의 형식으로 verdict를 출력할 것:

---VERDICT---
status: PASS
reason: |
  설계는 구현 착수 가능
evidence: |
  전 리뷰 기준을 충족하고 있다
suggestion: |
---END_VERDICT---

### status의 선택 기준

| status | 조건 |
|--------|------|
| PASS | Approve |
| RETRY | Changes Requested |
| ABORT | 중대한 문제 |
