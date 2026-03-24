# Worktree 경로 해결(공통 절차)

## 절차

1. **Issue 본문에서 Worktree 정보를 취득**:
   ```bash
   gh issue view [issue-number] --json body -q '.body'
   ```

2. **Worktree 의 상대 경로를 추출**:
   - `> **Worktree**: \`../kuku-[prefix]-[number]\`` 의 형식

3. **절대 경로에 변환**:
   ```bash
   MAIN_REPO=$(git rev-parse --show-toplevel)
   WORKTREE_PATH=$(realpath "$MAIN_REPO/../kuku-[prefix]-[number]")
   ```

4. **존재 확인**:
   - 존재하지 않는 경우는 `/issue-start [issue-number]` 를 안내하여 종료

## 주의 사항

- Claude Code 에서는 Bash 의 cwd 는 매번 리셋된다
- Bash 커맨드는 매번 `cd [absolute-path] && command` 로 실행
- Read/Edit/Write 도구에서는 절대 경로를 사용
