---
description: docs-only 변경을 레뷰하고, 사실정합성・구현정합성・운용정합성의 관점에서 판정한다.
name: i-doc-review
---

# I Doc Review

> **중요**: 이 스킬은 업데이트를 수행한 세션과는 별도의 세션으로 실행하는 것을 추천합니다.

> **CRITICAL**: 이 레뷰의 목적은 문장을 다듬는 것이 아니다. 현행 구현과의 차이, 오래된 절차, 오해를 유발하는 기술을 발견하는 것이다.

docs-only 변경을 레뷰한다. 신규 지적을 수행해도 좋다.

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| `i-doc-update` 완료 후 | ✅ 필수 |

**워크플로우 내 위치**: update-doc → **review-doc** → (fix-doc → verify-doc) → pr

## 입력

### 하네스 경유(컨텍스트 변수)

| 변수 | 타입 | 설명 |
|------|-----|------|
| `issue_number` | int | GitHub Issue 번호 |
| `step_id` | str | 현재 스텝 ID |
| `cycle_count` | int | 현재 이터레이션 |
| `max_iterations` | int | 사이클의 상한 횟수 |

### 수동실행(슬래시 커맨드)

```
$ARGUMENTS = <issue-number>
```

### 해결 규칙

컨텍스트 변수 `issue_number`가 존재하면 그쪽을 사용.
없으면 `$ARGUMENTS`의 제1인수를 `issue_number`로 하여 사용.

## 문서 품질의 원칙

- 단계적 공개의 방침을 취한다. 문서는 작게 유지한다. 커지면 구조화하여 분할한다
- 추가보다 삭제가 어렵다. 추가 시에 정말로 필요한지 판단한다. 불필요한 정보는 삭제, 슬림화를 검토한다
- 코드로부터 추론할 수 있는 정보는 작성하지 않는다. 구체적인 코드도 문서에 작성하지 않는다. 필요한 경우는 실제 코드로의 포인터를 기재한다

## 실행절차

### Step 1: 컨텍스트의 취득

1. [_shared/worktree-resolve.md](../_shared/worktree-resolve.md)의 절차에 따라, Worktree의 절대 경로를 취득
2. Issue 코멘트에서 직근의 docs-only 업데이트 보고를 확인
3. 설계서가 있으면 확인:
   ```bash
   cat [worktree-absolute-path]/draft/design/issue-[number]-*.md
   ```
4. 차분을 확인:
   ```bash
   cd [worktree-absolute-path] && git diff main...HEAD
   ```

### Step 2: 레뷰

이하의 관점에서 엄격하게 레뷰한다.

1. 현행 구현과 일치하고 있는가
2. CLI 커맨드 예가 현행 사양과 일치하는가
3. `CLAUDE.md`의 운용 방침과 모순되지 않는가
4. workflow / skill / docs 간에 기술이 모순되지 않는가
5. 링크 깨짐, 오래된 경로, 독자 동선의 파탄이 없는가

### Step 3: 변경 파일 한정 링크 체크

변경된 Markdown 파일로 좁혀서 이하를 실행한다.

```bash
cd [worktree-absolute-path] && python3 scripts/check_doc_links.py [changed-markdown-files...]
```

### Step 4: 결과를 Issue에 코멘트

Must Fix / Should Fix를 정리하여 Issue에 코멘트한다.

## Verdict 출력

```text
---VERDICT---
status: RETRY
reason: |
  docs의 정합성 레뷰에서 수정 사항이 발견되었다
evidence: |
  구현과의 차이, 운용 방침과의 불일치, 또는 독자를 오도하는 기술을 확인했다
suggestion: |
  Issue 코멘트의 지적에 따라 `i-doc-fix`로 수정할 것
---END_VERDICT---
```

### status의 선택 기준

| status | 조건 |
|--------|------|
| PASS | 수정 불필요로 PR로 진행 가능 |
| RETRY | docs 수정으로 해소 가능 |
| ABORT | docs-only의 범위를 초과하는 중대한 문제 |
