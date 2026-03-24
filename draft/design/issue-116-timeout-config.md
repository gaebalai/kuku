# [설계] 타임아웃의ハード코드삭제와설정파일화

Issue: #116

## 개요

`kuku_harness/cli.py` 의 `DEFAULT_TIMEOUT = 1800` 를 삭제し, config.toml → workflow YAML → step YAML の3계층폴백로타임아웃를해결한다.

## 배경·목적

現状, 타임아웃는 `cli.py:19` にハード코드되어 있으며, 유저이 변경할 수 없다.워크플로우정의나 프로젝트설정부터타임아웃를 제어한다수단가 없く, 軽い스텝도重い스텝도一律 1800s 이 된다.이것를 설정파일ベースの階계층적폴백에변경し, 타임아웃의所在를 명확에한다.

## 인터페이스

### 입력

#### `.kuku/config.toml`(필수)

```toml
[execution]
default_timeout = 1800 # 초.필수.未설정는 ConfigLoadError
```

#### 워크플로우 YAML(임의)

```yaml
name: feature-development
default_timeout: 600 # 워크플로우전체의기본값
```

#### 스텝 YAML(임의)

```yaml
steps:
 - id: implement
 timeout: 3600 # 스텝개별
```

### 출력

`execute_cli()` 内로 사용된다타임아웃값(초).

### 폴백階계층

```
step.timeout → workflow.default_timeout → config.execution.default_timeout
 (최우선) (중간) (최종·필수)
```

### 사용예

```python
# execute_cli 内로 의 타임아웃해결
timeout = resolve_timeout(step, workflow, config)
```

## 제약·전제 조건

- `config.toml` 의 `[execution] default_timeout` 는 필수.未설정시는 `ConfigLoadError` を送出
- 모두의 timeout 값(`config.execution.default_timeout`, `workflow.default_timeout`, `step.timeout`)는正の整数(초단위).0이하·비整数·bool 타입는밸리데이션에러
- `step.timeout` 의 타입는 `int | None` のまま변경하지 않는다이, `_parse_workflow()` 과 `validate_workflow()` 의 양쪽로밸리데이션를추가한다
- `Workflow` 데이터 클래스에 `default_timeout: int | None = None` 필드를추가
- `kukuConfig` 에 `ExecutionConfig` 데이터 클래스를추가
- `execute_cli()` のシグネチャ에 `default_timeout: int` 파라미터를추가
- **timeout: 0 の扱い**: `step.timeout or default_timeout` のよう한 truthy 판정는사용하지 않는다.`step.timeout is not None` 로 명시적에 None 체크한다(0 이 silent fallback 된다것을방지)

## 방침

### 1. `kukuConfig` 의 확장

`config.py` 에 `ExecutionConfig` 데이터 클래스를추가し, `kukuConfig` に持たせる.

```python
@dataclass(frozen=True)
class ExecutionConfig:
 default_timeout: int # 필수.기본값값없음

@dataclass(frozen=True)
class kukuConfig:
 repo_root: Path
 paths: PathsConfig
 execution: ExecutionConfig
```

`_load()` 内로 `[execution]` 섹션의존재과 `default_timeout` 의 값를 검증한다.未설정·타입부정·0이하는 `ConfigLoadError`.

### 2. `Workflow` 모델의확장

`models.py` 의 `Workflow` 에 `default_timeout: int | None = None` 를 추가.

**파서 (`_parse_workflow()`)**: `data.get("default_timeout")` 를 파싱し, 타입(int かつ비 bool)와값(正の整数)를 검증한다.`step.timeout` 에 대해도마찬가지의밸리데이션를추가한다.

**밸리데이터 (`validate_workflow()`)**: 파서를経由せず직접구축된 `Workflow(...)` / `Step(...)` にも동등의밸리데이션를적용한다.이것는 `validate_workflow()` 이 직접구축모델도守る기존계약(`tests/test_workflow_validator.py` 로 확인완료)를유지한다위해.구체적에는:
- `workflow.default_timeout` 이 설정되어 있다경우: 正の整数이다것
- 각 `step.timeout` 이 설정되어 있다경우: 正の整数이다것

### 3. `execute_cli()` 의 변경

- `DEFAULT_TIMEOUT` 定数를 삭제
- `execute_cli()` 에 `default_timeout: int` 파라미터를추가
- 타임아웃해결: `step.timeout if step.timeout is not None else default_timeout`(truthy 판정이 아니라명시적 None 체크)

### 4. `WorkflowRunner` 의 변경

- `WorkflowRunner` 에 `config: kukuConfig` を持たせる(既에 `artifacts_dir` 経由로 config 를 사용하고 있다때문에, config 自体를 전달하다形에 변경)
- `execute_cli()` 호출시에 `default_timeout` 를 산출하여전달하다:
 `workflow.default_timeout if workflow.default_timeout is not None else config.execution.default_timeout`

### 5. `cli_main.py` 의 변경

- `cmd_run()` 로 `config` 오브젝트를 `WorkflowRunner` 에 전달하다

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.
> AI 는 테스트를생략한다傾向이 있다때문에, 설계단계로명확에정의し, 생략의여지를배제한다.
> 상세는 [테스트 규약](../../../docs/dev/testing-convention.md) 참조.

### Small 테스트

- **ExecutionConfig 의 밸리데이션**: `default_timeout` 未설정·타입부정(문자열, bool, float)·0이하의케이스로 `ConfigLoadError`
- **kukuConfig._load() 의 [execution] 파싱**: 정상값·`[execution]` 섹션欠損·`default_timeout` 키欠損·부정값의각케이스
- **Workflow.default_timeout 파싱(`_parse_workflow()`)**: 정상값·None(생략)·타입부정(문자열, bool)·0이하의케이스
- **step.timeout 파싱(`_parse_workflow()`)**: 타입부정(문자열, bool, float)·0이하의케이스로에러
- **validate_workflow() 로 의 timeout 밸리데이션**: 직접구축한 `Workflow(default_timeout=0)` 와 `Step(timeout=-1)` 이 `WorkflowValidationError` 에 된다것
- **타임아웃해결로직**: `step.timeout is not None` 의 명시적 None 체크.step.timeout=0 이 폴백되지 않는다것(밸리데이션通過後의 안전性확인)
- **폴백組み合わせ**: step.timeout 있음/없음 × workflow.default_timeout 있음/없음 の組み合わせ
- **기존테스트의수정**: `DEFAULT_TIMEOUT` 를 참조하고 있다테스트의업데이트

### Medium 테스트

- **config.toml → execute_cli 의 폴백결합**: 実파일의 config.toml 를 읽기, `execute_cli()` に渡된다타임아웃값이올바른것을검증(프로세스기동는목)
- **WorkflowRunner 결합**: config + workflow + step の3계층폴백이 `WorkflowRunner.run()` 経由で正しく해결된다것을검증(CLI 실행는목)
- **config.toml 未설정시의 에러경로**: `[execution]` 섹션없음의 config.toml 로 워크플로우실행한다와에러종료한다것

### Large 테스트

- **CLI E2E**: 実際의 `kuku run` 명령어로 config.toml 의 `default_timeout` が反映된다것을검증(기존의 E2E 테스트프레임워크에準拠.実 agent 호출는스코프외)
- **kuku validate E2E**: `default_timeout` 를 포함워크플로우 YAML 이 정상에밸리데이션를通過한다것

## 영향문서

이변경에 의해업데이트이필요에된다가능性의 있다문서를列挙한다.

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 없음 | 새로운技術選定는 없다 |
| docs/ARCHITECTURE.md | 있음 | `config.py` 의 설명(L58)에 `ExecutionConfig` 의 추가를反映.에러 계층(L238-244)에 config 関連에러의업데이트이필요한 경우있음 |
| docs/dev/workflow-authoring.md | 있음 | `timeout` 필드의기본값값·폴백사양·`default_timeout` 워크플로우필드의追記이 필요 |
| README.md | 있음 | `.kuku/config.toml` 의 최소구성예(L46-52)에 `[execution] default_timeout` 이 필수항목로서추가된다위해업데이트이필요 |
| docs/cli-guides/ | 없음 | CLI 인터페이스의변경는 없다 |
| CLAUDE.md | 없음 | 규약변경는 없다 |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| 현행 cli.py | `kuku_harness/cli.py:19,58` | `DEFAULT_TIMEOUT = 1800` がハード코드.`timeout = step.timeout or DEFAULT_TIMEOUT` 로 해결 |
| 현행 config.py | `kuku_harness/config.py` | `kukuConfig` 는 `repo_root` + `PathsConfig` 만.`[execution]` 섹션는미정의 |
| 현행 models.py | `kuku_harness/models.py:66-73` | `Workflow` 에 `default_timeout` 필드없음 |
| 현행 workflow.py | `kuku_harness/workflow.py:166-172` | `_parse_workflow()` 는 `default_timeout` 를 파싱하지 않고 있다 |
| validate_workflow() 계약 | `kuku_harness/workflow.py:175-308`, `tests/test_workflow_validator.py` | `validate_workflow()` 는 직접구축의 `Workflow(...)` / `Step(...)` にも적용된다.테스트로 `Step(...)` 를 직접구축하여검증하고 있다 |
| 워크플로우 정의 매뉴얼 | `docs/dev/workflow-authoring.md:58` | `timeout` 필드는기재있다이 기본값값의설명없음 |
| README.md | `README.md:46-52` | `.kuku/config.toml` 최소구성예에 `[paths]` 만기재.`[execution]` 필수화로 업데이트이필요 |
| docs/ARCHITECTURE.md | `docs/ARCHITECTURE.md:58,201-203` | `config.py` 의 설명과 `artifacts_dir` 의 config.toml 참조있음 |
| Python tomllib | https://docs.python.org/3/library/tomllib.html | TOML 파싱에사용.kuku 는 Python 3.11+ 로 `tomllib` 를 표준사용 |
| TOML 사양 | https://toml.io/en/v1.0.0 | `[execution]` テーブル과 `default_timeout` 키는 TOML v1.0.0 準拠 |

> **중요**: 설계판단의근거와된다一次정보를必ず기재해 주세요.
> - URL만로없이, **근거(인용/要約)** も기재필수
> - 리뷰時に一次정보의기재이 없다경우, 설계 리뷰는중단され합니다
