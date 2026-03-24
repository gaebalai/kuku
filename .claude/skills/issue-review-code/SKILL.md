---
description: 구현완료 후의 산출물에 대해, 설계정합성과 코드 품질의 관점에서 엄격한 리뷰를 실시한다
name: issue-review-code
---

# Issue Review Code

> **중요**: 이 스킬은 구현/설계를 수행한 세션과는 **별도의 세션**에서 실행하는 것을 추천합니다.
> 동일 세션으로 실행하면, 구현 시의 바이어스가 리뷰 판단에 영향할 가능성이 있습니다.

구현 코드에 대하여, 설계서를 기반으로 엄격한 코드 리뷰를 실시합니다.

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| `/issue-implement` 완료 후 | ✅ 필수 |
| 구현 도중 | ⚠️ 임의(중간 리뷰로서) |

**워크플로우 내의 위치**: implement → **review-code** → (fix → verify) → doc-check → pr → close

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

### Step 1: 컨텍스트의 취득

1. [_shared/worktree-resolve.md](../_shared/worktree-resolve.md)의 절차에 따라, Worktree의 절대 경로를 취득.

2. **설계 정보의 취득**:
   ```bash
   cat [worktree-absolute-path]/draft/design/issue-[number]-*.md
   ```

3. **구현 서머리의 취득**:
   ```bash
   gh issue view [issue-number] --comments
   ```
   최근의 「구현완료 보고」를 확인.

4. **구현 차분의 취득**:
   ```bash
   cd [worktree-absolute-path] && git diff main...HEAD
   ```

### Step 1.5: 독립 테스트 실행(필수)

리뷰어 자신이 독립된 환경에서 테스트를 실행하고, 결과를 확인한다.
구현자의 보고에만 의존하지 않고, 테스트 결과를 독자적으로 검증하는 것이 목적.

1. **Baseline Check 코멘트의 확인**:
   Issue 코멘트(Step 1.3에서 취득완료)에서 최신의 `## Baseline Check 결과`를 검색한다.

2. **Lint / Format / 타입 체크(exit 0 필수)**:
   ```bash
   cd [worktree-absolute-path] && source .venv/bin/activate && ruff check kuku_harness/ tests/ && ruff format --check kuku_harness/ tests/ && mypy kuku_harness/
   ```

3. **테스트 실행(개별)**:
   ```bash
   cd [worktree-absolute-path] && source .venv/bin/activate && pytest
   ```
   **`pytest`는 `&&` 체인에 포함하지 않고, 반드시 개별로 실행한다.** baseline failure가 남아있으면 exit 비 0이 되기 때문에, 체인에 포함하면 후속 판정에 도달할 수 없다.

4. **합부 판정**:
   - **Baseline Check 코멘트가 없는 경우**:
     - 전 커맨드가 exit 0이 아니면 **Changes Requested**(종래대로)
   - **Baseline Check 코멘트가 있는 경우**:
     - ruff check / ruff format / mypy: exit 0 필수(변경 없음)
     - pytest: FAILED/ERROR를 baseline 목록과 대조한다
       - 비교 키 `(nodeid, kind, error_type)`가 baseline과 완전 일치 → 제외
       - 불일치의 신규 FAILED/ERROR → **Changes Requested**
       - baseline failure만 남아 있는 경우 → 테스트 합부는 OK로 한다

5. 테스트 총수, passed/failed/errors/skipped를 기록해둔다

### Step 2: 코드 리뷰의 실시

1. **설계와의 정합성**:
   - 설계서의 요건을 완전히 충족하고 있는가?
   - 임의의 사양 변경이나, 미구현 기능은 없는가?

2. **안전성과 견고성**:
   - 에러 핸들링은 적절한가?(무시, 범용 Exception의 금지)
   - 경계값(Boundary Value)이나 Null 안전성의 고려가 있는가?

3. **코드 품질**:
   - 타입 힌트는 구체적인가? (`Any`의 남용 금지)
   - 명명은 적절하고 설명적인가?
   - CLAUDE.md의 코딩 규약에 준거하고 있는가?

4. **테스트**:
   - 추가된 기능에 대한 테스트는 충분한가?
   - 설계서의 「테스트 전략」과 구현 테스트가 대응하고 있는가?
   - **S/M/L 망라성 체크(필수)**:
     - [ ] Small 테스트가 구현・PASSED인가
     - [ ] Medium 테스트가 구현・PASSED인가
     - [ ] Large 테스트가 구현・PASSED인가
     - [ ] pytest 출력이 Issue 코멘트에 포함되어 있는가
   - 테스트 미구현의 경우: 설계 리뷰로 생략이 승인완료가 아닌 한 **Changes Requested**
   - pytest 출력이 없는 경우는 **Changes Requested**

### Step 3: 리뷰 결과의 코멘트 투고

```bash
gh issue comment [issue-number] --body "$(cat <<'EOF'
# 코드 리뷰결과

## 개요

(한마디로 말하면 어떠했는가)

## 지적 사항 (Must Fix)

- [ ] **파일명:행수**: 구체적인 지적 내용
- [ ] ...

## 개선 제안 (Should Fix)

- **파일명**: 보다 나은 구현 패턴의 제안

## 좋은 점

- (특기할 만한 좋은 구현이 있으면 기재)

## 판정

[ ] Approve (수정 없이 머지 가능)
[ ] Changes Requested (수정 필요)
EOF
)"
```

### Step 4: 완료 보고

```
## 코드 리뷰완료

| 항목 | 값 |
|------|-----|
| Issue | #[issue-number] |
| 판정 | Approve / Changes Requested |
| Must Fix | N 건 |
| Should Fix | M 건 |

### 다음스텝

- Approve: `/issue-doc-check [issue-number]`로 문서 체크
- Changes Requested: `/issue-fix-code [issue-number]`로 수정
```

## Verdict 출력

실행완료 후, 이하의 형식으로 verdict를 출력할 것:

---VERDICT---
status: PASS
reason: |
  코드 품질 기준을 충족하고 있다
evidence: |
  설계정합성・테스트 커버리지・품질 체크 모두 합격
suggestion: |
---END_VERDICT---

### status의 선택 기준

| status | 조건 |
|--------|------|
| PASS | Approve |
| RETRY | Changes Requested |
| BACK | 설계에 문제 |
| ABORT | 중대한 문제 |
