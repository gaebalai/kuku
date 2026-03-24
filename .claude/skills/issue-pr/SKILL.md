---
description: 커밋 정리・푸시・PR생성을 일괄실행
name: issue-pr
---

# Issue PR

workflow 의 전단스텝완료 후, PR을 생성합니다.
커밋이력을 정리하여 PR을 생성합니다.

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| workflow 의 pr 스텝에 도달한 경우 | ✅ |
| 전단스텝이 미완료 | ❌ 대기 |

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

- `/issue-start` 가 실행완료되어 있을 것
- `git absorb` 가 설치완료되어 있을 것(임의)

## 공통 규칙

- [_shared/report-unrelated-issues.md](../_shared/report-unrelated-issues.md) — 작업중에 발견한 무관계한 문제의 보고 규칙

## 실행절차

### Step 1: Worktree 정보의 취득

[_shared/worktree-resolve.md](../_shared/worktree-resolve.md) 의 절차에 따라,
Worktree 의 절대 경로를 취득할 것.

또한, Issue 본문에서 `> **Branch**: \`[prefix]/[number]\`` 를 추출하여 prefix 를 취득한다.

### Step 2: 미커밋 변경확인

```bash
cd [worktree-absolute-path] && git status
```

미커밋 변경이 있는 경우는 먼저 커밋해주세요.

### Step 3: 커밋이력의 정리

```bash
cd [worktree-absolute-path] && git absorb --and-rebase
```

fixup대상이 없는 경우는 아무 일도 일어나지 않습니다(정상).
`git absorb` 가 설치되어 있지 않은 경우는 스킵.

### Step 4: 푸시와 PR생성

```bash
cd [worktree-absolute-path] && git push -u origin HEAD
```

```bash
cd [worktree-absolute-path] && gh pr create --base main --title "[prefix]: タイトル (#[issue-number])" --body "$(cat <<'EOF'
## Summary

(Issue의 개요를 1-2문으로)

Closes #[issue-number]

## Changes

- (주요 변경점)

## Verification

- [ ] 필요한 확인이 완료되어 있다
EOF
)"
```

### Step 5: Issue본문에 PR번호를 추가 기재

PR생성 후, Issue본문의 메타정보에 PR번호를 추가:

```bash
CURRENT_BODY=$(gh issue view [issue-number] --json body -q '.body')
# **Branch** 행의 뒤에 **PR**: #[pr-number] 를 추가한 본문을 생성하여 업데이트
gh issue edit [issue-number] --body "..."
```

### Step 6: 완료보고

```
## PR생성완료

| 항목 | 값 |
|------|-----|
| Issue | #[issue-number] |
| PR | #[pr-number] |
| URL | [pr-url] |
| 커밋 정리 | git absorb 실행완료 / 스킵 |

### 다음스텝

PR의 머지준비가 되면 `/issue-close [issue-number]` 를 실행해주세요.
```

## Verdict 출력

실행완료 후, 이하의 형식으로 verdict 를 출력할 것:

---VERDICT---
status: PASS
reason: |
  PR 생성성공
evidence: |
  PR #XX 를 생성
suggestion: |
---END_VERDICT---

### status 의 선택기준

| status | 조건 |
|--------|------|
| PASS | PR 생성성공 |
| RETRY | push 실패등 |
| ABORT | 중대한 문제 |
