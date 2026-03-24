# Architecture: kuku_harness (V7)

**Version**: 7.0.0
**Last Updated**: 2026-03-09
**ADR**: [ADR 003: CLI 스킬 하네스로의 전환](adr/003-skill-harness-architecture.md)

---

## 개요

**kuku_harness**는 Claude Code / Codex / Gemini CLI의 스킬을 워크플로우 YAML에 따라 실행하는 경량 하네스.

```
┌─────────────────────────────────────────────────┐
│  하네스 (kuku_harness/)                           │
│  워크플로우 YAML을 해석하여 CLI를 순차 호출      │
├─────────────────────────────────────────────────┤
│  스킬 (.claude/skills/, .agents/skills/)         │
│  각 스텝의 실제 작업 프롬프트. CLI가 로드        │
├─────────────────────────────────────────────────┤
│  CLI (Claude Code / Codex / Gemini)              │
│  스킬을 로드하여 프로젝트 컨텍스트에서 실행           │
└─────────────────────────────────────────────────┘
```

**설계 원칙**: 하네스는 "무엇을 어떤 순서로 실행할지"만 제어한다. 스킬 로드·프로젝트 문서 참조·도구 호출은 CLI에 위임.

---

## 3계층 아키텍처

### Layer 1: 워크플로우 정의 (YAML)

`workflows/*.yaml`에 선언적으로 기술. 스텝·전이 조건·사이클·execution policy를 정의한다.

참고: [워크플로우 정의 매뉴얼](dev/workflow-authoring.md)

### Layer 2: 스킬 입출력 계약

하네스와 스킬 간의 인터페이스.

- **입력**: 하네스가 프롬프트에 주입하는 컨텍스트 변수 (issue_number, step_id, previous_verdict 등)
- **출력**: verdict 블록 (`---VERDICT---` / `---END_VERDICT---`로 감싼 YAML). strict한 출력 계약이며, 하네스 측의 폴백은 후술하는 "Verdict 판정 기구"를 참조

참고: [스킬 작성 매뉴얼](dev/skill-authoring.md)

### Layer 3: 스킬 본체

`.kuku/config.toml`의 `paths.skill_dir`로 설정된 캐노니컬 디렉토리 하위의 `<name>/SKILL.md`. CLI가 `cwd=workdir`로 실행할 때 네이티브로 로드된다. 다른 에이전트용 디렉토리 (예: `.agents/skills/`)는 캐노니컬 디렉토리로의 심볼릭 링크로 구성한다.

---

## 패키지 구성

```
kuku_harness/
  __init__.py
  config.py       # .kuku/config.toml 탐색·파싱 (kukuConfig, PathsConfig, ExecutionConfig)
  models.py       # 데이터 클래스: Workflow, Step, CycleDefinition, Verdict, CLIResult
  errors.py       # 에러 계층 (13클래스, ConfigNotFoundError 포함)
  workflow.py     # YAML 파서 & 밸리데이터
  verdict.py      # Verdict 파서 (3단계 폴백)
  adapters.py     # CLI 이벤트 어댑터 (Claude/Codex/Gemini)
  cli.py          # CLI 인수 구축 & 서브프로세스 실행
  prompt.py       # 프롬프트 빌더
  skill.py        # 스킬 존재 확인 & 패스 트래버설 방어 (config.paths.skill_dir 기반)
  state.py        # 세션 상태 영속화 (artifacts_dir 기반)
  logger.py       # JSONL 구조화 로그
  runner.py       # WorkflowRunner (자동 전이·사이클 관리)
```

---

## 데이터 흐름

```
WorkflowRunner.run()
  │
  ├─ validate_workflow(workflow)         # 정적 밸리데이션
  │
  ├─ SessionState.load_or_create()      # issue 단위 상태를 로드
  │
  └─ while current_step != "end":
       │
       ├─ build_prompt(step, state)     # 컨텍스트 변수를 주입
       │
       ├─ execute_cli(step, prompt)     # CLI를 서브프로세스로 실행
       │   └─ CLIEventAdapter           # stream-json → text/session_id/cost로 변환
       │
       ├─ parse_verdict(output)         # 3단계 폴백으로 verdict를 추출
       │   ├─ Step 1: Strict Parse     # 엄밀한 delimiter + YAML
       │   ├─ Step 2: Relaxed Parse    # 흔들림 허용 delimiter + KV 패턴
       │   └─ Step 3: AI Formatter     # 에이전트 재정형 → 재파싱
       │
       ├─ state.record_step()           # 상태를 영속화
       │
       └─ next_step = step.on[verdict]  # 전이처를 결정
```

---

## Verdict 판정 기구

에이전트 출력에서 verdict를 추출하는 3단계 폴백. V5/V6의 운용 지식에 기반한 설계이며, V7에서 복원 (#77).

### 폴백 전략

```
parse_verdict(output, valid_statuses, ai_formatter)
  │
  ├─ Step 1: Strict Parse
  │   └─ ---VERDICT--- / ---END_VERDICT--- 엄밀 일치 + YAML 파싱
  │
  ├─ Step 2a: Relaxed Delimiter + YAML
  │   └─ 대문자 소문자·공백·언더스코어 흔들림을 허용한 delimiter + YAML 파싱
  │
  ├─ Step 2b: Key-Value Pattern Extraction
  │   └─ delimiter 없는 KV 형식 (Result: PASS, Status: PASS, 스테이터스: PASS 등)
  │   └─ status는 valid_statuses로 동적 제약 (오검출 방지)
  │   └─ reason + evidence가 둘 다 확보되지 않으면 Step 3으로
  │
  └─ Step 3: AI Formatter Retry (ai_formatter 제공 시에만)
      └─ raw output을 8000자로 head+tail 절단
      └─ 에이전트 CLI로 정규 포맷으로 재정형
      └─ 재정형 결과를 Step 1 → 2a → 2b로 재파싱
      └─ 최대 2회 리트라이 (각 리트라이마다 에이전트 API 비용 발생)
```

runner는 step마다 `create_verdict_formatter(agent, valid_statuses, model, workdir)`로 formatter를 생성하고, `parse_verdict()`에 전달한다. formatter는 동일한 에이전트 CLI를 plain text 모드로 기동한다.

통상의 well-formed 출력은 Step 1-2에서 처리되며, Step 3이 기동되는 것은 delimiter / KV 복구로도 처리할 수 없는 경우에 한정된다. 추가 API 비용과 지연은 항상 발생하는 것이 아니라, 이 최종 수단에 도달했을 때만 발생한다.

### 출력 수집을 포함한 판정 경로

Verdict 판정 기구는 parser 단체가 아니라, `full_output`을 조립하는 수집층까지 포함하여 성립한다.

- `stream_and_log()`는 JSONL의 decode에 실패한 행도 버리지 않고, plain text로서 `full_output`에 보유한다
- `CodexAdapter`는 `agent_message` / `reasoning`에 더해 `mcp_tool_call`의 `result.content[].text`에서도 텍스트를 추출한다
- `parse_verdict()`는 이 수집된 `full_output`을 입력으로 하여 비로소 strict / relaxed / formatter retry를 적용할 수 있다

이 전제가 필요한 이유는, Codex `mcp_tool_call` 모드에서는 verdict가 비 JSON 텍스트나 `result.content` 측에 나타날 수 있기 때문. parser만 강화해도, 수집 단계에서 verdict 텍스트를 누락하면 복구할 수 없다.

### parser와 runner의 책임 분리

`parse_verdict()`의 책임은 `output`에서 `Verdict` dataclass를 추출하고 타당성을 검증하는 것. `ABORT`도 parse 가능한 status 중 하나이며, parser 자체는 워크플로우 종료를 결정하지 않는다.

종료 판정과 전이 결정은 runner 측의 책임이며, `verdict.status`를 `step.on`에 대입하여 다음 스텝을 선택하고, 최종적으로 `ABORT`를 workflow end status에 반영한다.

### Relaxed Parse의 허용 패턴

Step 2에서 복구 대상으로 하는 대표적인 출력 흔들림 목록.

**Delimiter 흔들림 (Step 2a):**

| 패턴 | 예 |
|----------|-----|
| 언더스코어 → 스페이스 | `---END VERDICT---` (#73에서 발생) |
| 대문자 소문자 혼재 | `---verdict---`, `---Verdict---` |
| 전후 여분의 공백 | `--- VERDICT ---` |

**KV 패턴 흔들림 (Step 2b):**

| 패턴 | 예 |
|----------|-----|
| `Result:` / `Status:` | `- Result: PASS` |
| Markdown 볼드 | `**Status**: PASS` |
| 등호 구분 | `Status = PASS`, `Result = ABORT` |
| 한국어 키 | `스테이터스: PASS` |

### 실패 경계 (폴백 대상 외)

이하는 포맷 흔들림이 아니라 의미적 오류이며, 폴백으로 복구해서는 안 된다.

- **`InvalidVerdictValue` (미정의 status 값)**: 즉시 실패. 전 단계 공통. `valid_statuses` 이외의 값은 prompt 위반
- **`ABORT`/`BACK` verdict의 suggestion 빈칸**: 즉시 실패. 다음 스텝으로의 정보가 누락되어 있기 때문

### 왜 strict parse만으로는 불충분한가

이하는 드문 엣지 케이스가 아니라 통상 운용에서 빈발한다. strict parse만으로는 workflow가 불안정해진다.

- `---END VERDICT---` (언더스코어 → 스페이스, #73에서 발생)
- `Result: PASS` / `Status: PASS` (delimiter 없는 KV 형식)
- verdict 블록 전후에 사고 트레이스·로그가 혼입
- Codex `mcp_tool_call` 모드에서의 비 JSON 텍스트 혼재

V6→V7 이전 시 이 구조를 strict parse만으로 단순화한 결과, #73에서 workflow 전체가 정지했다. 이 경위가 복원의 직접적인 이유.

### Troubleshooting

Verdict 해석에 실패한 경우, 먼저 parser가 아니라 수집된 출력의 누락 여부부터 확인한다.

- `stdout.log`: 원시 CLI 출력. verdict 블록이나 `Result:` / `Status:`, 비 JSON 행 유래 텍스트가 실제로 나와 있는지 확인
- `console.log`: adapter가 decode / extract할 수 있었던 텍스트와 비 JSON 행 양쪽을 포함하는 사람이 읽을 수 있는 출력. `full_output`과 동등한 내용
- `stderr.log`: CLI 자체의 에러 출력. formatter subprocess나 본체 CLI의 실패 구분에 사용
- `run.log`: workflow 전체의 실행 로그. `VerdictNotFound` / `VerdictParseError` / `InvalidVerdictValue` 중 어느 것으로 떨어졌는지 확인

---

## 세션 관리와 재개

**session-state.json** (`<artifacts_dir>/<issue>/session-state.json`):

- `artifacts_dir`는 `.kuku/config.toml`의 `paths.artifacts_dir` (기본값: `~/.kuku/artifacts`)로 결정
- issue 단위로 1파일. 크래시 후 재개 기반
- `session_id`: CLI resume용 세션 ID를 스텝마다 저장
- `cycle_counts`: 사이클의 이터레이션 수
- `step_history`: 스텝 실행 이력과 verdict

**재개 명령어**:

```bash
kuku run workflows/feature-development.yaml 57 --from fix-code
```

`--from`으로 지정한 스텝부터 재개하고, `session-state.json`의 `session_id`를 사용하여 CLI 세션을 복원한다.

---

## CLI 대응 매트릭스

| 기능 | Claude Code | Codex | Gemini |
|------|-------------|-------|--------|
| 비인터랙티브 실행 | `-p` | `exec --json` | `-p` |
| 스트리밍 | `--output-format stream-json --verbose` | `--json` | `-o stream-json` |
| 세션 resume | `--resume <session_id>` | `resume <thread_id>` | `--resume <session_id>` |
| 승인 바이패스 (auto) | `--permission-mode bypassPermissions` | `--dangerously-bypass-approvals-and-sandbox` | `--approval-mode yolo` |
| 모델 지정 | `--model` | `-m` | `--model` |

---

## 에러 계층

```
HarnessError
├── WorkflowValidationError    # YAML 정의 에러
├── MissingResumeSessionError  # resume 대상 세션 없음
├── InvalidTransition          # 미정의 verdict 전이
├── VerdictNotFound            # verdict 블록 없음
├── VerdictParseError          # verdict YAML 해석 에러
├── InvalidVerdictValue        # 미정의 verdict 값
├── ConfigNotFoundError         # .kuku/config.toml을 찾을 수 없음
├── CLINotFoundError           # CLI 명령어를 찾을 수 없음
├── CLIExecutionError          # CLI 실행 에러
├── StepTimeoutError           # 타임아웃
├── SkillNotFoundError         # 스킬 파일 없음
├── PathTraversalError         # 패스 트래버설 방어
└── CycleLimitExhausted        # 사이클 상한 도달
```

---

## 기억 구조

| 층 | 매체 | 용도 | 수명 |
|---|------|------|------|
| 단기 | CLI resume 세션 | 동일 agent 내 컨텍스트 계속 | 세션 내 |
| 중기 | `session-state.json`, run 로그 | 상태 확인·`--from` 재실행 | 워크플로우 실행 중 |
| 장기 | GitHub Issue (본문·코멘트) | agent 간·세션 간 지식 공유 | 영속 |

---

## V6 → V7 이전

- V5/V6 파일은 `legacy/`로 이동 완료 (#59에서 실시)

---

## 관련 문서

| 문서 | 내용 |
|-------------|------|
| [ADR 003](adr/003-skill-harness-architecture.md) | 아키텍처 결정 기록 |
| [워크플로우 정의 매뉴얼](dev/workflow-authoring.md) | YAML 정의 작성법 |
| [스킬 작성 매뉴얼](dev/skill-authoring.md) | 스킬 작성법·verdict 규약 |
| [테스트 규약](dev/testing-convention.md) | S/M/L 테스트 사이즈 정의 |
| [워크플로우 가이드](dev/workflow_guide.md) | 워크플로우 선택 기준·개요 |
| [Claude Code CLI 가이드](cli-guides/claude-code-cli-guide.md) | claude 명령어 사양 |
| [Codex CLI 가이드](cli-guides/codex-cli-session-guide.md) | codex 명령어 사양 |
| [Gemini CLI 가이드](cli-guides/gemini-cli-session-guide.md) | gemini 명령어 사양 |
