# Git Worktree 가이드

Bare Repository + Worktree 패턴에 의한 병렬 개발 환경 구축·운용 가이드.

> **본 문서의 구성**: 전반은 범용적인 Bare Repository 패턴, 후반 ("[kuku 프로젝트에서의 운용](#kuku-프로젝트에서의-운용)")은 kuku 고유의 일반 리포지토리 + worktree 패턴을 기재.

## 개요

Git Worktree를 사용하면 하나의 리포지토리에서 여러 브랜치를 동시에 작업 디렉토리로 전개할 수 있다. 이를 통해:

- **병렬 개발**: 여러 브랜치에서 동시에 작업 가능
- **컨텍스트 전환 불필요**: `git checkout` 없이 디렉토리 이동만으로
- **AI 병렬 개발**: 각 worktree에서 독립된 Claude Code 세션 실행 가능

## 추천 구성: Bare Repository 패턴

```
/home/user/dev/project-name/        # 프로젝트 컨테이너
├── .bare/                          # bare git repository (실제 데이터)
├── .git                            # 포인터 파일 → .bare 참조
├── main/                           # worktree (main 브랜치)
├── feature-xxx/                    # worktree (feature-xxx 브랜치)
└── issue-42/                       # worktree (issue-42 브랜치)
```

### 구성의 장점

| 관점 | 장점 |
|------|----------|
| 정리성 | 1리포지토리 = 1디렉토리, 다른 리포지토리와 섞이지 않음 |
| 분리 | bare repo는 순수한 Git 데이터, worktree가 파일 조작 |
| AI 병렬 개발 | 각 worktree에서 독립된 Claude Code 세션 실행 가능 |
| 컨텍스트 유지 | 브랜치별로 대화 이력·상태가 유지됨 |

## 셋업 절차

### 신규 리포지토리의 경우

```bash
# 1. 프로젝트 컨테이너 생성
mkdir -p /home/user/dev/project-name
cd /home/user/dev/project-name

# 2. GitHub 리포지토리 생성 (README 포함하여 초기 커밋 생성)
gh repo create username/project-name --public \
  --description "Project description" \
  --add-readme

# 3. bare repository로 초기화
git clone --bare git@github.com:username/project-name.git .bare

# 4. .git 포인터 파일 생성
echo "gitdir: ./.bare" > .git

# 5. fetch 설정 추가
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"

# 6. main worktree 생성
git worktree add main main
```

> **Note**: `--add-readme` 옵션으로 초기 커밋이 생성된다.
> 이것이 없으면 빈 리포지토리가 되어 `git worktree add main main`이 실패한다.

### 기존 리포지토리 이전

```bash
# 1. 기존 리포지토리를 bare 형식으로 클론
cd /home/user/dev
mkdir project-name
cd project-name
git clone --bare git@github.com:username/project-name.git .bare

# 2. .git 포인터 파일 생성
echo "gitdir: ./.bare" > .git

# 3. fetch 설정 추가
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"

# 4. main worktree 생성
git worktree add main main
```

## 일상 운용

### Worktree 생성

```bash
# 프로젝트 루트에서 실행
cd /home/user/dev/project-name

# 신규 브랜치로 worktree 생성
git worktree add -b feature/new-feature ./feature-new-feature main

# 기존 브랜치로 worktree 생성
git worktree add ./hotfix-123 hotfix/123
```

### Worktree 목록 표시

```bash
git worktree list
```

### Worktree 삭제

```bash
# worktree 디렉토리 삭제
git worktree remove ./feature-new-feature

# 브랜치도 삭제하는 경우 (머지 완료)
git branch -d feature/new-feature

# 브랜치도 삭제하는 경우 (강제)
git branch -D feature/new-feature
```

### 브랜치 전환

```bash
# git checkout은 사용하지 않음
# 대신 디렉토리 이동
cd ../feature-xxx
```

## kuku 프로젝트에서의 운용

kuku에서는 Bare Repository 패턴이 아닌 **일반 리포지토리 + worktree** 패턴을 채용하고 있다.
Issue마다 worktree를 생성하여 병렬 개발을 실현한다.

### 디렉토리 구성

```
/home/user/dev/
├── kuku/                           # 메인 리포지토리 (main 브랜치)
├── kuku-feat-42/                   # worktree (feat/42 브랜치)
├── kuku-fix-73/                    # worktree (fix/73 브랜치)
└── kuku-docs-79/                   # worktree (docs/79 브랜치)
```

### 명명 규칙

| 항목 | 패턴 | 예 |
|------|----------|-----|
| 브랜치명 | `[prefix]/[issue-number]` | `feat/42` |
| 디렉토리 | `../kuku-[prefix]-[issue-number]` | `../kuku-feat-42` |

### 스킬에 의한 자동화

worktree의 라이프사이클은 스킬로 관리된다:

- `/issue-start [issue-number]`: worktree 생성, `.venv` 심볼릭 링크, Issue 본문에 메타 정보 추가 기재
- `/issue-close [issue-number]`: `.venv` symlink 삭제, worktree 삭제, 브랜치 삭제, PR 머지

수동으로 worktree를 삭제하는 경우, `.venv` 심볼릭 링크를 먼저 삭제해야 한다 (untracked file이 있으면 `git worktree remove`가 실패한다):

```bash
rm ../kuku-feat-42/.venv
git worktree remove ../kuku-feat-42
git branch -d feat/42
```

### .venv 공유

각 worktree는 메인 리포지토리의 `.venv`로의 심볼릭 링크를 사용한다:

```bash
ln -s /home/user/dev/kuku/.venv /home/user/dev/kuku-feat-42/.venv
```

> **⚠️ 주의**: `.venv`를 공유하고 있으므로, worktree 내에서의 `pip install`은 메인 리포지토리의 환경에도 영향을 준다. `pyproject.toml`의 의존 관계를 변경하는 경우, 개별 venv를 생성하여 검증할 것.

## 운용 규칙

### Do

- 디렉토리 이동으로 브랜치 전환 (`cd ../feature-xxx`)
- worktree 관리는 프로젝트 루트에서 실행
- 각 worktree에서 upstream 설정 (`git branch --set-upstream-to=origin/xxx`)

### Don't

- `git checkout`을 사용하지 않음 (디렉토리 이동으로 대응)
- 프로젝트 루트에서 일반적인 git 명령어를 실행하지 않음 (Bare Repository 패턴의 경우. 일반 리포지토리에서는 문제 없음)

## 참고 자료

- [Git 공식 `git-worktree` 매뉴얼](https://git-scm.com/docs/git-worktree)
- [How to use git worktree and in a clean way](https://morgan.cugerone.com/blog/how-to-use-git-worktree-and-in-a-clean-way/)
- [Bare Git Worktrees AGENTS.md](https://gist.github.com/ben-vargas/fd99be9bbce6d485c70442dd939f1a3d)
- [Git Worktree Best Practices and Tools](https://gist.github.com/ChristopherA/4643b2f5e024578606b9cd5d2e6815cc)
- [incident.io: Shipping faster with Claude Code and Git Worktrees](https://incident.io/blog/shipping-faster-with-claude-code-and-git-worktrees)
- [Parallel AI Coding with Git Worktrees](https://docs.agentinterviews.com/blog/parallel-ai-coding-with-gitworktrees/)
