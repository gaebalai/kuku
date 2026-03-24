---
description: 이슈 완료 시에 사용. 설계서 아카이브・PR머지・worktree삭제・브랜치삭제를 일괄실행
name: issue-close
---

# Issue Close

이슈대응완료 후의 클린업을 실행합니다.
설계서가 있는 경우는 Issue 본문에 아카이브한 후 worktree 를 삭제합니다.

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| PR이 Approve되어 머지가능 | ✅ 사용 |
| PR리뷰 대기 | ❌ 대기 |
| 작업중 | ❌ 불필요 |

**워크플로우 내의 위치**: implement → review-code → doc-check → pr → **close**

## 입력

### 하네스경유(컨텍스트변수)

**항상 주입되는 변수:**

| 변수 | 타입 | 설명 |
|------|-----|------|
| `issue_number` | int | GitHub Issue 번호 |
| `step_id` | str | 현재 스텝 ID |

### 수동실행(슬래시 명령)

```
$ARGUMENTS = <issue-number>
```

### 해결 규칙

컨텍스트변수 `issue_number` 가 존재하면 그쪽을 사용.
없으면 `$ARGUMENTS` 의 제1인수를 `issue_number` 로 하여 사용.

## 전제 조건

- `/issue-pr` 로 PR이 생성완료되어 있을 것
- Merge commit방식을 사용(브랜치이력을 유지)

## 실행절차

### Step 1: Worktree정보의 취득

Issue본문에서 Worktree정보를 취득합니다:

```bash
gh issue view [issue-number] --json body -q '.body'
```

이하의 정보를 추출:
- `> **Worktree**: \`../kuku-[prefix]-[number]\`` → worktree 경로
- `> **Branch**: \`[prefix]/[number]\`` → 브랜치이름

### Step 2: 메인리포지토리의 경로를 특정

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
```

> **주의**: `git rev-parse --show-toplevel` 은 현재의 worktree 의 루트를 반환하기 때문에,
> worktree 내에서 실행하면 main repo 를 취득할 수 없다. 반드시 `git worktree list` 를 사용할 것.

worktree 내에 있는 경우는 main repo 로 이동:

```bash
cd "$MAIN_REPO"
```

### Step 3: 설계서의 Issue 본문 아카이브

worktree 삭제 전에, 설계서를 Issue 본문에 저장합니다.

1. **`draft/design/` 의 존재확인**:
   ```bash
   WORKTREE_PATH=$(realpath "$MAIN_REPO/../kuku-[prefix]-[number]")
   ls "$WORKTREE_PATH/draft/design/" 2>/dev/null
   ```

2. **설계서가 있는 경우**:
   - Issue 본문에 `## 설계서` 섹션이 **이미 존재하는지** 확인(멱등성 보장):
     ```bash
     gh issue view [issue-number] --json body -q '.body' | grep -q '^## 설계서'
     ```
   - 기존인 경우는 스킵
   - 미존재인 경우만, 설계서의 내용을 읽어들여 Issue 본문에 `<details>` 태그로 추가 기재:

   ```bash
   CURRENT_BODY=$(gh issue view [issue-number] --json body -q '.body')
   DESIGN_CONTENT=$(cat "$WORKTREE_PATH"/draft/design/issue-[number]-*.md)

   gh issue edit [issue-number] --body "$(cat <<BODY_EOF
   $CURRENT_BODY

   ---

   ## 설계서

   <details>
   <summary>클릭하여 전개</summary>

   $DESIGN_CONTENT

   </details>
   BODY_EOF
   )"
   ```

3. **추가 기재 실패 시의 폴백**:
   본문사이즈 상한초과 등으로 추가 기재에 실패한 경우는, Issue **코멘트** 에 설계서 전문을 투고하고, 본문에는 `## 설계서` 섹션과 코멘트로의 링크만 추가 기재한다.

4. **설계서가 없는 경우**: 이 스텝을 스킵

### Step 4: PR의 머지

```bash
gh pr merge [branch-name] --merge --delete-branch
```

머지커밋을 생성하여 브랜치이력을 유지한다.

### Step 5: .venv 심볼릭 링크삭제

worktree 삭제 전에 `.venv` 심볼릭 링크를 삭제(untracked files 에러회피):

```bash
rm "$WORKTREE_PATH/.venv"
```

### Step 6: worktree삭제

```bash
git worktree remove "$WORKTREE_PATH"
```

### Step 7: main을 최신화

```bash
git pull origin main
```

### Step 8: 완료보고

```
## Issue 클로즈완료

| 항목 | 상태 |
|------|------|
| Issue | #[issue-number] |
| 설계서 | Issue본문에 아카이브완료 / 없음 |
| PR | 머지완료 |
| .venv symlink | 삭제완료 |
| worktree | 삭제완료 |
| 리모트브랜치 | 삭제완료 (--delete-branch) |
| main | 최신화완료 |
```

## Verdict 출력

실행완료 후, 이하의 형식으로 verdict 를 출력할 것:

---VERDICT---
status: PASS
reason: |
  클로즈완료
evidence: |
  PR 머지・worktree 삭제・main 최신화완료
suggestion: |
---END_VERDICT---

### status 의 선택기준

| status | 조건 |
|--------|------|
| PASS | 클로즈완료 |
| RETRY | 머지실패등 |
| ABORT | 중대한 문제 |
