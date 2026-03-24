# [설계] 同居타입이용모델와설정파일설계

Issue: #70

## 개요

kuku_harness 를 별프로젝트로이용한다를 위한同居타입이용모델를정의し, 설정파일 `.kuku/config.toml` 의 사양, 경로해결규칙, artifacts 배치를설계한다.

## 배경·목적

kuku_harness 는 현재, 自身의 리포지토리内로 의 실행를暗黙의 전제로서있다.별프로젝트(예: kamo2)로이용한다위해는이하의기술적負債を解지우다る필요이 있다.

**現状의 문제**:

1. `state.py:15` 의 `STATE_DIR = Path("test-artifacts")` 이 모듈레벨定数로서ハード코드되어 있다
2. `runner.py:64-65` 이 `Path(f"test-artifacts/{self.issue_number}/runs/...")` 를 직접구축하고 있으며, `STATE_DIR` と暗黙결합하고 있다
3. Skills 는 `workdir` 기준로해결된다이, State / Logs 는 프로세스 CWD 기준로해결된다不整合이 있다
4. 설정파일의구조이존재하지 않는다

## 인터페이스

### 입력

#### `.kuku/config.toml`

대상프로젝트의 repo root 에 배치한다유일의설정파일.

```toml
# .kuku/config.toml — 최소구성(필수키없음)

[paths]
artifacts_dir = ".kuku-artifacts" # 기본값값.repo root 상대
```

| 섹션 | 키 | 타입 | 필수 | 기본값 | 설명 |
|-----------|------|-----|------|-----------|------|
| `[paths]` | `artifacts_dir` | string | No | `".kuku-artifacts"` | artifacts 출력선.repo root 상대경로 |

**설계판단**: 필수키를設け없다.`.kuku/config.toml` 이 존재한다것自体が"kuku 프로젝트이다"라는마커이 된다.空파일로도유효.

#### CLI 인수

```bash
# 현행 CLI(변경없음)
kuku run <workflow-path> <issue> [--workdir <dir>] [--from <step>] [--step <step>] [--quiet]
kuku validate <workflow-yaml>... [--project-root <dir>]
```

CLI 인수의구조는변경하지 않는다.변경한다의는내부의 경로해결로직만.

### 출력

- `{artifacts_dir}/{issue}/session-state.json` — 세션상태
- `{artifacts_dir}/{issue}/progress.md` — 사람이 읽을 수 있는한 진척
- `{artifacts_dir}/{issue}/runs/{timestamp}/run.log` — JSONL 실행로그
- `{artifacts_dir}/{issue}/runs/{timestamp}/{step_id}/stdout.log` — CLI 生출력
- `{artifacts_dir}/{issue}/runs/{timestamp}/{step_id}/console.log` — adapter 정형완료출력
- `{artifacts_dir}/{issue}/runs/{timestamp}/{step_id}/stderr.log` — 에러출력

### 사용예

```python
# 1. Config 의 로드(내부 API)
from kuku_harness.config import kukuConfig

config = kukuConfig.discover() # CWD 부터 .kuku/config.toml 를 탐색
print(config.repo_root) # /home/user/kamo2
print(config.artifacts_dir) # /home/user/kamo2/.kuku-artifacts

# 2. WorkflowRunner 로의주입
runner = WorkflowRunner(
 workflow=workflow,
 issue_number=42,
 project_root=config.repo_root, # 스킬해결 + agent cwd
 artifacts_dir=config.artifacts_dir, # state + logs
)
```

```bash
# CLI 실행예

# 1. 初회세트업(대상프로젝트로)
cd /path/to/kamo2
mkdir -p .kuku/workflows
touch .kuku/config.toml
echo ".kuku-artifacts/" >> .gitignore

# 2. repo root 부터실행
cd /path/to/kamo2
kuku run .kuku/workflows/feature-development.yaml 42

# 3. 서브디렉토리부터실행
# - workflow path 는 CWD 상대로 해결
# - config 탐색는 CWD 부터 walk-up 하여 repo root 를 자동検出
# - agent CLI は検出된 repo root 로 실행된다
cd /path/to/kamo2/src/deep/nested
kuku run ../../../.kuku/workflows/feature-development.yaml 42

# 4. --workdir 明示(config 탐색의起点를 덮어쓰기)
# - workflow path は引き続き CWD 상대
# - config 탐색는 --workdir を起点에 한다
kuku run /path/to/kamo2/.kuku/workflows/feature-development.yaml 42 --workdir /path/to/kamo2

# 5. config 를 찾를 찾을 수 없다경우
cd /tmp
kuku run workflow.yaml 42
# → stderr: "Error: .kuku/config.toml not found. Searched from /tmp to /."
# → exit 2
```

## 제약·전제 조건

- Python 3.11+ 이 전제(`tomllib` 이 표준라이브러리에포함된다)
- 설정소스는 `.kuku/config.toml` の一箇所만.CLI flag / 환경변수 / `pyproject.toml` 에서의설정읽기는대상외
- 분리타입(orchestrator repo 와 대상프로젝트J repo 를 분ける운용)는대상외
- Skills 의 디렉토리경로는각에이전트 CLI 의 관습에고정된다(`.claude/skills/`, `.agents/skills/`)때문에, config 에서의변경는불가

## 방침

### 1. `project_root` 과 `agent_workdir` 의 책무분리

현행구현로는 `workdir` 이 이하의2つ의 역할를兼ね하고 있다:

| 현행의 `workdir` 의 용도 | 참조箇所 |
|------------------------|---------|
| 스킬존재확인의 기저경로 | `runner.py:55` → `validate_skill_exists(step.skill, step.agent, self.workdir)` |
| 에이전트 CLI 의 `cwd` | `cli.py:56` → `subprocess.Popen(cwd=workdir)` |
| Codex 의 `-C` 인수 | `cli.py:187` → `-C str(workdir)` |
| verdict formatter 의 `workdir` | `runner.py:149` → `create_verdict_formatter(workdir=self.workdir)` |

同居타입모델로는, 이것들의 역할를 **`project_root`** 로서統一し, config 부터결정한다:

```
project_root(config 由来)
 ├─ 스킬해결의 기저경로 → project_root / .claude/skills/
 ├─ 에이전트 CLI 의 cwd → subprocess.Popen(cwd=project_root)
 ├─ artifacts 基底경로 → project_root / artifacts_dir
 └─ verdict formatter → create_verdict_formatter(workdir=project_root)
```

**`--workdir` 의 역할변경**:

| | 변경전 | 변경후 |
|--|--------|--------|
| 의미 | 에이전트 CLI 의 cwd + 스킬해결의 기저 | config 탐색의起点 |
| 기본값 | CWD | CWD |
| 実효과 | 그まま `subprocess.Popen(cwd=)` に渡る | `discover(start_dir=)` 의 인수에된다 |

config 発見後는 `project_root = config.repo_root` 이 전경로해결의유일의기준이 된다.`--workdir` 의 값自体は使われ없다.

**판단이유**: 에이전트 CLI 이 `.claude/skills/` 와 `CLAUDE.md` を正しく로드하려면, `cwd` 이 repo root でなければ라면없다.`--workdir` 를 그まま agent cwd 에 전달하다현행의설계는, 서브디렉토리실행로 skill 해결이파탄한다.config 부터 repo root 를 확정させ, 전경로해결를거기에 집약한다方이 안전.

### 2. Config 発見알고리즘

```
discover(start_dir=None):
 1. start_dir 이 지정されていれば, 그것を起点으로 한다
 2. 지정されていなければ CWD を起点으로 한다
 3. 起点부터親디렉토리를順に辿り, .kuku/config.toml を探す
 4. 파일시스템루트(/)에도달하여も見つ부터なければ,
 stderr 에 탐색범위를 포함에러메시지를출력し exit 2

CLI 와 의 통합:
 - `kuku run`:
 1. --workdir 이 지정されていれば --workdir を起点, なければ CWD を起点
 2. discover() 로 .kuku/config.toml 를 탐색
 3. config.repo_root 를 project_root とし, 스킬해결·agent cwd·artifacts 에 사용
 - `kuku validate`:
 1. --project-root 이 지정されていれば그것를 repo root 로서사용
 2. なければ YAML 親디렉토리부터 .kuku/config.toml 를 탐색
 3. config 를 찾부터なければ pyproject.toml 를 탐색(하위 호환)
 4. いずれも見つ부터なければ YAML 親디렉토리를 root 으로 한다(현행동작)
```

**`kuku validate` 이 config 를 필수에하지 않는다이유**: kuku 自身의 리포지토리로도 `kuku validate` 를 사용한다위해.단, 프로젝트 PJ 로 `.kuku/config.toml` 이 존재하는 경우는그것를 우선한다함으로써, 비 Python 리포지토리로의 skill 해결파탄(YAML 親 = `.kuku/workflows/` → `.kuku/workflows/.claude/skills/...` を探し에 행く문제)를防ぐ.

### 3. Repo root 의 정의

- **repo root = `.kuku/config.toml` 를 포함디렉토리**
- Artifacts, skills 는 모두 repo root 상대로 해결한다
- Workflow 경로는 CWD 상대(후술의 §5 참조)
- 에이전트 CLI 의 `cwd` 는 `project_root`(repo root)에고정된다

### 4. Artifacts 統一

현행의 `test-artifacts/` 를 config ベース의 `artifacts_dir` 에 치환하다.

```
변경前:
 state.py: STATE_DIR = Path("test-artifacts") # CWD 상대
 runner.py: Path(f"test-artifacts/{issue}/runs/...") # CWD 상대

변경後:
 config: artifacts_dir = repo_root / config.paths.artifacts_dir
 state.py: SessionState.load_or_create(issue, artifacts_dir)
 runner.py: WorkflowRunner(artifacts_dir=config.artifacts_dir)
```

**영향범위**:
- `SessionState.__init__` 에 `artifacts_dir: Path` 파라미터를추가
- `STATE_DIR` 모듈레벨定数를 삭제
- `WorkflowRunner` 에 `artifacts_dir: Path` 파라미터를추가.현행의 `workdir` 파라미터는폐지し, `project_root` 에 명칭변경
- `runner.py:64-65` のハード코드된경로를 `artifacts_dir` 経由에 변경

### 5. Workflow 경로의해결기준

`<workflow-path>` 는 **CWD 상대**로 해결한다.repo root 상대이 아니다.

```bash
# CWD = repo root 의 경우(最も일반적)
cd /path/to/kamo2
kuku run .kuku/workflows/feature-development.yaml 42
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# CWD 에서의상대경로 → /path/to/kamo2/.kuku/workflows/feature-development.yaml

# CWD = 서브디렉토리의 경우
cd /path/to/kamo2/src/deep
kuku run ../../.kuku/workflows/feature-development.yaml 42
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# CWD 에서의상대경로 → /path/to/kamo2/.kuku/workflows/feature-development.yaml

# 絶対경로도가능
kuku run /path/to/kamo2/.kuku/workflows/feature-development.yaml 42
```

**판단이유**: シェル의 표준적인 경로해결을 따른다.현행구현 (`cli_main.py:161` 의 `args.workflow.exists()`) 도 CWD 상대이며, 동작변경없음.`<workflow-path>` 만 repo root 상대에 하면, CLI 인수의セマンティクス이 혼재하여直感に反한다.

### 6. `test-artifacts/` 에서의移행계약

**Clean break** 를 채용한다.

- `.kuku/config.toml` 이 존재한다환경로는 `artifacts_dir`(기본값: `.kuku-artifacts/`)만를 참조한다
- 旧 `test-artifacts/` 로의 fallback 참조는행わ없다
- 기존의 `session-state.json` は移행하지 않는다(`--from` 에 의한 resume 는 새로운 artifacts_dir で最初부터やり直し)
- kuku 自身의 리포지토리로는 `.kuku/config.toml` 를 도입し, `test-artifacts/` 를 단계적으로 폐지한다

**판단이유**: `test-artifacts/` 는 kuku 自身의 개발용디렉토리명이며, 외프로젝트PJ に는 존재하지 않는다.Fallback を入れると"config 있음 + 구디렉토리있음"の組み合わせ테스트이필요에되어, 복잡さに見合う利益이 없다.resume が壊れる케이스는 `--from` 없음로最初부터실행すれば회復가능.

### 7. kuku 自体의 도입방법

kuku_harness 는 대상프로젝트J 의 Python 환경에 `pip install` 한다.

```bash
# HTTPS(CI / GitHub Actions 용 — 토큰인증)
pip install "kuku @ git+https://github.com/apokamo/kuku.git@v0.2.0"

# SSH(로컬개발용)
pip install "kuku @ git+ssh://git@github.com/apokamo/kuku.git@v0.2.0"
```

| 항목 | 방침 |
|------|------|
| 프로토콜 | HTTPS 과 SSH の両方를 지원.문서에両方기재 |
| 버전고정 | **git ref 지정를필수**으로 한다.tag(`@v0.2.0`)추천, commit hash(`@79ceab8`)も가능.ref 없음의 `@main` 는 비추천.現時点로 는 tag 未생성때문, 初회도입시는 commit hash 를 사용し, 릴리스운용確立後에 tag に移행한다 |
| PyPI | 現時点では未공개.안정後に移행가능(대상 프로젝트 側의 변경는 install 명령어만) |

### 8. 대상 프로젝트 의 표준디렉토리구성

```
target-project/
├── .kuku/ # kuku 설정(git 관리)
│ ├── config.toml # 설정파일(空でも가능)
│ └── workflows/ # 워크플로우정의
│ ├── feature-development.yaml
│ └── bugfix.yaml
├── .claude/skills/ # Claude Code 용스킬(경로고정)
│ ├── issue-design/
│ │ └── SKILL.md
│ └── issue-implement/
│ └── SKILL.md
├── .agents/skills/ # Codex / Gemini 용스킬(경로고정)
│ └── ...
├── .kuku-artifacts/ # 실행 artifacts(.gitignore 대상)
│ └── <issue-number>/
│ ├── session-state.json
│ ├── progress.md
│ └── runs/
│ └── <timestamp>/
│ ├── run.log
│ ├── stdout.log
│ ├── console.log
│ └── stderr.log
├── .gitignore # .kuku-artifacts/ 를 포함
└── (대상프로젝트의소스코드)
```

### 9. 구현방침(疑似코드)

#### config.py(신규)

```python
import tomllib
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class PathsConfig:
 artifacts_dir: str = ".kuku-artifacts"

@dataclass(frozen=True)
class kukuConfig:
 repo_root: Path
 paths: PathsConfig

 @property
 def artifacts_dir(self) -> Path:
 return self.repo_root / self.paths.artifacts_dir

 @classmethod
 def discover(cls, start_dir: Path | None = None) -> "kukuConfig":
 """CWD or start_dir 부터 .kuku/config.toml 를 탐색."""
 current = (start_dir or Path.cwd()).resolve()
 while True:
 candidate = current / ".kuku" / "config.toml"
 if candidate.is_file():
 return cls._load(candidate)
 parent = current.parent
 if parent == current:
 raise ConfigNotFoundError(start_dir or Path.cwd())
 current = parent

 @classmethod
 def _load(cls, path: Path) -> "kukuConfig":
 """TOML 를 파싱し kukuConfig 를 구축."""
 with open(path, "rb") as f:
 data = tomllib.load(f)
 paths_data = data.get("paths", {})
 paths = PathsConfig(**{
 k: v for k, v in paths_data.items()
 if k in PathsConfig.__dataclass_fields__
 })
 return cls(repo_root=path.parent.parent, paths=paths)
```

#### cli_main.py 의 변경

```python
def cmd_run(args):
 # config 탐색: --workdir 이 지정されていれば거기を起点, なければ CWD
 start_dir = args.workdir.resolve() if args.workdir != Path.cwd() else None
 try:
 config = kukuConfig.discover(start_dir=start_dir)
 except ConfigNotFoundError as e:
 print(f"Error: {e}", file=sys.stderr)
 return EXIT_CONFIG_NOT_FOUND # exit 2

 project_root = config.repo_root # 전경로해결의기준

 runner = WorkflowRunner(
 workflow=workflow,
 issue_number=args.issue,
 project_root=project_root, # 스킬해결 + agent cwd
 artifacts_dir=config.artifacts_dir, # state + logs
 ...
 )
```

```python
def _resolve_project_root_for_validate(explicit_root, yaml_path):
 """validate 용의 root 해결.run とは異되어 config 필수에하지 않는다."""
 # 1. --project-root 明示
 if explicit_root is not None:
 return explicit_root.resolve()
 # 2. .kuku/config.toml 를 탐색
 try:
 config = kukuConfig.discover(start_dir=yaml_path.resolve().parent)
 return config.repo_root
 except ConfigNotFoundError:
 pass
 # 3. pyproject.toml 를 탐색(하위 호환)
 current = yaml_path.resolve().parent
 while True:
 if (current / "pyproject.toml").exists():
 return current
 parent = current.parent
 if parent == current:
 break
 current = parent
 # 4. YAML 親디렉토리
 return yaml_path.resolve().parent
```

#### runner.py 의 변경

```python
@dataclass
class WorkflowRunner:
 workflow: Workflow
 issue_number: int
 project_root: Path # 旧 workdir 를 명칭변경.스킬해결 + agent cwd
 artifacts_dir: Path # 신파라미터.state + logs 의 기저

 def run(self):
 # 스킬검증: project_root 를 기준
 for step in self.workflow.steps:
 validate_skill_exists(step.skill, step.agent, self.project_root)

 # state: artifacts_dir 를 기준
 state = SessionState.load_or_create(self.issue_number, self.artifacts_dir)

 # run log: artifacts_dir 를 기준
 run_dir = self.artifacts_dir / str(self.issue_number) / "runs" / timestamp

 # CLI 실행: project_root 를 cwd に
 result = execute_cli(step=..., workdir=self.project_root, ...)
```

#### state.py 의 변경

```python
# STATE_DIR 定数를 삭제

class SessionState:
 def __init__(self, issue_number: int, artifacts_dir: Path):
 self.issue_number = issue_number
 self._artifacts_dir = artifacts_dir

 @classmethod
 def load_or_create(cls, issue: int, artifacts_dir: Path) -> "SessionState":
 path = artifacts_dir / str(issue) / STATE_FILE
 ...
```

### 10. kamo2 도입세트업

대상프로젝트 kamo2 로의도입절차:

```bash
# 1. kuku 의 설치
cd /path/to/kamo2
pip install "kuku @ git+https://github.com/apokamo/kuku.git@v0.2.0"

# 2. 설정디렉토리의생성
mkdir -p .kuku/workflows

# 3. 설정파일의생성(空でも가능)
touch .kuku/config.toml

# 4. .gitignore 에 artifacts 를 추가
echo ".kuku-artifacts/" >> .gitignore

# 5. 워크플로우와스킬의배치
cp /path/to/templates/feature-development.yaml .kuku/workflows/
mkdir -p .claude/skills .agents/skills
# 스킬파일를배치...

# 6. 동작확인
kuku validate .kuku/workflows/feature-development.yaml
kuku run .kuku/workflows/feature-development.yaml 1 --step design
```

**전제 조건**:
- Python 3.11+ 이 설치완료
- 에이전트 CLI(claude, codex, gemini のいずれか)이설치완료
- GitHub CLI (`gh`) 이 설치완료(Issue 조작를 수행한다스킬를 사용하다경우)
- 로컬실행만.CI 실행는将来검토

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.
> AI 는 테스트를생략한다傾向이 있다때문에, 설계단계로명확에정의し, 생략의여지를배제한다.
> 상세는 [테스트 규약](../../../docs/dev/testing-convention.md) 참조.

### Small 테스트

- **TOML 파싱**: 유효한 config / 空파일 / 부정 TOML / 미지키(無視된다)의 파싱과 validation
- **PathsConfig 기본값값**: `artifacts_dir` 생략時에 기본값값이적용된다것
- **repo root 산출**: config.toml 의 경로부터正しく親の親를 repo root 로서반환하다것
- **artifacts_dir 해결**: repo root + `paths.artifacts_dir` 의 결합이올바른것
- **ConfigNotFoundError**: 탐색실패시의 에러메시지에탐색시작경로이포함된다것

### Medium 테스트

- **Config discovery(파일시스템결합)**: tmpdir 에 `.kuku/config.toml` 를 배치し, CWD / 서브디렉토리 / 존재하지 않는다케이스로의 탐색동작를 검증
- **SessionState with artifacts_dir**: `artifacts_dir` 파라미터経由로 state 파일의読み書き이 올바른경로에행われる것
- **RunLogger with configurable dir**: `artifacts_dir` 하위에 run 로그이출력된다것
- **WorkflowRunner with config**: config 부터주입된 `artifacts_dir` 이 state 과 logger に伝播한다것
- **CLI integration**: `cmd_run` 이 config discovery → runner 구축 → 실행의流れ로 `artifacts_dir` を正しく전달하다것

### Large 테스트

- **E2E: config-based run**: `.kuku/config.toml` 를 가진다테스트프로젝트로 `kuku run` 를 실행し, `.kuku-artifacts/` 에 state 과 logs 이 출력된다것
- **E2E: config not found**: `.kuku/config.toml` 이 존재하지 않는다환경로 `kuku run` 를 실행し, exit 2 + 적절한 에러메시지이出る것
- **E2E: validate without config**: `kuku validate` 이 config 없음로도동작한다것(하위 호환)

### 스킵한다サイズ

없음.모두의サイズ를 구현한다.

## 영향문서

이변경에 의해업데이트이필요에된다가능性의 있다문서를列挙한다.

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 없음 | 이용모델의 ADR 는 설계이안정한단계로별途검토 |
| docs/ARCHITECTURE.md | 있음 | 세션관리의 경로기술 (`test-artifacts/`) 를 업데이트.config 계층의추가 |
| docs/dev/development_workflow.md | 없음 | 워크플로우절차自体は変わら없다 |
| docs/dev/workflow-authoring.md | 있음 | 워크플로우 YAML 의 배치선로서 `.kuku/workflows/` を追記 |
| docs/cli-guides/ | 없음 | CLI 인수구조는変わら없다 |
| CLAUDE.md | 있음 | Essential Commands 의 `kuku run` 예에 config 전제를追記 |
| README.md | 있음 | 세트업절차, 이용예, 디렉토리구성를업데이트 |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| Python tomllib | https://docs.python.org/3/library/tomllib.html | Python 3.11+ 표준라이브러리.외부의존불필요로 TOML 를 파싱할 수 있다 |
| kuku_harness/state.py | `kuku_harness/state.py:15` | `STATE_DIR = Path("test-artifacts")` — 변경대상의ハード코드定数 |
| kuku_harness/runner.py | `kuku_harness/runner.py:64-65` | `Path(f"test-artifacts/...")` — STATE_DIR と暗黙결합하고 있다 run log 경로 |
| kuku_harness/cli_main.py | `kuku_harness/cli_main.py:71-89` | `_resolve_project_root()` — 현행의 project root 해결로직.config discovery 에 치환대상 |
| kuku_harness/skill.py | `kuku_harness/skill.py:7-11` | `SKILL_DIRS` — Skills 디렉토리는 agent CLI 의 관습에고정.config 에서의변경는불가의 근거 |
| TOML v1.0.0 사양 | https://toml.io/en/v1.0.0 | TOML 포맷의공식사양.config.toml の書式근거 |
| Issue #70 설계 리뷰 (1st) | Issue #70 코멘트 (2026-03-11) | config 発見알고리즘, workflow 해결계약, 移행계약, 테스트전략의 must-fix 指摘 |
| Issue #70 설계 리뷰 (2nd) | previous_verdict (cycle 1) | project_root 과 agent_workdir 의 책무분리, validate 의 root 해결, workflow-path 상대기준의 3 건 |
