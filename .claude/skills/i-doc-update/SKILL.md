---
description: docs-only 업데이트를 수행한다. 코드나 테스트는 변경하지 않고, 현행 구현・CLI・운용 방침과의 정합을 확인하면서 docs를 수정한다.
name: i-doc-update
---

# I Doc Update

문서 수정 전용 스킬.
이 스킬의 목적은 **문서만을 업데이트하는 것**이다. 코드, 설정, 테스트는 변경하지 않는다.
다만, docs의 기술이 현행 구현이나 운용 방침과 모순되지 않는지는 엄격하게 확인한다.

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| docs-only Issue의 주 작업 | ✅ 필수 |
| 코드 변경을 수반하는 Issue | ❌ `issue-implement` / `issue-doc-check`를 사용 |

**워크플로우 내 위치**: start → **update-doc** → review-doc → (fix-doc → verify-doc) → pr → close

## 입력

### 하네스 경유(컨텍스트 변수)

| 변수 | 타입 | 설명 |
|------|-----|------|
| `issue_number` | int | GitHub Issue 번호 |
| `step_id` | str | 현재 스텝 ID |

### 수동실행(슬래시 커맨드)

```
$ARGUMENTS = <issue-number>
```

### 해결 규칙

컨텍스트 변수 `issue_number`가 존재하면 그쪽을 사용.
없으면 `$ARGUMENTS`의 제1인수를 `issue_number`로 하여 사용.

## 확인 대상

1. `docs/dev/workflow_feature_development.md`
2. `README.md`
3. 변경 대상 docs
4. 관련 구현, workflow, 설계서, 운용 문서

## 문서 품질의 원칙

- 단계적 공개의 방침을 취한다. 문서는 작게 유지한다. 커지면 구조화하여 분할한다
- 추가보다 삭제가 어렵다. 추가 시에 정말로 필요한지 판단한다. 불필요한 정보는 삭제, 슬림화를 검토한다
- 코드로부터 추론할 수 있는 정보는 작성하지 않는다. 구체적인 코드도 문서에 작성하지 않는다. 필요한 경우는 실제 코드로의 포인터를 기재한다

## 가드레일

- 코드, 설정, 테스트는 변경하지 않는다
- 사실 확인을 위한 read / search / 최소한의 커맨드 확인은 허가
- `python3 scripts/check_doc_links.py`에 의한 전체 확인은 허가
- docs만으로는 해결할 수 없는 불일치를 발견한 경우는 `ABORT`

## 실행절차

### Step 1: Worktree 정보의 취득

[_shared/worktree-resolve.md](../_shared/worktree-resolve.md)의 절차에 따라,
Worktree의 절대 경로를 취득할 것. 이후의 스텝에서는 이 경로를 사용한다.

### Step 2: 설계서와 Issue의 확인

1. Issue 본문과 코멘트를 확인
2. 설계서가 있으면 확인:
   ```bash
   cat [worktree-absolute-path]/draft/design/issue-[number]-*.md
   ```
3. 변경 대상 docs와 expected outcome을 정리

### Step 3: 정합성 감사

최소한, 이하를 확인한다.

- `docs/`의 기술이 현행 코드와 모순되지 않는가
- `CLAUDE.md`의 커맨드, 금지 사항, 운용 규칙과 모순되지 않는가
- `docs/dev/workflow_feature_development.md`와 workflow/skill 구성이 일치하고 있는가
- links, 참조 경로, 커맨드 예가 깨지지 않았는가

### Step 4: docs 업데이트

필요한 문서만을 업데이트한다.

### Step 5: 전체 링크 체크

초회에 이하를 실행하여, 기존 docs 전체의 상태를 확인한다.

```bash
cd [worktree-absolute-path] && python3 scripts/check_doc_links.py
```

- 이번 변경과 무관한 기존 에러는, 이 Issue에서 무리하게 해소하지 않는다
- 무관한 기존 에러는 별도 Issue를 생성하여 추적한다

### Step 6: 커밋

```bash
cd [worktree-absolute-path] && git add docs/ README.md workflows/ .claude/skills/ .agents/skills/ && git commit -m "docs: update documentation for #[issue-number]"
```

필요에 따라 변경 대상 경로를 좁혀도 좋다.

### Step 7: Issue 코멘트

무엇을 업데이트하고, 어떤 관점을 확인했는지를 Issue에 코멘트한다.

## Verdict 출력

```text
---VERDICT---
status: PASS
reason: |
  docs-only 업데이트를 완료했다
evidence: |
  대상 문서를 업데이트하고, 현행 구현・CLI・운용 방침과의 정합을 확인했다
suggestion: |
---END_VERDICT---
```

### status의 선택 기준

| status | 조건 |
|--------|------|
| PASS | docs 업데이트 완료 |
| ABORT | docs만으로는 안전하게 대처할 수 없다 |
