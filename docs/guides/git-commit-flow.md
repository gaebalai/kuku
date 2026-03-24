# Git 커밋 전략 가이드

git absorb + `--no-ff` 머지에 의한 커밋 이력 관리 전략.

## 개요

이 워크플로우는 이하를 양립한다:

- **의미 있는 커밋 단위**: 기능·수정별로 커밋
- **리뷰 지적의 자동 흡수**: `git absorb`로 과거 커밋에 자동 fixup
- **브랜치 시각화**: `--no-ff` 머지로 브랜치의 분기·합류가 명확

## 왜 이 전략인가

머지 전략에는 3가지 선택지가 있다. 각각에 트레이드오프가 있다:

| 전략 | 커밋 이력 | 리뷰 수정 | 문제점 |
|------|-------------|-------------|--------|
| squash merge | 1커밋으로 압축 | 흔적 없음 | **이력이 소실**. 무엇을 어떤 순서로 만들었는지 추적 불가 |
| 통상 merge | 전체 커밋 유지 | 수정 커밋이 남음 | **노이즈 증가**. `fix: review feedback`가 산란 |
| **git absorb + `--no-ff`** | 의미 있는 단위로 유지 | 원래 커밋에 흡수 | 도구 도입 필요 |

이 전략은 squash와 통상 merge의 중간을 취한다:

- **squash처럼 깔끔**: 리뷰 수정은 원래 커밋에 흡수되어 노이즈가 남지 않음
- **통상 merge처럼 상세**: 기능·수정별 커밋 단위가 유지됨
- **`--no-ff`로 브랜치 구조도 시각화**: 언제 분기하고 언제 합류했는지 명확

## 추천 도구

[git-absorb](https://github.com/tummychow/git-absorb) 설치를 추천한다 (미설치 시 `/issue-pr` 스킬에서는 absorb 스텝이 스킵된다):

```bash
# macOS
brew install git-absorb

# Ubuntu/Debian
apt install git-absorb

# Cargo (Rust)
cargo install git-absorb
```

## 워크플로우

### 1. 작업 중 (의미 있는 단위로 커밋)

```bash
git commit -m "feat: 사용자 인증 기능 추가"
git commit -m "feat: 로그아웃 기능 추가"
git commit -m "fix: 인증 토큰 유효기한 체크 수정"
```

기능·수정별로 의미 있는 커밋을 생성한다.

### 2. 리뷰 지적 대응 (git absorb로 자동 흡수)

> **⚠️ 커밋하지 않음**: 수정은 스테이지만. 커밋하면 `git absorb`로 흡수할 수 없게 된다.

```bash
# 리뷰 지적에 대응하여 파일 수정
vim src/auth.py

# 수정을 스테이지 (커밋하지 않음!)
git add src/auth.py

# 적절한 과거 커밋에 자동 흡수
git absorb --and-rebase
```

`git absorb`는 **스테이지된 변경만** 대상으로 한다. 실수로 커밋한 경우는 "[복구](#복구)"를 참조.

### 3. PR 생성

```bash
gh pr create --title "feat: 신기능" --body "..."
```

### 4. 머지 (브랜치 시각화 유지)

#### kuku에서의 운용 (PR 기반)

kuku에서는 PR을 생성하고, GitHub 상에서 merge commit을 사용하여 머지한다:

```bash
# PR 생성 (/issue-pr 스킬로 자동화)
gh pr create --title "feat: 신기능" --body "..."

# 머지 (/issue-close 스킬로 자동화)
gh pr merge --merge --delete-branch
```

`--merge` 옵션에 의해 merge commit이 생성되어, `--no-ff`와 동등한 브랜치 구조가 유지된다.

#### Git 일반론 (로컬 머지)

PR을 사용하지 않는 프로젝트에서는 로컬에서 `--no-ff` 머지를 수행한다:

```bash
git switch main
git merge --no-ff feature-branch
git push
```

**중요**: `--no-ff`를 반드시 사용한다.

## 왜 `--no-ff`인가

### Fast-forward 머지 (기본값)

```
main:    A---B---C---D---E  (feature commits absorbed)
```

브랜치의 존재가 이력에서 사라진다.

### No-fast-forward 머지

```
main:    A---B-----------M
              \         /
feature:       C---D---E
```

브랜치의 분기·합류가 `git log --graph`로 확인 가능.

## 커밋 메시지 규약

[Conventional Commits](https://www.conventionalcommits.org/)를 따른다:

| Prefix | 용도 |
|--------|------|
| feat | 신기능 |
| fix | 버그 수정 |
| docs | 문서 |
| test | 테스트 |
| refactor | 리팩터링 |
| chore | 기타 (빌드, CI 등) |

예:
```
feat: 사용자 인증 기능 추가
fix: 로그인 시 에러 핸들링 수정
docs: README에 설치 절차 추가
```

## 금지 사항

- `git merge`의 기본값 (fast-forward) 사용
- squash 머지 (이력이 소실됨)
- main 브랜치에 직접 커밋

## git absorb의 동작 원리

1. 스테이지된 변경을 분석
2. 각 변경이 어떤 과거 커밋에 속하는지 판정
3. 자동으로 `fixup!` 커밋을 생성
4. `--and-rebase` 옵션으로 자동 리베이스

### 예

```bash
# 3개의 커밋이 있는 상태
# commit A: file1.py에 함수 추가
# commit B: file2.py에 함수 추가
# commit C: file3.py에 함수 추가

# file1.py와 file2.py를 수정
vim file1.py file2.py
git add .
git absorb --and-rebase

# 결과: 수정이 각각 commit A, B에 흡수됨
```

## 복구

### 실수로 커밋한 경우

리뷰 수정을 별도 커밋으로 만들어 버린 경우의 대처법.

#### 방법 1: 커밋을 취소하고 다시 하기 (추천)

```bash
# 직전 커밋을 취소하고 변경을 스테이지 상태로 되돌림
git reset --soft HEAD~1

# git absorb로 흡수
git absorb --and-rebase
```

#### 방법 2: rebase로 통합

이미 푸시 완료, 또는 여러 커밋을 정리하는 경우.

```bash
# 먼저 대상 커밋의 위치를 확인
git log --oneline main..HEAD

# 인터랙티브 rebase로 통합
# ⚠️ '2s/pick/fixup/'의 행번호는 대상 커밋의 위치에 맞출 것
GIT_SEQUENCE_EDITOR="sed -i '2s/pick/fixup/'" git rebase -i main

# force push (푸시 완료인 경우)
# ⚠️ 단독 작업 브랜치에서만 사용. 공동 작업 중에는 리뷰어에게 통지할 것
git push --force-with-lease
```

## 참고 자료

- [git-absorb GitHub](https://github.com/tummychow/git-absorb)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub CLI `gh pr merge`](https://cli.github.com/manual/gh_pr_merge)
