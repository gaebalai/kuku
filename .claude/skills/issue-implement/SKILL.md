---
description: 설계서(draft/design/)에 기반하여, TDD(테스트 주도 개발) 접근법을 사용하여 기능을 구현한다.
name: issue-implement
---

# Issue Implement

승인된 설계서를 바탕으로, 테스트 코드의 생성부터 구현을 시작합니다.
**Test-Driven Development (TDD)**의 원칙에 따라, 「테스트 생성 (Red) → 구현 (Green) → 리팩터링」의 사이클을 반복합니다.

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| 설계 리뷰 완료・승인 후 | ✅ 필수 |
| 설계 리뷰 미완료 | ❌ 대기 |

**워크플로우 내의 위치**: design → review-design → **implement** → review-code → doc-check → pr → close

## 입력

### 하네스 경유(컨텍스트 변수)

**항상 주입되는 변수:**

| 변수 | 타입 | 설명 |
|------|-----|------|
| `issue_number` | int | GitHub Issue 번호 |
| `step_id` | str | 현재의 스텝 ID |

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

## 전제 조건

- `/issue-start`가 실행완료일 것
- `/issue-design`으로 설계서가 생성완료일 것
- 설계 리뷰가 완료・승인되어 있을 것

## 공통 규칙

- [_shared/report-unrelated-issues.md](../_shared/report-unrelated-issues.md) — 작업 중에 발견한 무관한 문제의 보고 규칙

## 실행절차

### Step 1: Worktree 정보의 취득

[_shared/worktree-resolve.md](../_shared/worktree-resolve.md)의 절차에 따라,
Worktree의 절대 경로를 취득할 것. 이후의 스텝에서는 이 경로를 사용한다.

### Step 2: 설계서의 읽기

```bash
cat [worktree-absolute-path]/draft/design/issue-[number]-*.md
```

**특히 주목할 섹션**:
- 「인터페이스」: 구현해야 할 API
- 「테스트 전략」: 테스트 케이스의 기반이 된다
- 「영향 문서」: 구현 후에 업데이트가 필요한 문서

### Step 2.5: Baseline Check

구현 시작 전에 테스트 환경의 상태를 확인하고, 변경 전부터 존재하는 실패(baseline failure)를 기록한다.

1. **pytest를 실행한다**:
   ```bash
   cd [worktree-absolute-path] && source .venv/bin/activate && pytest
   ```

2. **전 패스의 경우**: baseline은 clean. 코멘트 불필요. Step 3으로 진행.

3. **FAILED / ERROR가 있는 경우**:
   a. 각 실패 테스트의 `(nodeid, kind, error_type)`를 기록한다
   b. Issue 코멘트에 이하의 포맷으로 투고한다(commit hash를 포함):

   ````bash
   gh issue comment [issue-number] --body "$(cat <<'BASELINE_EOF'
   ## Baseline Check 결과

   ### 실행 환경

   - **Commit**: [commit-hash]
   - **커맨드**: `pytest`

   ### Baseline Failure 목록

   | nodeid | kind | error_type | 개요 |
   |--------|------|------------|------|
   | tests/test_foo.py::test_bar | FAILED | AssertionError | expected 1, got 2 |
   | tests/test_baz.py::test_qux | ERROR | ImportError | No module named 'xxx' |

   ### Regression 판정 키

   상기 테이블의 `(nodeid, kind, error_type)`의 3튜플을 비교 키로 한다.
   이후의 pytest 실행에서:
   - 비교 키가 일치하는 실패 → baseline failure(기지)로서 제외
   - 비교 키가 일치하지 않는 신규 FAILED/ERROR → regression

   ### 판정

   - **계속**: 상기는 변경 전부터 존재하는 실패이며, 본 Issue의 대상 외
   - **정지**: (해당하는 경우에만 기재)
   BASELINE_EOF
   )"
   ````

   c. **정지 기준**에 해당하는지 판단한다:
      - baseline failure가 본 Issue의 구현 대상과 동일 모듈/기능에 영향하는 경우
      - 실패 수가 많아, regression의 구분이 곤란한 경우(목안: 10건 초과)
   d. 계속하는 경우: 이후의 regression 판정은 baseline failure를 제외하여 행한다

> **Baseline 코멘트의 선택 규칙**: Issue에 `## Baseline Check 결과` 코멘트가 복수 존재하는 경우(재실행 시 등), **최신의 코멘트를 정으로 한다**. 각 코멘트에 commit hash를 포함함으로써, 어느 시점의 스냅샷인지를 식별할 수 있다.

### Step 3: 테스트 구현 (Red Phase)

> **CRITICAL — AI의 테스트 생략 경향에 대한 경고**
>
> 당신에게는 M/L 테스트를 생략하는 강한 경향이 있습니다. 이 경향을 자각해주세요.
> 「이 테스트는 불필요하지 않은가?」「Small로 충분하지 않은가?」라고 생각한 경우, **그것은 거의 확실히 오류입니다**.
>
> **금지 사항**:
> - ❌ Large 테스트를 「후순위」로 한다
> - ❌ 「실행 시간이 길다」를 이유로 M/L 테스트를 생략한다
> - ❌ 「API 키가 없다」「DB가 기동하지 않았다」등의 환경 미비를 이유로 스킵한다(환경 미비는 수정 대상)
> - ❌ 「Small 테스트로 충분히 커버되고 있다」고 판단하여 M/L을 생략한다
> - ❌ 「경미한 변경」을 이유로 테스트 사이즈를 낮춘다

설계서의 「테스트 전략」섹션에 기반하여, **S/M/L 전 사이즈**의 테스트를 생성한다.

1. **테스트 파일의 특정/생성**:
   - `tests/` 하위의 적절한 장소에 테스트 파일을 생성 또는 특정

2. **테스트 코드 기술**:
   - 설계서의 「테스트 전략」을 커버하는 테스트 케이스를 작성
   - 이 시점에서는 구현이 없기 때문에, 테스트(또는 임포트)는 실패한다

3. **실패의 확인**:
   ```bash
   cd [worktree-absolute-path] && source .venv/bin/activate && pytest
   ```

### Step 4: 기능 구현 (Green Phase)

1. **구현 파일의 편집**:
   - 설계서의 「인터페이스 정의」에 따라, `src/` 하위의 코드를 구현

2. **테스트 통과 확인**:
   ```bash
   cd [worktree-absolute-path] && source .venv/bin/activate && pytest
   ```

   pytest의 합부 판정 기준:
   - **Baseline Check 코멘트가 없는 경우**: 전 테스트 PASSED를 기대(종래대로)
   - **Baseline Check 코멘트가 있는 경우**:
     1. FAILED/ERROR의 테스트를 baseline failure 목록과 대조한다
     2. 비교 키 `(nodeid, kind, error_type)`가 baseline과 일치 → 기지(제외)
     3. 비교 키가 불일치의 신규 FAILED/ERROR → regression(수정이 필요)
     4. baseline에 있었지만 사라진 경우(PASSED로 변경) → 문제없음

### Step 5: 리팩터링

- 코드의 가독성을 높이는 수정을 행한다
- 테스트가 계속해서 패스하는 것을 확인

### Step 6: 문서 업데이트

설계서의 「영향 문서」섹션에서 「있음」의 문서를 업데이트한다.

### Step 7: 품질 체크(커밋 전 필수)

이하의 2단계로 실행할 것. **모든 기준을 클리어할 때까지 커밋해서는 안 된다**.

#### 7a. Lint / Format / 타입 체크(exit 0 필수)

```bash
cd [worktree-absolute-path] && source .venv/bin/activate && ruff check kuku_harness/ tests/ && ruff format kuku_harness/ tests/ && mypy kuku_harness/
```

ruff / mypy는 전 패스 필수. baseline failure의 개념을 적용하지 않는다.

#### 7b. 테스트 실행

```bash
cd [worktree-absolute-path] && source .venv/bin/activate && pytest
```

**`pytest`는 `&&` 체인에 포함하지 않고, 반드시 개별로 실행한다.** baseline failure가 남아있으면 exit 비 0이 되지만, 이하의 기준으로 합부를 판정한다:

- **Baseline Check 코멘트가 없는 경우**: 전 테스트 PASSED 필수(exit 0이 아니면 NG)
- **Baseline Check 코멘트가 있는 경우**: Step 4와 동일한 regression 판정 기준을 적용한다
  - FAILED/ERROR를 baseline 목록과 대조하여, 비교 키 `(nodeid, kind, error_type)`가 전 일치 → OK(커밋 가능)
  - 비교 키가 불일치의 신규 FAILED/ERROR가 1건이라도 있다 → NG(수정이 필요)

실패한 경우는 원인을 수정하여 재실행할 것.

### Step 8: 커밋

```bash
cd [worktree-absolute-path] && git add . && git commit -m "feat: implement [feature] for #[issue-number]"
```

### Step 9: Issue에 코멘트

구현완료를 Issue에 코멘트합니다. pytest 및 품질 체크의 출력을 그대로 포함할 것.

````bash
gh issue comment [issue-number] --body "$(cat <<'COMMENT_EOF'
## 구현완료 보고 (TDD)

설계에 기반하여, TDD로 구현을 수행했습니다.

### 실시 내용

- **테스트**: `tests/test_xxx.py`에 XX건의 케이스를 추가 (Red → Green)
- **구현**: `src/xxx.py`에 기능을 구현

### 테스트 결과

```
(pytest의 표준 출력을 그대로 붙여넣기)
```

| 항목 | 결과 |
|------|------|
| 테스트 총수 | XX |
| passed | XX |
| failed | XX (이 중 baseline: YY, regression: 0) |
| errors | XX (이 중 baseline: YY, regression: 0) |
| skipped | XX |

### 품질 체크 결과

```
(ruff check + ruff format + mypy의 출력을 그대로 붙여넣기)
```

### 변경 파일

- `src/xxx.py`: (변경 내용)
- `tests/test_xxx.py`: (변경 내용)

### 다음스텝

`/issue-review-code [issue-number]`에 의한 코드 리뷰를 부탁드립니다.
COMMENT_EOF
)"
````

### Step 10: 완료 보고

```
## 구현완료

| 항목 | 값 |
|------|-----|
| Issue | #[issue-number] |
| 테스트 | XX 건 추가 |
| 품질 체크 | 모두 패스 |

### 다음스텝

`/issue-review-code [issue-number]`로 코드 리뷰를 실시해주세요.
```

## Verdict 출력

실행완료 후, 이하의 형식으로 verdict를 출력할 것:

---VERDICT---
status: PASS
reason: |
  구현・테스트・품질 체크 전 패스
evidence: |
  pytest 전 테스트 패스, ruff/mypy 에러 없음
suggestion: |
---END_VERDICT---

### status의 선택 기준

| status | 조건 |
|--------|------|
| PASS | 구현・테스트・품질 체크 전 패스 |
| RETRY | 테스트 실패 등 |
| BACK | 설계에 문제 |
| ABORT | 중대한 문제 |
