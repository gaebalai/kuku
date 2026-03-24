# [설계] dao run CLI서브명령어의구현

Issue: #67

## 개요

`dao run` 서브명령어를구현し, 워크플로우를명령어ラ인부터실행가능에한다.

## 배경·목적

하네스의코어기능(`WorkflowRunner`, `load_workflow`, `SessionState` 등)는구현·테스트완료だが, CLIフロントエンド이 존재하지 않는다위해 `dao run <workflow.yaml> <issue>` 로서실행할 수 없다.

## 전제 조건·스코프

本イシュー로 CLI 기반(`cli_main.py` + argparse 서브명령어파서ー + `pyproject.toml` 의 `[project.scripts]` 유효화)과 `run` 서브명령어의両方를 구현한다.

#65 (`dao validate`) 는 2026-03-11 時点로 OPEN 이며, 머지待ち로 블록한다의이 아니라, #67 側로 CLI 기반를구축한다.#65 は後부터 `validate` 서브명령어를추가한다形で進める(기반의重複구현를회피).

### 本イシュー의 구현범위

1. `dao_harness/cli_main.py` — argparse 서브명령어파서ー + `run` 서브명령어
2. `pyproject.toml` — `[project.scripts]` 의 코멘트해제 + `dao` 엔트리 포인트추가
3. 테스트

## 인터페이스

### 입력

```
dao run <workflow> <issue> [options]
```

| 인수/옵션 | 타입 | 필수 | 설명 |
|-----------------|-----|------|------|
| `workflow` | positional (str) | ○ | 워크플로우YAML파일경로 |
| `issue` | positional (int) | ○ | GitHub Issue번호 |
| `--from STEP_ID` | option (str) | × | 지정스텝부터재개 |
| `--step STEP_ID` | option (str) | × | 단일스텝만실행 |
| `--workdir DIR` | option (str) | × | 에이전트 CLI 의 작업디렉토리(기본값: カレント디렉토리).상태파일·로그의저장先に는 영향하지 않는다(후술) |
| `--quiet` | flag | × | 에이전트출력의스트리밍표시를抑制 |

`--from` 과 `--step` 는 배타(동시지정는에러).

### 출력

- **정상종료**: exit 0, 최종상태의サマリー를 stdout 에 출력
- **워크플로우 ABORT**: exit 1, ABORT 이유를 stderr 에 출력
- **밸리데이션에러**: exit 2, 에러상세를 stderr 에 출력
- **CLI 실행에러**: exit 3, 에러상세를 stderr 에 출력

### 사용예

```bash
# 기본실행
dao run workflows/design.yaml 67

# 도중부터재개
dao run workflows/design.yaml 67 --from review-design

# 단일스텝실행
dao run workflows/design.yaml 67 --step implement

# 작업디렉토리지정 + 静か에 실행
dao run workflows/design.yaml 67 --workdir ../dao-feat-67 --quiet
```

## 제약·전제 조건

- 외부의존를추가하지 않는다(argparse 만)
- `WorkflowRunner` 의 기존인터페이스를변경하지 않는다
- 에러ハンドリング는 `HarnessError` 階계층를그まま활용
- exit code 는 의미를持たせる(스크립트에서의호출를상정)

### `--workdir` 와 상태저장場所の関係

`--workdir` 는 에이전트 CLI 의 `cwd` 만를 제어한다.상태파일와로그는 `dao run` 를 실행한프로세스의カレント디렉토리기준로저장된다:

| 대상 | 저장선 | `--workdir` 의 영향 |
|------|--------|-------------------|
| `SessionState` | `test-artifacts/<issue>/session-state.json`(프로세스 cwd 기준) | 없음 |
| 실행로그 | `test-artifacts/<issue>/runs/<timestamp>/`(프로세스 cwd 기준) | 없음 |
| 에이전트 CLI 의 `cwd` | `--workdir` 로 지정된디렉토리 | **있음** |

이분리는 `WorkflowRunner` 의 기존설계에従った것.`runner.py` 로 `run_dir` 는 프로세스 cwd 기준, `execute_cli()` 의 `cwd=workdir` 는 에이전트실행선만를指す.

### `--workdir` 부정시의 에러계약

`cmd_run` 는 `WorkflowRunner` を呼ぶ前에 `--workdir` の사전 검증를 수행한다:

```python
workdir = args.workdir.resolve()
if not workdir.is_dir():
 print(f"Error: --workdir '{args.workdir}' is not a valid directory", file=sys.stderr)
 return 2 # 정의에러(실행前に検出가능)
```

**이유**: `cli.py` L54-59 로 는 `subprocess.Popen(..., cwd=workdir)` 의 `FileNotFoundError` 이 `CLINotFoundError` に包まれる때문에, 사전 검증없음로は"작업디렉토리부정"が"CLI 를 찾를 찾을 수 없다"라는잘못된診断이 된다.사전 검증에 의해정확한 에러메시지를返し, exit code 2(정의에러)로종료한다.

## 방침

### 1. `cli_main.py` 의 생성과 `run` 서브명령어추가

`cli_main.py` 를 신규생성し, argparse 서브명령어파서ー과 `run` 서브명령어를구현한다.서브명령어구조는 #65 (`validate`) が後부터추가할 수 있다확장性を持たせる.

```python
# 疑似코드
def register_run(subparsers):
 p = subparsers.add_parser("run", help="Run a workflow")
 p.add_argument("workflow", type=Path)
 p.add_argument("issue", type=int)
 p.add_argument("--from", dest="from_step")
 p.add_argument("--step", dest="single_step")
 p.add_argument("--workdir", type=Path, default=Path.cwd())
 p.add_argument("--quiet", action="store_true")
 p.set_defaults(func=cmd_run)
```

### 2. `cmd_run` 함수

`load_workflow` → `WorkflowRunner` → `run()` 의 파이프라인를 실행し, 예외를 exit code 에 매핑한다.

```python
def cmd_run(args) -> int:
 # 배타체크: --from 과 --step
 # load_workflow(args.workflow)
 # WorkflowRunner(...).run()
 # 에러ハンドリング → 적절한 exit code
```

### 3. exit code 매핑

기지의 `HarnessError` 서브클래스를망라적에매핑한다.`HarnessError` を基底로 catch 한다함으로써, 将来추가된다서브클래스도"기지에러"로서다루다.

| exit code | 의미 | 대응한다예외 |
|-----------|------|-------------|
| 0 | 정상종료 | — |
| 1 | 워크플로우 ABORT | ABORT verdict 로 종료한 경우 |
| 2 | 정의에러(실행前に検出) | `WorkflowValidationError`, `SkillNotFound`, `SecurityError` |
| 3 | 실행시에러(스텝실행中에 발생) | `CLIExecutionError`, `CLINotFoundError`, `StepTimeoutError`, `MissingResumeSessionError`, `InvalidTransition`, `VerdictNotFound`, `VerdictParseError`, `InvalidVerdictValue` |
| 1 | 예기하지 않는다에러 | `HarnessError` 의 미지서브클래스, 또는 `HarnessError` 이외의예외 |

**구현방침**: 개별의예외클래스를列挙한다의이 아니라, `HarnessError` 의 catch 内로 분류한다:

```python
try:
 ...
except WorkflowValidationError | SkillNotFound | SecurityError as e:
 # 정의에러 → exit 2
except HarnessError as e:
 # 기타기지실행시에러 → exit 3
except Exception as e:
 # 예기하지 않는다에러 → exit 1
```

**유저용메시지**: 모두의 `HarnessError` 는 `str(e)` 로 사람이 읽을 수 있는한 메시지를제공완료(`errors.py` 의 각 `__init__` 로 설정).CLI 는 `stderr` 에 그まま출력한다.

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.

### Small 테스트

- `--from` 과 `--step` 의 배타밸리데이션
- 인수파싱: 각옵션이正しく `WorkflowRunner` 의 파라미터에매핑된다것
- exit code 매핑: 전 `HarnessError` 서브클래스(`WorkflowValidationError`, `SkillNotFound`, `SecurityError`, `CLIExecutionError`, `CLINotFoundError`, `StepTimeoutError`, `MissingResumeSessionError`, `InvalidTransition`, `VerdictNotFound`, `VerdictParseError`, `InvalidVerdictValue`)이올바른 exit code 로 변환된다것
- `HarnessError` 이외의예기하지 않는다예외 → exit 1
- `--workdir` 사전 검증: 존재하지 않는다경로 → exit 2, 파일경로(디렉토리이 아니다) → exit 2
- サマリー출력의포맷

### Medium 테스트

- 유효한 워크플로우YAML + 목완료 `WorkflowRunner` 로 정상종료 → exit 0
- 부정なYAML → exit 2 + 에러메시지이 stderr 에 출력
- `WorkflowRunner.run()` 이 `CLIExecutionError` → exit 3
- `WorkflowRunner.run()` 이 ABORT verdict → exit 1
- `--workdir` 에 존재하지 않는다디렉토리 → exit 2 + 정확한 에러메시지(`CLINotFoundError` 이 아니라)
- `subprocess` 経由로 의 `dao run --help` 출력검증

### Large 테스트

- 実際의 `dao run` 명령어를 subprocess 로 실행し, 유효한 워크플로우YAML(단에이전트CLI未설치의상태)로 `CLINotFoundError` 상당의에러이返る것
- `pip install -e .` 후에 `dao run --help` 이 이용가능이다것

## 영향문서

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 없음 | argparse 選定는 #65 로 논의완료.本イシューは同방침를踏襲 |
| docs/ARCHITECTURE.md | 軽微 | L108-113 로 `dao run` 의 `--from` 재개를既에 기술완료.신플래그 (`--workdir`, `--quiet`) の追記이 필요한 가능性 |
| docs/dev/workflow-authoring.md | 업데이트 | L170-181 로 `dao run` 명령어예를既에 기술완료.신플래그의追記 + exit code 의 설명추가 |
| docs/dev/skill-authoring.md | 없음 | 컨텍스트변수의변경없음 |
| docs/dev/development_workflow.md | 없음 | 스킬ライフ사이클의기술이며 CLI 하네스는無関係 |
| docs/cli-guides/ | 없음 | claude/codex/gemini 각 CLI 의 레퍼런스이며 `dao` CLI 는 대상외 |
| README.md | 업데이트 | 워크플로우실행방법의섹션이미기재.`dao run` 의 기본적인 使い方를 추가 |
| CLAUDE.md | 軽微 | `dao run` 의 기본3패턴는기재완료.`--workdir` / `--quiet` を追記한다가능性 |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| argparse 공식문서 | https://docs.python.org/3/library/argparse.html | 서브명령어파서ー (`add_subparsers`) 의 사양.#65 で選定완료의 수법를踏襲 |
| WorkflowRunner 구현 | `dao_harness/runner.py` | `run()` 메서드의シグネチャ: `workflow`, `issue_number`, `workdir`, `from_step`, `single_step`, `verbose` |
| #65 설계 | https://github.com/apokamo/dev-agent-orchestra/issues/65 | CLI기반(`cli_main.py` + argparse + `[project.scripts]`)의 설계.`run` 서브명령어는명시적에스코프외.#67 로 기반를선행구현한다방침에변경 |
| state.py | `dao_harness/state.py` L15-16 | `STATE_FILE = "session-state.json"`.상태파일의정식명칭 |
| errors.py | `dao_harness/errors.py` | 예외階계층: `HarnessError` を基底とし, 각에러이명확에분류완료 |
