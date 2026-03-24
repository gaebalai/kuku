# [설계] V5/V6旧파일를legacy/에 정리しV7기반를명확화

Issue: #59

## 개요

V5/V6의구파일를 `legacy/` 디렉토리에이동し, `pyproject.toml`·`README.md`·`docs/ARCHITECTURE.md` をV7기반에合わせて업데이트한다.

## 배경·목적

V7(dao_harness)로의移행이완료し, #57/#58로 머지완료.しかし리포지토리루트에V5/V6의코드·테스트·문서이혼재하고 있으며, 이하의リスク이 있다:

1. 신규参加者がV5코드를誤って수정·사용한다
2. `pyproject.toml` 이 `bugfix_agent*` を含み, 불필요한 패키지이공개된다
3. `README.md` がV5의내용로, 프로젝트의現状を反映하지 않고 있다

구파일는git履歴로 완전에참조가능だが, `legacy/` に退避한다함으로써디렉토리를辿って참조할 수 있다利便性를 유지한다.

## 인터페이스

### 입력

없음(리포지토리内의 파일조작만)

### 출력

- `legacy/` 디렉토리에구파일이이동된상태
- 업데이트된 `pyproject.toml`, `README.md`, `docs/ARCHITECTURE.md`

### 사용예

```bash
# 移행후의 디렉토리구성확인
ls legacy/
# bugfix_agent/ bugfix_agent_orchestrator.py config.toml tests/ ...

# V7테스트의실행(legacy이동後も変わらず동작)
pytest tests/

# V7의품질 체크
ruff check dao_harness/ tests/ && mypy dao_harness/
```

> **주의**: 現時点로 는 `dao_harness` にCLI엔트리 포인트이존재하지 않는다(`__main__.py` 未생성, `pyproject.toml` 의 `[project.scripts]` 未정의).CLI엔트리 포인트의추가는이Issue의스코프외이며, 별途대응한다.本Issue는 파일정리와문서업데이트만를스코프으로 한다.

## 제약·전제 조건

- `legacy/` 하위의파일는**참조전용**.동작한다필요는없이, import가능이다필요도 없다
- `legacy/` 内의 Python파일는 `pyproject.toml` 의 패키지에含め없다
- V7코드 (`dao_harness/`) 및 V7테스트 (`tests/`) 는 `legacy/` 内의 모듈에一切의존해서는 안 된다
- `git mv` 를 사용하여git履歴의 추적性를 유지한다

## 방침

### Phase 1: V5/V6테스트의仕분け

현재 `tests/` 에 V5테스트(`bugfix_agent` 를 import)과 V7테스트(`dao_harness` 를 import)이혼재하고 있다.이동前に仕분け이 필요.

**V5테스트(`legacy/` へ이동):**

| 파일 | 근거 |
|---|---|
| `tests/test_prompts.py` | `from bugfix_agent.prompts import ...` |
| `tests/test_handlers.py` | `from bugfix_agent.agent_context import ...` |
| `tests/test_issue_provider.py` | `from bugfix_agent.agent_context import ...` |
| `tests/conftest.py` | `from bugfix_agent.agent_context import AgentContext` 등.V5픽스처전용 |
| `tests/utils/providers.py` | `from bugfix_agent.providers import IssueProvider` |
| `tests/utils/context.py` | `from bugfix_agent.agent_context import AgentContext` |
| `tests/utils/__init__.py` | `from bugfix_agent.providers import ...` |

**V7테스트(`tests/` 에 남기다):**

| 파일 | 근거 |
|---|---|
| `tests/test_adapters.py` | `dao_harness.adapters` 의 테스트 |
| `tests/test_cli_args.py` | `dao_harness.cli` 의 테스트 |
| `tests/test_cli_streaming_integration.py` | `dao_harness.cli` 의 테스트 |
| `tests/test_cycle_limit.py` | `dao_harness.models` 의 테스트 |
| `tests/test_e2e_cli.py` | `dao_harness.adapters` E2E테스트 |
| `tests/test_logging_integration.py` | `dao_harness.logger` 의 테스트 |
| `tests/test_prompt_builder.py` | `dao_harness.prompt` 의 테스트 |
| `tests/test_run_logger.py` | `dao_harness.logger` 의 테스트 |
| `tests/test_session_state.py` | `dao_harness.state` 의 테스트 |
| `tests/test_skill_validation.py` | `dao_harness.skill` 의 테스트 |
| `tests/test_start_logic.py` | `dao_harness.runner` 의 테스트 |
| `tests/test_state_persistence.py` | `dao_harness.state` 의 테스트 |
| `tests/test_verdict_parser.py` | `dao_harness.verdict` 의 테스트 |
| `tests/test_workflow_execution.py` | `dao_harness.runner` 의 테스트 |
| `tests/test_workflow_parser.py` | `dao_harness.workflow` 의 테스트 |
| `tests/test_workflow_validator.py` | `dao_harness.workflow` 의 테스트 |

**conftest.py の扱い**: 현재의 `tests/conftest.py` はV5픽스처전용(`bugfix_agent` import).V7테스트는conftest.py의픽스처를 사용하지 않고 있다때문에, 그まま `legacy/` へ이동한다.V7테스트에conftest.py이 필요에되었다경우는별途생성한다.

### Phase 2: 파일이동

`git mv` 로 이하를 `legacy/` 에 이동:

```
legacy/
├── bugfix_agent/ # V5/V6패키지
├── bugfix_agent_orchestrator.py # V5엔트리 포인트
├── test_bugfix_agent_orchestrator.py # V5통합테스트(루트바로 아래)
├── prompts/ # V6프롬프트
├── config.toml # V5설정
├── AGENT.md # V5에이전트지시서
├── tests/ # V5테스트
│ ├── conftest.py
│ ├── test_prompts.py
│ ├── test_handlers.py
│ ├── test_issue_provider.py
│ └── utils/ # V5테스트유틸리티
│ ├── __init__.py
│ ├── context.py
│ └── providers.py
└── docs/ # V5문서
 ├── ARCHITECTURE.ja.md
 ├── E2E_TEST_FINDINGS.md
 └── TEST_DESIGN.md
```

### Phase 3: pyproject.toml 업데이트

- `include = ["bugfix_agent*", "dao_harness*"]` → `include = ["dao_harness*"]`
- V5関連코멘트삭제

### Phase 4: docs/ARCHITECTURE.md 업데이트

L159-163 の"V6 → V7 移행"섹션를, 이동완료를反映한기술에업데이트.

### Phase 5: README.md 신규생성

V7 dao_harness ベース의 내용로書き換え.이하를 포함:
- 프로젝트개요(dao_harness의 역할)
- 3계층아키텍처의간결한 설명
- 세트업절차
- CLI엔트리 포인트는미구현때문, 기동방법섹션는設け없다(별Issue대응)
- 개발워크플로우(`/issue-create` ~ `/issue-close`)
- 품질 체크명령어
- 문서링크목록
- `legacy/` 의 설명(V5/V6참조용)
- README 모두에"V7 (dao_harness) 이 현재의정규엔트리 포인트이며, `legacy/` 는 참조전용로비지원"を明記한다
- README 의 상세는 `docs/ARCHITECTURE.md` 및 `docs/dev/*` 에 위임し, 과잉한 상세화를避ける

### Phase 6: 검증

- `ruff check dao_harness/ tests/ && ruff format --check dao_harness/ tests/ && mypy dao_harness/ && pytest` 이 전경로
- `dao_harness/` 과 `tests/` 부터 `bugfix_agent` 로의 import 이 존재하지 않는다것을 grep 로 확인

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.

### Small 테스트
- V7테스트(`tests/` 에 남다테스트전건)이전경로한다것(純粋な로직·밸리데이션·매핑의검증)
- V5테스트이동후에 `pytest` 의 테스트수집로에러이발생하지 않는다것(import실패등)
- `grep -r "from bugfix_agent\|import bugfix_agent" dao_harness/ tests/` が0건이다것(의존격리의 검증)

### Medium 테스트
- V7테스트의うち, 파일I/Oを伴う테스트(워크플로우YAML읽기·상태영속화등)이정상경로한다것(파일I/O결합의검증)
- `legacy/` 디렉토리内의 파일이 `pyproject.toml` 의 패키지탐색대상에含まれ없다것을, setuptools 의 `find_packages` 결과로검증(패키지구성의결합검증)

### Large 테스트
- 서브프로세스로 `pip install -e ".[dev]"` 를 실행し, 설치후에 `import bugfix_agent` 이 `ModuleNotFoundError` 에 된다것을검증(패키지배포境界의 E2E검증)
- 서브프로세스로 `pytest --collect-only tests/` 를 실행し, 수집에러(ImportError등)이0건이다것을검증(테스트기반의E2E疎通)

### 스킵한다サイズ(該当하는 경우만)
- 없음

### 검증절차(테스트외)
이하는테스트サイズ분류이 아니라, Phase 6 의 품질 게이트로서실시한다정적해석:
- `ruff check dao_harness/ tests/ && ruff format --check dao_harness/ tests/`
- `mypy dao_harness/`

## 영향문서

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 없음 | ADRは歴史기록.변경불필요 |
| docs/ARCHITECTURE.md | 있음 | V6→V7移행섹션의기술업데이트 |
| docs/dev/ | 없음 | V7용가이드, 변경불필요 |
| docs/cli-guides/ | 없음 | CLI사양에변경없음 |
| CLAUDE.md | 없음 | 규약변경없음 |
| README.md | 있음 | V7ベース로 전面書き換え |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| ADR-003: CLI스킬하네스로의전환 | `docs/adr/003-skill-harness-architecture.md` | V6→V7移행의意思결정기록."bugfix_agent/ 는 참조용아카이브.保守·기능추가의대상外" |
| V7아키텍처 | `docs/ARCHITECTURE.md` | L161-163: "V7안정後にbugfix_agent/를 삭제予定"→ 今회legacy/로의이동로실시 |
| Issue #57 | `https://github.com/apokamo/dev-agent-orchestra/issues/57` | V7구현완료·머지완료의 기록 |
| V5테스트의import분석 | `grep -r "from bugfix_agent" tests/` | conftest.py, test_handlers.py, test_issue_provider.py, test_prompts.py, utils/ がV5의존.V7테스트는모두dao_harness import만 |
| pyproject.toml 엔트리 포인트확인 | `pyproject.toml` L30付近 | `[project.scripts]` 이 코멘트아웃완료.`dao` 명령어는미정의.CLI는 `python -m dao_harness` 経由로 기동 |
| 테스트 규약 | `docs/dev/testing-convention.md` | S=외부의존없음純粋로직, M=파일I/O·DB·내부서비스결합, L=実API·E2E·외부서비스疎通 |
