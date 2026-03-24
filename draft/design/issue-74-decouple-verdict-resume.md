# [설계] resume 과 previous_verdict 의 결합를解지우다る

Issue: #74

## 개요

`previous_verdict` 의 주입조건를 `resume`(세션계속)부터분리し, 워크플로우YAML로 독립에제어할 수 있다하도록한다.併せて, 테스트이본번YAML에 의존하고 있다구조를解지우다る.

## 배경·목적

현재 `previous_verdict` 는 `step.resume` 이 설정되어 있다경우만주입된다(`prompt.py:36`).
이것에 의해 mixed-agent 구성(예: review 를 codex, fix 를 claude 로 실행)로は, fix 스텝이 review 의 세션를 resume 할 수 없다위해 `previous_verdict` も受け取れ없다.

現状의 `feature-development.yaml` 로 는 `fix-code` 부터 `resume` を外す함으로써 `MissingResumeSessionError` 를 회피하고 있다이, 결과로서 review 의 verdict 정보이 fix に渡ら없다.

また, `test_skill_harness_adaptation.py` 이 `workflows/feature-development.yaml` 를 직접참조하고 있으며, 본번워크플로우의구조변경로테스트이壊れる.

## 인터페이스

### 입력

#### Step 모델의변경

```python
@dataclass
class Step:
 # ... 기존필드 ...
 resume: str | None = None
 inject_verdict: bool = False # 신규추가
```

#### 워크플로우YAML의변경

```yaml
- id: fix-code
 skill: issue-fix-code
 agent: claude
 model: opus
 inject_verdict: true # resume 없음로 도 verdict 를 받다
 on:
 PASS: verify-code
 ABORT: end
```

### 출력

`build_prompt` 이 생성한다프롬프트에 `previous_verdict` 변수이포함된다조건:

| 현재 | 변경후 |
|------|--------|
| `step.resume and state.last_transition_verdict` | `(step.resume or step.inject_verdict) and state.last_transition_verdict` |

### 사용예

```yaml
# mixed-agent: review(codex) → fix(claude)
# resume 불가だ이 verdict 는 인수인계たい
- id: fix-code
 skill: issue-fix-code
 agent: claude
 inject_verdict: true
 on:
 PASS: verify-code

# same-agent: design(claude) → fix-design(claude)
# 세션계속 + verdict 인수인계
- id: fix-design
 skill: issue-fix-design
 agent: claude
 resume: design # resume 가 있れば inject_verdict は暗黙 true
 on:
 PASS: verify-design
```

## 제약·전제 조건

- `resume` 이 설정되어 있다경우는 `inject_verdict` を明示하지 않아도 verdict 이 주입된다(하위 호환性)
- `inject_verdict` 는 `resume` 와 독립에설정가능
- 워크플로우YAML의파싱(`workflow.py`)로 `inject_verdict` 필드를認識한다필요이 있다
- 기존의워크플로우YAML는 변경없음로 동작한다(`inject_verdict` 의 기본값는 `false`)
- `inject_verdict` 의 YAML파싱時에 타입검증를 수행한다: `bool` 이외의값(문자列·数값등)는 `WorkflowValidationError` 으로 한다

## 방침

### 1. Step 모델에 `inject_verdict: bool` 를 추가

`models.py` 의 `Step` 에 `inject_verdict: bool = False` 를 추가.
`workflow.py` 의 파서ー로 YAML 부터읽기.타입검증를추가:

```python
# workflow.py _parse_workflow() 内
raw_inject_verdict = step_data.get("inject_verdict", False)
if not isinstance(raw_inject_verdict, bool):
 raise WorkflowValidationError(
 f"Step '{step_data['id']}' 'inject_verdict' must be a boolean, "
 f"got {type(raw_inject_verdict).__name__}"
 )
```

### 2. `build_prompt` 의 주입조건를변경

```python
# 변경전
if step.resume and state.last_transition_verdict:

# 변경후
if (step.resume or step.inject_verdict) and state.last_transition_verdict:
```

### 3. `feature-development.yaml` 의 업데이트

`fix-code` 에 `inject_verdict: true` 를 추가.

### 4. 테스트用YAML분리

`test_skill_harness_adaptation.py` 이 `workflows/feature-development.yaml` 를 직접참조하고 있다구조를解지우다る.

- エンジン로직의테스트 → `tests/fixtures/` にミニマルなfixture YAML를 배치
- 본번YAML의밸리데이션 → `kuku validate` 명령어에委ねる(pytestでの二重검증는불필요)

대상테스트클래스의분리방침:

| 테스트클래스 | 방침 |
|-------------|------|
| `TestWorkflowYamlParseable` | fixture YAML 에 전환 |
| `TestWorkflowValidation` | fixture YAML 에 전환 |
| `TestWorkflowSkillsExist` | 삭제.단 skill 존재확인를 `cmd_validate` 에 추가(후술 4a) |
| `TestWorkflowResumeConfig` | 삭제·再설계(`inject_verdict` 테스트에치환) |
| `TestSkillVerdictParseable` | fixture YAML 에 전환 |
| `TestWorkflowTransitions` | fixture YAML 에 전환 |

### 4a. `kuku validate` 에 skill 존재확인를추가

현행의 `cmd_validate()` 는 `load_workflow()` + `validate_workflow()` 만로, workflow 内의 `skill` 필드이実際에 파일시스템上에 존재한다か는 검증하지 않고 있다.`TestWorkflowSkillsExist` 를 삭제한다에あたり, 이책무를 `cmd_validate` に移管한다.

```python
# cli_main.py cmd_validate() 内
wf = load_workflow(path)
validate_workflow(wf)
# 추가: skill 존재확인
for step in wf.steps:
 validate_skill_exists(step.skill, step.agent, path.parent)
```

`validate_skill_exists` 는 기존의 `kuku_harness/skill.py` 에 있음, `WorkflowRunner.run()` でも사용되어 있다.`cmd_validate` にも같은검증를추가한다함으로써, `kuku validate` 単体로 skill 누락를検出할 수 있다하도록된다.

**workdir の扱い**: `cmd_validate` 는 `--workdir` 옵션를持た없다때문에, YAML 파일의親디렉토리를프로젝트루트로서사용한다.통상 `workflows/` 는 프로젝트루트바로 아래에있기 때문에 `path.parent` で十분だが, 보다정확에는 `path.parent` 부터 `pyproject.toml` 를 탐색하여프로젝트루트를특정한다방법도 있다.初회구현로는 `path.parent` 를 사용し, 부족가 있れば後続로 대응한다.

### 5. 문서업데이트

- `docs/dev/workflow-authoring.md`: `inject_verdict` 필드의설명를추가
- `docs/dev/skill-authoring.md`: `previous_verdict` 주입조건의기술를업데이트

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.

### Small 테스트

- `build_prompt` 로 `inject_verdict=True, resume=None` 의 경우에 `previous_verdict` 이 주입된다것
- `build_prompt` 로 `inject_verdict=False, resume=None` 의 경우에 `previous_verdict` 이 주입되지 않는다것
- `build_prompt` 로 `resume` 설정시는 `inject_verdict` 의 값에関わらず verdict 이 주입된다것(하위 호환)
- `Step` 모델에 `inject_verdict` 필드이존재し, 기본값 `False` 이다것

### Medium 테스트

- fixture YAML 부터워크플로우를 로드し, `inject_verdict` 필드이正しく파싱된다것
- fixture YAML 의 밸리데이션(cycle integrity, transitions)이エンジン로직로서正しく동작한다것
- SKILL.md 의 verdict example 이 fixture YAML 의 스텝정의에 기반하여파싱할 수 있다것

### Large 테스트

`kuku` CLI 는 `pyproject.toml` 에 `kuku = "kuku_harness.cli_main:main"` 로서등록완료이며, `tests/test_cli_validate.py` 에 기존의 Large 테스트이 있다.

- `cmd_validate` 에 skill 존재확인를추가한후, 기존의 `test_cli_validate.py` 의 Large 테스트로 `validate_skill_exists` 통합이검증된다것을확인한다
- 필요에応じて `test_cli_validate.py` 에 skill 누락시의 에러케이스를추가한다

## 영향문서

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 없음 | 새로운技術選定없음 |
| docs/ARCHITECTURE.md | 없음 | 아키텍처변경없음 |
| docs/dev/workflow-authoring.md | 있음 | `inject_verdict` 필드의추가 |
| docs/dev/skill-authoring.md | 있음 | `previous_verdict` 주입조건의변경 |
| CLAUDE.md | 없음 | 규약변경없음 |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| 현행의주입로직 | `kuku_harness/prompt.py:35-40` | `if step.resume and state.last_transition_verdict:` — resume 에 결합 |
| Step 모델정의 | `kuku_harness/models.py:38-50` | `resume: str \| None = None` — inject_verdict 필드없음 |
| 본번워크플로우 | `workflows/feature-development.yaml:79-85` | `fix-code` 에 resume 없음, verdict 주입되지 않는다 |
| 테스트의본번YAML의존 | `tests/test_skill_harness_adaptation.py:48` | `WORKFLOW_YAML_PATH = PROJECT_ROOT / "workflows" / "feature-development.yaml"` |
| workflow-authoring 문서 | `docs/dev/workflow-authoring.md:89-109` | resume 섹션 — inject_verdict 未기재 |
| CLI 엔트리 포인트 | `pyproject.toml:33-34` | `kuku = "kuku_harness.cli_main:main"` — 구현완료 |
| cmd_validate 구현 | `kuku_harness/cli_main.py:64-91` | `load_workflow()` + `validate_workflow()` 만, skill 존재확인없음 |
| validate 의 기존테스트 | `tests/test_cli_validate.py` | S/M/L 전サイズ의 테스트이구현완료 |
| validate_skill_exists | `kuku_harness/skill.py` | `WorkflowRunner.run()` 로 사용되어 있다 skill 존재확인함수 |
