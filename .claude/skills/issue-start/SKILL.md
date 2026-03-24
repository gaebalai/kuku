---
description: 이슈 착수 시에 사용. worktree로 분리된 개발환경을 구축하고, Issue본문에 메타정보를 추가 기재한다
name: issue-start
---

# Issue Start

이슈대응을 시작하기 위한 worktree를 셋업하고, Issue본문에 메타정보를 추가 기재합니다.

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| 코드/문서변경을 수반하는 이슈 착수 | ✅ 필수 |
| 설계만(파일변경없음) | ⚠️ 임의 |
| 조사・리서치만 | ❌ 불필요 |

**중요**: PR을 생성할 때나 이슈대응으로 커밋이 필요한 경우, `git branch` 가 아니라 이 스킬을 사용해주세요.

## 인수

```
$ARGUMENTS = <issue-number> [prefix]
```

- `issue-number` (필수): Issue번호 (예: 42)
- `prefix` (임의): 브랜치 프리픽스 (기본값: feat)
  - 예: docs, fix, feat, refactor, test

## 명명 규칙

- **브랜치이름**: `[prefix]/[issue-number]` (예: `fix/42`)
- **디렉토리**: `../kuku-[prefix]-[issue-number]` (예: `../kuku-fix-42`)

## 실행절차

### Step 0: 인수의 해석

$ARGUMENTS 에서 issue-number 와 prefix 를 취득해주세요.
- prefix 가 지정되어 있지 않은 경우는 `feat` 를 기본값으로 한다

### Step 1: 브랜치와 Worktree의 생성

메인리포지토리의 루트에서 실행:

```bash
MAIN_REPO=$(git rev-parse --show-toplevel)
git worktree add -b [prefix]/[issue-number] "$MAIN_REPO/../kuku-[prefix]-[issue-number]" main
```

### Step 2: venv 심볼릭 링크생성

main 프로젝트의 `.venv` 에 대한 심볼릭 링크를 생성:

```bash
MAIN_REPO=$(git rev-parse --show-toplevel)
ln -s "$MAIN_REPO/.venv" "$MAIN_REPO/../kuku-[prefix]-[issue-number]/.venv"
```

이것으로 `ruff`, `mypy`, `pytest` 가 즉시 실행가능하게 됩니다.

### Step 3: Worktree의 확인

```bash
git worktree list
```

워크트리가 올바르게 생성되었는지 확인해주세요.

### Step 4: Issue본문에 메타정보를 추가 기재

Issue본문의 맨 앞에 Worktree정보를 추가 기재합니다:

```bash
# 현재의 Issue본문을 취득
CURRENT_BODY=$(gh issue view [issue-number] --json body -q '.body')

# 메타정보를 맨 앞에 추가한 새로운 본문을 생성
NEW_BODY=$(cat <<EOF
> [!NOTE]
> **Worktree**: \`../kuku-[prefix]-[issue-number]\`
> **Branch**: \`[prefix]/[issue-number]\`

$CURRENT_BODY
EOF
)

# Issue본문을 업데이트
gh issue edit [issue-number] --body "$NEW_BODY"
```

### Step 5: 셋업완료보고

이하의 형식으로 보고해주세요:

```
## Worktree 셋업완료

| 항목 | 값 |
|------|-----|
| Issue | #[issue-number] |
| 브랜치 | [prefix]/[issue-number] |
| 디렉토리 | ../kuku-[prefix]-[issue-number] |
| 기점브랜치 | main |
| .venv | 심볼릭 링크생성완료 |
| 메타정보 | Issue본문에 추가 기재완료 |

### 주의사항

⚠️ `.venv` 는 main 의 심볼릭 링크입니다:
- `pip install` 은 main 에 영향합니다
- pyproject.toml 을 변경하는 경우는 개별 venv 를 생성해주세요:
  ```bash
  rm .venv && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
  ```

### 다음스텝

이 태스크에 관한 앞으로의 명령은, 모두 이하의 디렉토리 내에서 실행해주세요:

../kuku-[prefix]-[issue-number]

### 클린업(작업완료 후)

작업이 완료되면 `/issue-close [issue-number]` 를 실행해주세요.
```

## Verdict 출력

실행완료 후, 이하의 형식으로 verdict 를 출력할 것:

---VERDICT---
status: PASS
reason: |
  Worktree 구축성공
evidence: |
  worktree 생성완료
suggestion: |
---END_VERDICT---

### status 의 선택기준

| status | 조건 |
|--------|------|
| PASS | Worktree 구축성공 |
| ABORT | 구축실패 |
