# [설계] 스킬실행하네스로의아키텍처전환

Issue: #57

## 개요

현행의 Python 상태マシン오케스트레이터(`bugfix_agent/`)를폐지し, Claude Code / Codex / Gemini CLI 의 스킬를워크플로우정의에 따라실행한다경량하네스에전환한다.

## 배경·목적

### 현행아키텍처의과제

1. **네이티브기능의재구현**: State machine, Verdict parsing, Tool abstraction, CLI streaming — 이것들는 Claude Code / Codex 의 스킬機構이 네이티브로제공한다기능를 Python(約2000 LOC)로再구현하고 있다
2. **프로젝트 컨텍스트의단절**: 외부오케스트레이터부터각 프로젝트 의 문서·コーディング규약·테스트 규약를 참조할 수 없다프로젝트J 内의 스킬로서 CLI 이 실행されれば, 스킬이필요한 프로젝트밍로 PJ 의 문서(コーディング규약, 테스트 규약, 설계템플릿등)를 Read 도구로 단계적으로 読み込める.이것는 외부오케스트레이터부터프로젝트가능이며, 스킬이 PJ 의 문서ツリー에 접근할 수 있다位置로 실행된다것이전제와된다
3. **保守코스트**: CLI 의 버전업(Claude v2.0→v2.1, Codex v0.63→v0.112, Gemini v0.18→v0.31)로의追従이 Tool abstraction 계층로困難

### 신아키텍처의방침

> **설계근거**: 본설계는 Anthropic"[Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)"のベストプラクティス에 기반한.
> 하네스는전이제어만, 스킬이実작업, GitHub Issue が長期記憶 — 이분리는同記事の"Initializer + Coding Agent"패턴및"구조화アーティファクト에 의한세션간상태관리"와 같은설계思想.

- **스킬는 CLI 이 네이티브로로드**: `.claude/skills/` 와 `.agents/skills/` 에 배치된스킬는, 각 CLI 이 `cwd=workdir` 로 실행된다際에 자동적으로 시스템컨텍스트로서読み込まれる.**하네스는스킬파일의내용를読み込ま없다**.하네스의프롬프트는스킬명를 참조한다만로, 스킬본체의로드는 CLI 에 위임한다
- **단계적開示(Progressive Disclosure)**: CLAUDE.md / AGENTS.md 는 라우팅정보(스킬목록, 워크플로우명, 품질 체크명령어등)만에留め, 경량에保つ.コーディング규약·테스트 규약·설계템플릿등의상세규칙는, 각스킬이실행시에 Read 도구로 필요한 문서만를읽어들이는.이것에 의해컨텍스트ウィンドウを節約し, 각스텝로関連정보만이로드된다
- **하네스는"무엇을어떤순로 실행한다か"만를 제어**: 워크플로우정의(YAML)를해석し, CLI 를 외부호출(방식 A)하여스킬를순차실행한다.1스텝1関心事의 분割에 의해, 에이전트이過大な태스크를一度에 실행한다傾向(over-ambitious execution)를구조적으로 방지한다
- **3계층의記憶구조**:

| 계층 | 媒体 | 용도 | 寿命 |
|---|------|------|------|
| 短期 | CLI resume 세션 | 동일 agent 内의 컨텍스트계속 | 세션内 |
| 中期 | `progress.md` / `session-state.json` | 로컬상태확인·`--from` 再실행 | 워크플로우실행中 |
| 長期 | GitHub Issue(本文업데이트 + 코멘트) | agent 間·세션間의 지식공유 | 영속 |

 - **短期**: CLI 의 resume 기능에 위임.동일 agent 内는 세션계속, 리뷰등는의도적으로 세션절단
 - **中期**: 하네스이스텝완료마다에자동업데이트.人間의 상태확인나 이상종료後の再실행에사용
 - **長期**: 스킬이 Issue 本文업데이트 + 코멘트로작업성과·판정결과를기록.次세션시작時에 스킬이 Issue を読んで現状を把握한다(Anthropic の"progress file"패턴에 해당)

- **이상종료시는 `--from` で再실행**: 하네스의クラッシュ時는 SessionState(스텝완료마다에영속화)를基に, 도중의스텝부터수동로재실행한다.자동リカバリ는 구현하지 않는다
- **스킬·워크플로우생성매뉴얼**: AI 이 스킬나 워크플로우정의를 생성·최적화한다것을전제에, 機械가독한 사양書로서 `docs/dev/` 에 배치한다.CLAUDE.md / AGENTS.md に는 매뉴얼로의라우팅를기재하지 않는다(초기로드의경량화).스킬생성·최적화를依頼할 때에, 작업指示로 매뉴얼경로를지정한다

| 매뉴얼 | 배치선 | 내용 |
|-----------|--------|------|
| 스킬 작성 매뉴얼 | `docs/dev/skill-authoring.md` | 스킬파일구성, SKILL.md 포맷, verdict 출력규약, GitHub Issue 활용규약(섹션관리규칙, 리뷰系의 추가규칙), 추천패턴(Devil's Advocate プリアンブル, 인クリメンタル커밋등) |
| 워크플로우 정의 매뉴얼 | `docs/dev/workflow-authoring.md` | YAML 구조, 스텝필드정의, 사이클선언, verdict 전이설계, CLI 플래그매핑 |

## 인터페이스

### 입력

#### 1. 워크플로우정의파일(YAML)

```yaml
# workflows/feature-development.yaml
name: feature-development
description: "설계→리뷰→구현→리뷰→PR 의 표준플로우"
execution_policy: auto # auto / sandbox / interactive

# 사이클선언 — ループ구조를明示し, 정적검증의대상에한다
cycles:
 design-review:
 entry: review-design # 사이클의入口(初회리뷰)
 loop: [fix-design, verify-design] # RETRY 시의ループ(fix → verify → fix → ...)
 max_iterations: 3 # fix→verify を1イテレーション로서カウント
 on_exhaust: ABORT # 상한도달시의 verdict

 code-review:
 entry: review-code
 loop: [fix-code, verify-code]
 max_iterations: 3
 on_exhaust: ABORT

# 스텝정의 — フラット로 전이이명시적
steps:
 - id: design
 skill: issue-design
 agent: claude
 model: sonnet
 effort: high
 max_turns: 50
 resume: null
 on:
 PASS: review-design # → design-review 사이클へ
 ABORT: end

 - id: review-design
 skill: issue-review-design
 agent: codex
 effort: high
 resume: null # 컨텍스트절단
 on:
 PASS: implement # 사이클脱出
 RETRY: fix-design # 사이클内ループへ
 ABORT: end

 - id: fix-design
 skill: issue-fix-design
 agent: claude
 effort: high
 resume: design # design 세션를계속
 on:
 PASS: verify-design
 ABORT: end

 - id: verify-design
 skill: issue-verify-design
 agent: codex
 effort: high
 resume: null # 컨텍스트절단
 on:
 PASS: implement # 사이클脱出
 RETRY: fix-design # ループ계속

 - id: implement
 skill: issue-implement
 agent: claude
 model: opus
 effort: high
 max_budget_usd: 5.0
 max_turns: 80
 resume: null
 on:
 PASS: review-code # → code-review 사이클へ
 ABORT: end

 - id: review-code
 skill: issue-review-code
 agent: codex
 effort: high
 resume: null
 on:
 PASS: doc-check # 사이클脱出
 RETRY: fix-code # 사이클内ループへ
 BACK: design # 설계페이즈へ差し戻し
 ABORT: end

 - id: fix-code
 skill: issue-fix-code
 agent: claude
 effort: high
 max_turns: 50
 resume: implement
 on:
 PASS: verify-code
 ABORT: end

 - id: verify-code
 skill: issue-verify-code
 agent: codex
 effort: high
 resume: null
 on:
 PASS: doc-check # 사이클脱出
 RETRY: fix-code # ループ계속

 - id: doc-check
 skill: issue-doc-check
 agent: claude
 resume: implement
 on:
 PASS: pr
 ABORT: end

 - id: pr
 skill: issue-pr
 agent: claude
 resume: implement
 on:
 PASS: end
 ABORT: end
```

#### 워크플로우정의의구조

| 섹션 | 역할 |
|-----------|------|
| `cycles` | ループ구조의선언.어떤스텝이사이클를구성한다인가, 상한회수, 상한도달시의挙動를 정의 |
| `steps` | フラットな스텝정의.각스텝의전이는 `on` 로 명시적에기술 |

#### 스텝의필드

| 필드 | 필수 | 타입 | 설명 |
|-----------|------|-----|------|
| `id` | Yes | str | 스텝識별子(一意) |
| `skill` | Yes | str | 실행한다스킬명 |
| `agent` | Yes | str | `claude` / `codex` / `gemini` |
| `model` | No | str | 모델지정.생략時는 에이전트의기본값 |
| `effort` | No | str | `low` / `medium` / `high`.생략時는 에이전트의기본값 |
| `max_budget_usd` | No | float | API비용상한.Claude Code 만유효, 他は無視 |
| `max_turns` | No | int | 도구호출회수상한.Claude Code 만유효, 他は無視 |
| `timeout` | No | int | 스텝의타임아웃초수.생략時는 기본값(1800s) |
| `resume` | No | str\|null | 세션계속원의 step id.null = 신규세션 |
| `on` | Yes | dict | verdict → 전이선매핑 |

#### 실행ポリシー(execution_policy)

워크플로우정의의탑레벨로 지정.전스텝에적용된다:

```yaml
execution_policy: auto # auto / sandbox / interactive
```

| ポリシー | 설명 | Claude Code | Codex | Gemini |
|---------|------|-------------|-------|--------|
| `auto` | 전승인를자동화(기본값) | `--permission-mode bypassPermissions` | `--dangerously-bypass-approvals-and-sandbox` | `--approval-mode yolo` |
| `sandbox` | 샌드박스内로 자동 | `--permission-mode default` | `-s workspace-write` | `-s` |
| `interactive` | 승인요구있음(디버그용) | *(플래그없음)* | *(플래그없음)* | *(플래그없음)* |

> **중요**: `auto` ポリシー는 외부샌드박스환경(컨테이너등)로의 실행를전제으로 한다.
> Codex 의 `--dangerously-bypass-approvals-and-sandbox` 는 이름의通り위험한 플래그이며,
> 신뢰할 수 없다환경로의사용는금지.

#### CLI 플래그매핑

| 필드 | Claude Code | Codex | Gemini |
|-----------|-------------|-------|--------|
| `model` | `--model {v}` | `-m {v}` | `-m {v}` |
| `effort` | `--effort {v}` | `-c 'model_reasoning_effort="{v}"'` | *(無視)* |
| `max_budget_usd` | `--max-budget-usd {v}` | *(無視)* | *(無視)* |
| `max_turns` | `--max-turns {v}` | *(無視)* | *(無視)* |

#### 사이클선언의필드

| 필드 | 필수 | 설명 |
|-----------|------|------|
| `entry` | Yes | 사이클의入口스텝(初회리뷰) |
| `loop` | Yes | RETRY 時に繰り반환하다스텝의順序리스트 |
| `max_iterations` | Yes | ループ상한(`loop` 의 전스텝실행를1イテレーション로서カウント) |
| `on_exhaust` | Yes | 상한도달時に発행한다 verdict(`ABORT` 추천) |

#### 판정(verdict)의 책무境界

| 책무 | 담당 | 설명 |
|------|------|------|
| verdict の**생성** | 스킬 | `---VERDICT---` 블록를출력 |
| verdict の**파싱** | 하네스 | 텍스트부터 status / reason / evidence / suggestion 를 추출 |
| verdict 에 기반한**전이** | 하네스 | `on` 필드에 따라次스텝를결정 |
| verdict の**의미정의** | 워크플로우정의 | `PASS`=次へ, `RETRY`=ループ, `BACK`=前페이즈へ戻る, `ABORT`=중단 |
| イテレーション**상한판정** | 하네스 | `cycles` 의 `max_iterations` 와 대조 |

#### 2. CLI 실행인수

```bash
dao run --workflow feature-development --issue 123 [--from design] [--step review-code]
```

| 인수 | 필수 | 설명 |
|------|------|------|
| `--workflow` | Yes | 워크플로우정의명(`workflows/` 内의 파일명) |
| `--issue` | Yes | GitHub Issue 번호 |
| `--from` | No | 지정스텝부터시작(도중재개용) |
| `--step` | No | 단일스텝만실행 |
| `--dry-run` | No | 실행せず워크플로우의전이를표시 |

### 출력

- **세션상태파일**: `test-artifacts/<issue>/session-state.json` — issue-scoped 한 stable state.세션 ID·verdict 履歴·사이클カウント·`last_transition_verdict` 를 보유(스텝완료마다에업데이트)
- **진척파일**: `test-artifacts/<issue>/progress.md` — 사람이 읽을 수 있는한 진척목록(스텝완료마다에자동업데이트)
- **각실행의 run 로그**: `test-artifacts/<issue>/runs/<timestamp>/` 에 JSONL 형식로저장
- **GitHub Issue 코멘트**: 각스텝완료時에 스킬이 Issue 에 코멘트(하네스이 아니라스킬側의 책무)

### 사용예

```python
# プ로그ラム적 이용
from dao_harness import WorkflowRunner

runner = WorkflowRunner(
 workflow="feature-development",
 issue_number=123,
 workdir="/home/aki/dev/kamo2-feat-123",
)
result = runner.run()
print(result.final_verdict) # PASS or ABORT
print(result.completed_steps) # ["design", "review-design", "implement", ...]
```

## 제약·전제 조건

### 기술적제약

1. **CLI 의 비인터랙티브모드의존**: Claude Code 는 `-p`, Codex 는 `exec`, Gemini 는 `-p` 로 비인터랙티브실행
2. **세션 resume 는 동일 agent 内만**: Claude → Codex 間의 세션인수인계는불가능.agent を跨いだ `resume` 지정는워크플로우정의의밸리데이션時에 에러으로 한다
3. **JSON 출력의 CLI 차이**: 각 CLI 의 JSON 출력포맷이다르다(후술의출력파서로吸収)

| CLI | 비인터랙티브 | 스트리밍출력 | resume 時 JSON | 세션 ID 취득 | 자동승인 |
|-----|-------------------|-------------------|---------------|-------------------|---------|
| Claude Code v2.1+ | `-p` | `--output-format stream-json --verbose` | 가능 | `session_id` 필드 | `--permission-mode bypassPermissions` |
| Codex v0.112+ | `exec` | `--json`(기본값로 JSONL 스트림) | **가능**(v0.112 로 해소) | `thread.started` → `thread_id` | `--dangerously-bypass-approvals-and-sandbox` |
| Gemini v0.31+ | `-p` | `-o stream-json` | 가능 | `init` → `session_id` | `--approval-mode yolo` |

4. **Gemini 의 `--allowed-tools` 비추천**: v0.30.0+ 로 는 Policy Engine(TOML)이추천.当面はレガシー의 `--allowed-tools` も사용가능
5. **스킬의배치선이 CLI 에 의해다르다**: 동일스킬내용(YAML frontmatter + Markdown)를, CLI 마다에다르다디렉토리에배치한다필요이 있다

| CLI | 스킬배치선 | 파일 |
|-----|------------|---------|
| Claude Code | `.claude/skills/<skill-name>/` | `SKILL.md` |
| Codex / Gemini | `.agents/skills/<skill-name>/` | `SKILL.md` |

하네스는 CLI 기동前에 스킬파일의존재를 검증한다(pre-flight check).**스킬의내용는読み込ま없다** — CLI 이 `cwd=workdir` 로 실행된다際에 네이티브로로드한다:

```python
SKILL_DIRS = {
 "claude": ".claude/skills",
 "codex": ".agents/skills",
 "gemini": ".agents/skills",
}

def validate_skill_exists(skill_name: str, agent: str, workdir: Path) -> None:
 """CLI 기동전의 스킬존재확인(pre-flight check).
 스킬내용는 CLI 이 네이티브로로드한다때문에, 하네스는読み込ま없다."""
 base = workdir / SKILL_DIRS[agent] / skill_name / "SKILL.md"
 # 경로트래버설방어
 resolved = base.resolve()
 if not resolved.is_relative_to(workdir.resolve()):
 raise SecurityError(f"Skill path escapes workdir: {resolved}")
 if not resolved.exists():
 raise SkillNotFound(f"{base} not found")
```

6. **타임아웃·프로세스관리**: 각스텝에타임아웃(기본값 1800s)를설정.타임아웃時는 프로세스를 SIGTERM → 猶予後 SIGKILL 로 강제종료.타임아웃検出는 `threading.Event` 로 메인스레드에통지し, 메인스레드로 `StepTimeoutError` 를 raise 한다
7. **verdict 블록내는 YAML 형식**: `yaml.safe_load()` 로 파싱.`evidence` / `suggestion` 의 복수행기술(YAML block scalar `|`)에대응.PyYAML 는 기존의존(`pyyaml`)

### ビジネス제약

1. **기존의워크플로우호환性**: 현행의 `/issue-create` → `/issue-close` 의 스킬체인를변경せず에 하네스로자동화할 수 있다것
2. **단계적移행**: 기존의 `bugfix_agent/` を即座에 삭제せず, V7 구현완료까지참조가능한 상태를유지한다.V6 は**移행기간中의 참조용아카이브**이며, 保守·기능추가의대상이 아니다

### 移행전략(V6 → V7)

スクラップ빌드방식로 V7.0 로서刷新한다.現状를 `v6.0` 태그로저장し, `dao_harness/` 를 신규생성:

```bash
# 1. 現状를 태그로저장(참조용)
git tag v6.0

# 2. 신패키지를 생성(bugfix_agent/ 는 참조용로서보유)
mkdir -p dao_harness/

# 3. V7 완료후에 bugfix_agent/ 를 삭제
```

#### 리포지토리구성의변경

| 대상 | V7 での扱い | 이유 |
|------|------------|------|
| `bugfix_agent/` | `dao_harness/` 에 치환(V7완료후삭제) | スクラップ빌드대상 |
| `pyproject.toml` | 패키지名·엔트리 포인트변경 | `dao_harness` 로 |
| `CLAUDE.md` | 업데이트(Essential Commands, 경로변경) | 신패키지에合わせる |
| `docs/ARCHITECTURE.md` | 전面개정 | 하네스아키텍처 |
| `docs/dev/development_workflow.md` | 업데이트 | 하네스経由의 자동실행플로우追記 |
| `docs/dev/skill-authoring.md` | **신규생성** | 스킬 작성 매뉴얼 |
| `docs/dev/workflow-authoring.md` | **신규생성** | 워크플로우 정의 매뉴얼 |
| `docs/cli-guides/` | 그まま유지 | 최신화완료 |
| `docs/dev/testing-convention.md` | 그まま유지 | 변경없음 |
| `docs/guides/` | 그まま유지 | git worktree 등는공통 |
| `docs/adr/` | 유지 + V7 ADR 추가 | 履歴저장 |

> **참조방법**: V6 의 코드를 참조하는 경우는 `git show v6.0:bugfix_agent/verdict.py` 등로即座에 접근가능.V6 폴더로의物理이동는행わ없다.

### 에러 계층

현행오케스트레이터의5種에러클래스를상속·再編:

```python
class HarnessError(Exception):
 """하네스의 기저예외."""

# --- 워크플로우정의에러(기동時に検出) ---
class WorkflowValidationError(HarnessError):
 """워크플로우 YAML 의 정적검증에러."""

# --- 스킬해결에러 ---
class SkillNotFound(HarnessError):
 """스킬파일를 찾를 찾을 수 없다."""

class SecurityError(HarnessError):
 """경로트래버설등의보안위반."""

# --- CLI 실행에러 ---
class CLIExecutionError(HarnessError):
 """CLI 프로세스이 비정상종료."""
 def __init__(self, step_id: str, returncode: int, stderr: str): ...

class CLINotFoundError(HarnessError):
 """CLI 명령어를 찾를 찾을 수 없다(FileNotFoundError 를 래핑)."""

class StepTimeoutError(HarnessError):
 """스텝이타임아웃.SIGTERM → SIGKILL 후에 raise."""
 def __init__(self, step_id: str, timeout: int): ...

class MissingResumeSessionError(HarnessError):
 """resume 지정스텝로계속원의 세션 ID 를 찾를 찾을 수 없다.
 문맥계속를サイレントに失う것을防ぐ fail-fast 에러."""
 def __init__(self, step_id: str, resume_target: str): ...

# --- Verdict 에러 ---
class VerdictNotFound(HarnessError):
 """출력에 ---VERDICT--- 블록이 없다.회復不能."""

class VerdictParseError(HarnessError):
 """필수필드欠損.회復不能."""

class InvalidVerdictValue(HarnessError):
 """on に未정의의 status 값.프롬프트위반.회復不能·리트라이하지 않는다."""

# --- 전이에러 ---
class InvalidTransition(HarnessError):
 """verdict.status 에 대응한다전이선이 on に未정의."""
```

> **現행에서의상속**: `VerdictParseError`, `InvalidVerdictValueError` 의 회復不能セマンティクスを踏襲.
> 현행의 `AgentAbortError`(ABORT verdict 시에 raise)는폐지 — 신설계로는 ABORT 는 통상의전이로서 `on` 로 처리한다.
> 현행의 `LoopLimitExceeded`(예외로중단)も폐지 — 신설계로는사이클상한도달시에 `on_exhaust` verdict を発행하여전이한다.

### 프롬프트プリアンブル(Devil's Advocate 등)

현행오케스트레이터로는리뷰系스텝에 Devil's Advocate プリアンブル를 하네스이주입하여いたが, 신설계로는스킬側의 책무으로 한다.리뷰품질를담보한다プリアンブル의 패턴는, 스킬 작성 매뉴얼에추천事項로서기재한다.

## 방침

### 3계층아키텍처

```
┌──────────────────────────────────────────────────────────┐
│ Layer 1: 워크플로우정의 (YAML) │
│ 하네스이해석한다.steps / transitions / conditions │
│ agent·model·resume 지정 │
├──────────────────────────────────────────────────────────┤
│ Layer 2: 스킬入출력계약 │
│ 하네스이주입(컨텍스트변수)·파싱(verdict)한다 │
│ Input: 컨텍스트변수 + 스킬명참조(내용는 CLI 이 읽다)│
│ Output: verdict (PASS/RETRY/BACK/ABORT) + structured fields │
├──────────────────────────────────────────────────────────┤
│ Layer 3: 스킬본체 │
│ P프로젝트고유.Claude Code / Codex / Gemini 의 형식로기술 │
│ .claude/skills/ or .agents/skills/ 에 배치 │
│ P프로젝트문서참조는自由 │
└──────────────────────────────────────────────────────────┘
```

### 스킬入출력계약(Layer 2)

하네스와스킬間の入출력규칙.현행오케스트레이터(`bugfix_agent/`)의 verdict 프로토콜를 상속·簡素화한것.

#### 입력계약(하네스 → 스킬)

하네스이프롬프트에주입한다컨텍스트변수:

| 변수 | 타입 | 필수 | 설명 |
|------|-----|------|------|
| `issue_number` | int | Yes | GitHub Issue 번호 |
| `step_id` | str | Yes | 현재의스텝 ID |
| `previous_verdict` | str | No | 현재의전이를引き起こ한 verdict(reason + evidence + suggestion).`resume` 지정스텝(= 문맥계속스텝)로만주입 |
| `cycle_count` | int | No | 현재의사이클イテレーション(1-indexed).사이클내스텝만 |
| `max_iterations` | int | No | 사이클의상한회수.사이클내스텝만 |

> **現행에서의상속**: `${loop_count}` / `${max_loop_count}` 를 `cycle_count` / `max_iterations` に改名.
> fix 系스킬이"何회目의 수정か"를 알다함으로써, Issue 本文의 기존섹션삭제→再追記를 제어할 수 있다.
>
> **`previous_verdict` 의 주입조건**: `resume` 지정스텝(문맥계속스텝)로만주입한다.
> `state.last_transition_verdict`(현재의전이를引き起こ한 verdict)를 참조한다.
> 이것에 의해 `review-design` → `fix-design`(resume: design)의 전이로리뷰 지적이正しく渡된다.
> 한편, `design` → `review-design`(resume: null)로는 주입되지 않고,
> 리뷰스텝이전단의自己평가에引っ張られる것을防ぐ.

#### 출력계약(스킬 → 하네스)

스킬는실행완료時에 이하의 verdict 블록를출력에포함하다것.블록내부는 **YAML 형식** 로 기술한다(복수행 evidence/suggestion 에 대응한다위해):

```
---VERDICT---
status: PASS | RETRY | BACK | ABORT
reason: "판정이유"
evidence: |
 구체적근거(테스트결과, 리뷰 지적, 差분등)
 복수행기술가능(YAML block scalar)
suggestion: "다음アクション提案"
---END_VERDICT---
```

| 필드 | 필수 | 설명 |
|-----------|------|------|
| `status` | Yes | 스텝의 `on` 에 정의된 verdict 값의いずれ인가 |
| `reason` | Yes | 판정이유(空문자불가) |
| `evidence` | Yes | 구체적한 근거.抽象表現금지("문제없음"이 아니라"전12테스트 PASS, 커버리지 85%") |
| `suggestion` | ABORT/BACK 시필수 | 중단·差し戻し時に次에 무엇을해야 할かの提案.PASS/RETRY 時는 임의 |

> **verdict 값의의미**:
> - `PASS`: 성공.다음스텝へ進む
> - `RETRY`: 軽微な문제.사이클内로 수정를繰り반환하다
> - `BACK`: 근본적인 문제.전의 페이즈(예: 구현→설계)へ差し戻す
> - `ABORT`: 속행不能.워크플로우를중단한다

> **現행에서의상속**: 현행의 `Result` / `Reason` / `Evidence` / `Suggestion` 4필드형식를踏襲.
> `Result` → `status` に改名(워크플로우정의의 `on` 키와직접대응させる위해).

#### 에러분류

| 에러 | 회復가능 | 설명 |
|--------|---------|------|
| **verdict 未検出** | No | 출력에 `---VERDICT---` 블록이 없다.`VerdictNotFound` 를 raise |
| **status 값부정** | No | `on` 에 정의되어 있지 않다 status 값.`InvalidVerdictValue` 를 raise(프롬프트위반를示す때문에, 리트라이하지 않는다) |
| **필드欠損** | No | 필수필드(status, reason, evidence)이欠損.`VerdictParseError` 를 raise |

> **現행에서의상속**: `InvalidVerdictValueError` 는 회復不能에러로서即座에 raise 한다설계를踏襲.
> 현행의 AI Formatter Retry(3段폴백)는딜리미터형식의채용에 의해폐지.

#### GitHub Issue 활용규약(長期記憶)

GitHub Issue 는 세션間·agent 間の長期記憶로서기능한다.스킬는이하의규약에 따라 Issue 를 조작한다것.

| 조작 | 담당 | 타이밍 | 방법 |
|------|------|-----------|------|
| **Issue 本文업데이트** | 작업系스킬 | 스텝완료시 | `gh issue edit` 로 산출물섹션를追記 |
| **Issue 코멘트** | 리뷰系스킬 | verdict 확정시 | `gh issue comment` 로 verdict + 체크리스트를投稿 |
| **Issue 읽기** | 전스킬 | 세션시작시 | `gh issue view` で現状を把握 |

**섹션관리규칙**:

- **cycle_count=1(初회)**: Issue 本文말미에섹션를追記
- **cycle_count>=2(再실행)**: 기존의同名섹션를삭제하여부터말미에再追記
- 스킬는 `cycle_count` 컨텍스트변수를 참조하여동작를전환る

**리뷰系스킬의추가규칙**:

- PASS 시만 Issue 本文에 리뷰결과를反映
- RETRY/BACK 時는 코멘트만(本文는 업데이트하지 않는다)

> 상세한 섹션구성·포맷는스킬 작성 매뉴얼에기재.

### 하네스의메인ループ(疑似코드)

```python
def run_workflow(workflow: Workflow, issue: int, workdir: Path,
 from_step: str | None = None,
 single_step: str | None = None,
 verbose: bool = True):
 execution_policy = workflow.execution_policy or "auto"

 # 0. 전스텝의스킬존재를사전 검증(pre-flight)
 for step in workflow.steps:
 validate_skill_exists(step.skill, step.agent, workdir)

 # 1. issue-scoped な상태를 로드또는신규생성
 state = SessionState.load_or_create(issue)

 # 2. run 로그는실행마다에타임스탬프별디렉토리
 run_dir = Path(f"test-artifacts/{issue}/runs/{datetime.now().strftime('%y%m%d%H%M')}")
 run_dir.mkdir(parents=True, exist_ok=True)
 logger = RunLogger(run_dir / "run.log")
 logger.log_workflow_start(issue, workflow.name)

 # 3. 시작스텝의결정
 if single_step:
 # --step: 지정스텝만실행(전이せず종료)
 current_step = workflow.find_step(single_step)
 if not current_step:
 raise WorkflowValidationError(f"Step '{single_step}' not found")
 elif from_step:
 # --from: 지정스텝부터재개(이후는통상전이)
 current_step = workflow.find_step(from_step)
 if not current_step:
 raise WorkflowValidationError(f"Step '{from_step}' not found")
 # --from 時는 전단를스킵.last_transition_verdict は
 # session-state.json 부터복원완료(전회실행의결과이그まま使える)
 else:
 current_step = workflow.find_start_step()

 while current_step and current_step.id != "end":
 start_time = time.monotonic()
 cycle = workflow.find_cycle_for_step(current_step.id)

 # 3. 사이클상한체크
 if cycle and state.cycle_iterations(cycle.name) >= cycle.max_iterations:
 verdict = Verdict(status=cycle.on_exhaust,
 reason=f"Cycle '{cycle.name}' exhausted",
 evidence=f"{cycle.max_iterations} iterations reached",
 suggestion="수동로확인해 주세요")
 cost = None
 else:
 # 4. 컨텍스트변수만를 포함프롬프트를구축(스킬내용는 CLI 이 로드)
 prompt = build_prompt(current_step, issue, state, workflow)

 # 5. CLI 를 실행(스트리밍 + リアルタイム로그)
 session_id = state.get_session_id(current_step.resume) if current_step.resume else None
 # resume 지정な의 에 session_id 를 찾를 찾을 수 없다 → fail-fast
 if current_step.resume and session_id is None:
 raise MissingResumeSessionError(current_step.id, current_step.resume)
 step_log_dir = run_dir / current_step.id
 step_log_dir.mkdir(parents=True, exist_ok=True)
 logger.log_step_start(current_step.id, current_step.agent,
 current_step.model, current_step.effort, session_id)

 result = execute_cli(
 step=current_step, prompt=prompt, workdir=workdir,
 session_id=session_id, log_dir=step_log_dir,
 execution_policy=execution_policy, verbose=verbose,
 )

 # 6. 세션 ID 를 저장
 state.save_session_id(current_step.id, result.session_id)
 cost = result.cost

 # 7. verdict 를 파싱(YAML 형식)
 verdict = parse_verdict(result.full_output,
 valid_statuses=set(current_step.on.keys()))

 # 8. 로그기록 + 상태업데이트(last_transition_verdict も저장)
 duration_ms = int((time.monotonic() - start_time) * 1000)
 logger.log_step_end(current_step.id, verdict, duration_ms, cost)
 state.record_step(current_step.id, verdict)

 if cycle and current_step.id == cycle.loop[-1] and verdict.status == "RETRY":
 state.increment_cycle(cycle.name)
 logger.log_cycle_iteration(cycle.name,
 state.cycle_iterations(cycle.name),
 cycle.max_iterations)

 # 9. 다음스텝를결정
 if single_step:
 # --step 모드: 単発실행로종료
 break
 next_step_id = current_step.on.get(verdict.status)
 if next_step_id is None:
 raise InvalidTransition(current_step.id, verdict.status)
 current_step = workflow.find_step(next_step_id)

 logger.log_workflow_end("COMPLETE", state.cycle_counts,
 total_duration_ms=..., total_cost=..., error=None)
 return state
```

### CLI 실행의추상화

전 CLI 로 JSONL 스트리밍출력를統一채용し, リアルタイム로그출력를실현한다.

#### 스트리밍출력의統一

| CLI | 플래그 | 형식 | 비고 |
|-----|--------|------|------|
| Claude Code | `--output-format stream-json --verbose` | JSONL | `--verbose` 필수 |
| Codex | `--json` | JSONL | 기본값로순차출력 |
| Gemini | `-o stream-json` | JSONL | — |

#### 이벤트구조의 CLI 差분

전 CLI 이 JSONL 를 출력한다이, 이벤트의 JSON 구조는다르다.CLI 별어댑터로吸収:

| 정보 | Claude Code | Codex | Gemini |
|------|-------------|-------|--------|
| 초기화 | `{type:"system", subtype:"init", session_id}` | `{type:"thread.started", thread_id}` | `{type:"init", session_id}` |
| 텍스트응답 | `{type:"assistant", message:{content:[{text}]}}` | `{type:"item.completed", item:{type:"agent_message", text}}` | `{type:"response", response:{content:[{text}]}}` |
| 완료 | `{type:"result", result, total_cost_usd}` | `{type:"turn.completed", usage:{input_tokens,...}}` | *(최종 response)* |
| 세션ID | `session_id` | `thread_id` | `session_id` |
| 코스트 | `total_cost_usd` (USD) | `usage.input_tokens` (토큰수) | 없음 |

#### 아키텍처

```
 ┌─────────────────────────────────┐
 Popen(stdout=PIPE)│ CLI 프로세스 (JSONL출력) │
 └──────────┬──────────────────────┘
 │ 행단위읽기
 ┌──────────▼──────────────────────┐
 │ StreamProcessor (공통) │
 │ ├─ raw 로그쓰기 (即時flush) │
 │ ├─ CLI별어댑터로デ코드 │
 │ ├─ 콘솔로그쓰기 │
 │ └─ verbose: 터미널출력 │
 └──────────┬──────────────────────┘
 │ 완료후
 ┌──────────▼──────────────────────┐
 │ CLIResult │
 │ ├─ full_output: str (전텍스트) │
 │ ├─ session_id: str │
 │ ├─ cost: CostInfo | None │
 │ └─ stderr: str │
 └─────────────────────────────────┘
```

#### CLI 별어댑터(Protocol)

```python
class CLIEventAdapter(Protocol):
 """CLI 고유의 JSONL 이벤트구조를デ코드한다.공통부분는 없다."""

 def extract_session_id(self, event: dict) -> str | None:
 """초기화이벤트부터세션 ID 를 추출."""
 ...

 def extract_text(self, event: dict) -> str | None:
 """텍스트응답이벤트부터사람이 읽을 수 있는텍스트를추출."""
 ...

 def extract_cost(self, event: dict) -> CostInfo | None:
 """완료이벤트부터코스트정보를추출."""
 ...


class ClaudeAdapter:
 def extract_session_id(self, event):
 if event.get("type") == "system" and event.get("subtype") == "init":
 return event.get("session_id")
 return None

 def extract_text(self, event):
 if event.get("type") == "assistant":
 content = event.get("message", {}).get("content", [])
 return "\n".join(c["text"] for c in content if c.get("type") == "text")
 if event.get("type") == "result":
 return event.get("result")
 return None

 def extract_cost(self, event):
 if event.get("type") == "result":
 return CostInfo(usd=event.get("total_cost_usd"))
 return None


class CodexAdapter:
 def extract_session_id(self, event):
 if event.get("type") == "thread.started":
 return event.get("thread_id")
 return None

 def extract_text(self, event):
 if event.get("type") == "item.completed":
 item = event.get("item", {})
 if item.get("type") in ("agent_message", "reasoning"):
 return item.get("text")
 return None

 def extract_cost(self, event):
 if event.get("type") == "turn.completed":
 usage = event.get("usage", {})
 return CostInfo(input_tokens=usage.get("input_tokens"),
 output_tokens=usage.get("output_tokens"))
 return None


class GeminiAdapter:
 def extract_session_id(self, event):
 if event.get("type") == "init":
 return event.get("session_id")
 return None

 def extract_text(self, event):
 if event.get("type") == "response":
 content = event.get("response", {}).get("content", [])
 return "\n".join(c["text"] for c in content if c.get("type") == "text")
 return None

 def extract_cost(self, event):
 return None # Gemini 는 코스트정보없음
```

#### 스트리밍실행(공통)

```python
ADAPTERS = {"claude": ClaudeAdapter(), "codex": CodexAdapter(), "gemini": GeminiAdapter()}

DEFAULT_TIMEOUT = 1800 # 30분

def execute_cli(step: Step, prompt: str, workdir: Path,
 session_id: str | None, log_dir: Path,
 execution_policy: str,
 verbose: bool = True) -> CLIResult:
 args = build_cli_args(step, prompt, workdir, session_id, execution_policy)
 adapter = ADAPTERS[step.agent]
 timeout = step.timeout or DEFAULT_TIMEOUT

 try:
 process = subprocess.Popen(args, stdout=PIPE, stderr=PIPE, text=True, cwd=workdir)
 except FileNotFoundError:
 raise CLINotFoundError(f"CLI '{args[0]}' not found. Is it installed?")

 # 타임아웃감시(shared Event 로 메인스레드에통지)
 timed_out = threading.Event()
 timer = threading.Timer(timeout, _kill_process, args=[process, timed_out])
 timer.start()
 try:
 result = stream_and_log(process, adapter, step.id, log_dir, verbose)
 process.wait()
 finally:
 timer.cancel()

 # 타임아웃판정는메인스레드로행う
 if timed_out.is_set():
 raise StepTimeoutError(step.id, timeout)
 if process.returncode != 0:
 raise CLIExecutionError(step.id, process.returncode, result.stderr)
 return result


def _kill_process(process: subprocess.Popen, timed_out: threading.Event):
 """타임아웃시의 프로세스강제종료.SIGTERM → 5초猶予 → SIGKILL.
 예외는 raise 하지 않는다 — shared Event 로 메인스레드에통지."""
 timed_out.set()
 process.terminate() # SIGTERM
 try:
 process.wait(timeout=5)
 except subprocess.TimeoutExpired:
 process.kill() # SIGKILL


def stream_and_log(process, adapter, step_id, log_dir, verbose) -> CLIResult:
 """행단위로읽기, 로그쓰기·デ코드·터미널표시를동시실행."""
 session_id = None
 cost = None
 texts = []

 with open(log_dir / "stdout.log", "a") as f_raw, \
 open(log_dir / "console.log", "a") as f_con:

 for line in process.stdout:
 # 1. raw 로그(即時 flush — tail -f 대응)
 f_raw.write(line)
 f_raw.flush()

 # 2. JSON デ코드 → CLI별어댑터
 try:
 event = json.loads(line)
 except json.JSONDecodeError:
 continue

 sid = adapter.extract_session_id(event)
 if sid:
 session_id = sid

 text = adapter.extract_text(event)
 if text:
 texts.append(text)
 f_con.write(text + "\n")
 f_con.flush()
 if verbose:
 print(f"[{step_id}] {text}")

 c = adapter.extract_cost(event)
 if c:
 cost = c

 # stderr も저장
 stderr = process.stderr.read()
 if stderr:
 (log_dir / "stderr.log").write_text(stderr)

 return CLIResult(
 full_output="\n".join(texts),
 session_id=session_id,
 cost=cost,
 stderr=stderr,
 )
```

#### CLI 인수ビルダー

```python
def build_cli_args(step: Step, prompt: str, workdir: Path,
 session_id: str | None,
 execution_policy: str) -> list[str]:
 match step.agent:
 case "claude":
 return _build_claude_args(step, prompt, workdir, session_id, execution_policy)
 case "codex":
 return _build_codex_args(step, prompt, workdir, session_id, execution_policy)
 case "gemini":
 return _build_gemini_args(step, prompt, workdir, session_id, execution_policy)


def _build_claude_args(step, prompt, workdir, session_id, execution_policy):
 args = ["claude", "-p", "--output-format", "stream-json", "--verbose"]
 if step.model: args += ["--model", step.model]
 if step.effort: args += ["--effort", step.effort]
 if step.max_budget_usd: args += ["--max-budget-usd", str(step.max_budget_usd)]
 if step.max_turns: args += ["--max-turns", str(step.max_turns)]
 if session_id: args += ["--resume", session_id]
 # execution_policy → 승인제어
 if execution_policy == "auto":
 args += ["--permission-mode", "bypassPermissions"]
 args.append(prompt)
 return args


def _build_codex_args(step, prompt, workdir, session_id, execution_policy):
 if session_id:
 args = ["codex", "exec", "resume", session_id, "--json"]
 else:
 args = ["codex", "exec", "--json", "-C", str(workdir)]
 if step.model: args += ["-m", step.model]
 if step.effort: args += ["-c", f'model_reasoning_effort="{step.effort}"']
 # max_budget_usd, max_turns: Codex 비대응 → 無視
 # execution_policy → 승인·샌드박스제어
 match execution_policy:
 case "auto":
 args.append("--dangerously-bypass-approvals-and-sandbox")
 case "sandbox":
 args += ["-s", "workspace-write"]
 # interactive: 플래그없음
 args.append(prompt)
 return args


def _build_gemini_args(step, prompt, workdir, session_id, execution_policy):
 args = ["gemini", "-p", "-o", "stream-json"] # -p: 비인터랙티브모드
 if step.model: args += ["-m", step.model]
 # effort, max_budget_usd, max_turns: Gemini 비대응 → 無視
 if session_id: args += ["-r", session_id]
 # execution_policy → 승인제어
 match execution_policy:
 case "auto":
 args += ["--approval-mode", "yolo"]
 case "sandbox":
 args.append("-s")
 # interactive: 플래그없음
 args.append(prompt)
 return args
```

### Verdict 파싱

파싱전략: 딜리미터로 verdict 블록를추출し, 내부를 **YAML 로서해석** 한다.
이것에 의해 `evidence` 와 `suggestion` 의 복수행기술(YAML block scalar `|`)를안전에扱える:

```python
import re
import yaml
from dataclasses import dataclass

@dataclass
class Verdict:
 status: str # PASS / RETRY / BACK / ABORT
 reason: str # 판정이유
 evidence: str # 구체적근거(복수행가능)
 suggestion: str # 다음アクション提案(ABORT 시필수)

VERDICT_PATTERN = re.compile(
 r"---VERDICT---\s*\n(.*?)\n\s*---END_VERDICT---",
 re.DOTALL,
)

def parse_verdict(output: str, valid_statuses: set[str]) -> Verdict:
 """CLI 출력부터 verdict 를 추출·검증한다.

 Args:
 output: CLIResult.full_output(어댑터이デ코드완료의 텍스트)
 valid_statuses: 스텝의 on 필드에정의된 verdict 값의집합
 """
 # stream_and_log() 이 어댑터経由로 텍스트추출완료なので,
 # 딜리미터검색만로十분(JSON/JSONL 파싱는불필요)
 match = VERDICT_PATTERN.search(output)
 if not match:
 raise VerdictNotFound(output[-500:])

 verdict = _parse_fields(match.group(1))
 _validate(verdict, valid_statuses)
 return verdict

def _parse_fields(block: str) -> Verdict:
 """verdict 블록를 YAML 로서해석し, 4필드를추출.
 YAML block scalar (|) 에 의해 evidence/suggestion 의 복수행기술에대응."""
 try:
 fields = yaml.safe_load(block)
 except yaml.YAMLError as e:
 raise VerdictParseError(f"YAML parse error in verdict block: {e}")

 if not isinstance(fields, dict):
 raise VerdictParseError(f"Verdict block is not a YAML mapping: {type(fields)}")

 if "status" not in fields:
 raise VerdictParseError("Missing required field: status")
 if "reason" not in fields or not fields["reason"]:
 raise VerdictParseError("Missing required field: reason")
 if "evidence" not in fields or not fields["evidence"]:
 raise VerdictParseError("Missing required field: evidence")

 return Verdict(
 status=str(fields["status"]).strip(),
 reason=str(fields["reason"]).strip(),
 evidence=str(fields["evidence"]).strip(),
 suggestion=str(fields.get("suggestion", "")).strip(),
 )

def _validate(verdict: Verdict, valid_statuses: set[str]):
 """verdict 값의타당성를 검증.부정값는회復不能에러."""
 if verdict.status not in valid_statuses:
 raise InvalidVerdictValue(
 f"'{verdict.status}' not in {valid_statuses}. "
 "This indicates a prompt violation — do not retry."
 )
 if verdict.status in ("ABORT", "BACK") and not verdict.suggestion:
 raise VerdictParseError(f"{verdict.status} verdict requires non-empty suggestion")
```

> **verdict 블록예(복수행 evidence)**:
> ```
> ---VERDICT---
> status: RETRY
> reason: "테스트부족와설계不整合を検出"
> evidence: |
> 1. test_workflow.py:L45 — Medium 테스트미구현
> 2. session_state.py:L120 — load() の戻り타입이설계와불일치
> 3. ruff check 로 3 건의 warning
> suggestion: "상기3点를 수정し, 품질 체크를재실행해 주세요"
> ---END_VERDICT---
> ```

### 로그출력

#### 디렉토리구조

```
test-artifacts/<issue>/
├── session-state.json # issue-scoped stable state(재개의기반)
├── progress.md # 진척목록(人間용, 스텝완료마다에업데이트)
└── runs/
 └── <YYMMDDhhmm>/ # 각실행의 run 로그
 ├── run.log # 워크플로우계층로그(JSONL)
 ├── design/ # 스텝별로그
 │ ├── stdout.log # CLI 生출력(JSONL 그まま)
 │ ├── stderr.log # CLI stderr
 │ └── console.log # 어댑터이デ코드완료의 사람이 읽을 수 있는텍스트
 ├── review-design/
 │ ├── stdout.log
 │ └── ...
 └── implement/
 └── ...
```

#### 워크플로우계층로그(run.log)

하네스의메인ループ이 기록한다이벤트:

| event | payload | 타이밍 |
|-------|---------|-----------|
| `workflow_start` | issue, workflow | 실행시작 |
| `step_start` | step_id, agent, model, effort, session_id | 스텝시작 |
| `step_end` | step_id, verdict(4필드), duration_ms, cost | 스텝완료 |
| `cycle_iteration` | cycle_name, iteration, max_iterations | 사이클カウント증가시 |
| `workflow_end` | status, cycle_counts, total_duration_ms, total_cost, error? | 실행종료 |

```python
@dataclass
class RunLogger:
 log_path: Path

 def _write(self, event: str, **kwargs):
 entry = {"ts": datetime.now(UTC).isoformat(), "event": event, **kwargs}
 with open(self.log_path, "a", encoding="utf-8") as f:
 f.write(json.dumps(entry, ensure_ascii=False) + "\n")
 f.flush()

 def log_workflow_start(self, issue: int, workflow: str):
 self._write("workflow_start", issue=issue, workflow=workflow)

 def log_step_start(self, step_id: str, agent: str, model: str | None,
 effort: str | None, session_id: str | None):
 self._write("step_start", step_id=step_id, agent=agent,
 model=model, effort=effort, session_id=session_id)

 def log_step_end(self, step_id: str, verdict: Verdict,
 duration_ms: int, cost: CostInfo | None):
 self._write("step_end", step_id=step_id,
 verdict=asdict(verdict), duration_ms=duration_ms,
 cost=asdict(cost) if cost else None)

 def log_cycle_iteration(self, cycle_name: str, iteration: int, max_iter: int):
 self._write("cycle_iteration", cycle_name=cycle_name,
 iteration=iteration, max_iterations=max_iter)

 def log_workflow_end(self, status: str, cycle_counts: dict,
 total_duration_ms: int, total_cost: float | None,
 error: str | None = None):
 self._write("workflow_end", status=status, cycle_counts=cycle_counts,
 total_duration_ms=total_duration_ms, total_cost=total_cost,
 error=error)
```

> **現행에서의상속**: `bugfix_agent/run_logger.py` の即時 flush + JSONL 형식를踏襲.
> 이벤트명를 `state_enter`/`state_exit` → `step_start`/`step_end` に改名し,
> verdict 4필드·코스트정보·duration 를 추가.

### 세션상태관리

상태파일는 **issue 단위로고정경로** 에 저장한다.이것에 의해 `--from` 재개時에 어떤 run 의 state 를 읽다かが一意に決まる:

```
test-artifacts/<issue>/
├── session-state.json # issue-scoped stable state(재개의기반)
├── progress.md # 사람이 읽을 수 있는한 진척목록
└── runs/
 └── <YYMMDDhhmm>/ # 각실행의 run 로그(타임스탬프별)
 ├── run.log
 └── <step_id>/
 ├── stdout.log
 ├── stderr.log
 └── console.log
```

```python
STATE_DIR = Path("test-artifacts")
STATE_FILE = "session-state.json"

@dataclass
class StepRecord:
 step_id: str
 verdict_status: str
 verdict_reason: str
 verdict_evidence: str
 verdict_suggestion: str
 timestamp: str # ISO 8601(JSON 시리얼라이즈가능한 str)

@dataclass
class SessionState:
 issue_number: int
 sessions: dict[str, str] # step_id → session_id
 step_history: list[StepRecord] # 실행履歴
 cycle_counts: dict[str, int] # cycle_name → iteration count
 last_completed_step: str | None # 最後에 완료한스텝 ID(再실행용)
 last_transition_verdict: Verdict | None # 현재의전이를引き起こ한 verdict

 @classmethod
 def load_or_create(cls, issue: int) -> "SessionState":
 path = STATE_DIR / str(issue) / STATE_FILE
 if path.exists():
 data = json.loads(path.read_text())
 # step_history 의 rehydrate
 data["step_history"] = [StepRecord(**r) for r in data.get("step_history", [])]
 # last_transition_verdict 의 rehydrate
 ltv = data.pop("last_transition_verdict", None)
 if ltv:
 data["last_transition_verdict"] = Verdict(**ltv)
 return cls(**data)
 return cls(issue_number=issue, sessions={}, step_history=[],
 cycle_counts={}, last_completed_step=None,
 last_transition_verdict=None)

 @property
 def _state_dir(self) -> Path:
 return STATE_DIR / str(self.issue_number)

 def save_session_id(self, step_id: str, session_id: str):
 self.sessions[step_id] = session_id

 def get_session_id(self, resume_target: str | None) -> str | None:
 if resume_target is None:
 return None
 return self.sessions.get(resume_target)

 def cycle_iterations(self, cycle_name: str) -> int:
 return self.cycle_counts.get(cycle_name, 0)

 def increment_cycle(self, cycle_name: str):
 self.cycle_counts[cycle_name] = self.cycle_iterations(cycle_name) + 1

 def record_step(self, step_id: str, verdict: Verdict):
 self.step_history.append(StepRecord(
 step_id=step_id,
 verdict_status=verdict.status,
 verdict_reason=verdict.reason,
 verdict_evidence=verdict.evidence,
 verdict_suggestion=verdict.suggestion,
 timestamp=datetime.now(UTC).isoformat(),
 ))
 self.last_completed_step = step_id
 self.last_transition_verdict = verdict # 次스텝에전달하다
 self._persist() # 스텝완료마다에영속화

 def _persist(self):
 """JSON + progress.md 에 영속화.이상종료시의 --from 再실행를가능에한다."""
 self._state_dir.mkdir(parents=True, exist_ok=True)
 # 機械용: session-state.json
 path = self._state_dir / STATE_FILE
 data = {
 "issue_number": self.issue_number,
 "sessions": self.sessions,
 "step_history": [asdict(r) for r in self.step_history],
 "cycle_counts": self.cycle_counts,
 "last_completed_step": self.last_completed_step,
 "last_transition_verdict": asdict(self.last_transition_verdict)
 if self.last_transition_verdict else None,
 }
 path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
 # 人間용: progress.md(상태확인도구)
 self._write_progress_md()

 def _write_progress_md(self):
 """스텝완료마다에사람이 읽을 수 있는한 진척파일를업데이트."""
 lines = [f"# Progress: Issue #{self.issue_number}\n"]
 for record in self.step_history:
 mark = "x" if record.verdict_status == "PASS" else " "
 lines.append(
 f"- [{mark}] {record.step_id}: {record.verdict_status}"
 f" — {record.verdict_reason}"
 )
 if self.cycle_counts:
 lines.append("\n## 사이클")
 for name, count in self.cycle_counts.items():
 lines.append(f"- {name}: {count} iterations")
 path = self._state_dir / "progress.md"
 path.write_text("\n".join(lines) + "\n", encoding="utf-8")
```

### 워크플로우정의의밸리데이션

로드時에 정적검증를 수행하고, 실행시에러를방지:

```python
def validate_workflow(workflow: Workflow):
 errors = []

 # 스텝레벨의검증
 for step in workflow.steps:
 # 1. resume 先이 존재し, 동일 agent 이다것
 if step.resume:
 target = workflow.find_step(step.resume)
 if not target:
 errors.append(
 f"Step '{step.id}' resumes unknown step '{step.resume}'"
 )
 elif target.agent != step.agent:
 errors.append(
 f"Step '{step.id}' resumes '{step.resume}' but agents differ "
 f"({step.agent} != {target.agent})"
 )

 # 2. on 의 전이先이 존재한다것
 for verdict, next_id in step.on.items():
 if next_id != "end" and not workflow.find_step(next_id):
 errors.append(
 f"Step '{step.id}' transitions to unknown step '{next_id}' on {verdict}"
 )

 # 3. verdict 값이유효이다것
 valid_verdicts = {"PASS", "RETRY", "BACK", "ABORT"}
 for verdict in step.on:
 if verdict not in valid_verdicts:
 errors.append(f"Step '{step.id}' has invalid verdict '{verdict}'")

 # 사이클레벨의검증
 for cycle in workflow.cycles:
 # 4. entry 스텝이존재한다것
 if not workflow.find_step(cycle.entry):
 errors.append(f"Cycle '{cycle.name}' entry step '{cycle.entry}' not found")

 # 5. loop 内스텝이존재한다것
 for step_id in cycle.loop:
 if not workflow.find_step(step_id):
 errors.append(f"Cycle '{cycle.name}' loop step '{step_id}' not found")

 # 6. loop 말미스텝이 RETRY 시에 loop 선두로 전이한다것
 last_step = workflow.find_step(cycle.loop[-1])
 if last_step and last_step.on.get("RETRY") != cycle.loop[0]:
 errors.append(
 f"Cycle '{cycle.name}' loop tail '{cycle.loop[-1]}' RETRY should "
 f"transition to loop head '{cycle.loop[0]}'"
 )

 # 7. entry/loop 内스텝이 PASS 時에 사이클外へ전이한다것(脱出口의 존재)
 all_cycle_steps = {cycle.entry} | set(cycle.loop)
 has_exit = False
 for step_id in all_cycle_steps:
 step = workflow.find_step(step_id)
 if step and step.on.get("PASS") not in all_cycle_steps:
 has_exit = True
 break
 if not has_exit:
 errors.append(f"Cycle '{cycle.name}' has no exit (PASS never leaves the cycle)")

 # 8. on_exhaust 이 유효한 verdict 이다것
 if cycle.on_exhaust not in valid_verdicts:
 errors.append(f"Cycle '{cycle.name}' on_exhaust '{cycle.on_exhaust}' is invalid")

 if errors:
 raise WorkflowValidationError(errors)
```

### 프롬프트구축

입력계약에 기반하여, 하네스이컨텍스트변수와출력요건만를프롬프트에주입한다.
**스킬본체(SKILL.md)는 CLI 이 네이티브로로드한다때문에, 하네스는내용를読み込ま없다**:

```python
def build_prompt(step: Step, issue: int, state: SessionState,
 workflow: Workflow) -> str:
 # 스킬존재확인(pre-flight — 내용는읽지 않는다)
 # validate_skill_exists() 는 run_workflow() 모두로전스텝분를사전 검증완료

 # 필수변수
 variables = {
 "issue_number": issue,
 "step_id": step.id,
 }

 # 사이클변수(사이클내스텝만)
 cycle = workflow.find_cycle_for_step(step.id)
 if cycle:
 variables["cycle_count"] = state.cycle_iterations(cycle.name) + 1 # 1-indexed
 variables["max_iterations"] = cycle.max_iterations

 # 전이원의 verdict(resume 지정 = 문맥계속스텝만)
 # resume 없음의 step(review-design, review-code 등)에는 주입하지 않는다.
 # 이것에 의해, 리뷰스텝이전단의自己평가에引っ張られる것을防ぐ.
 if step.resume and state.last_transition_verdict:
 v = state.last_transition_verdict
 variables["previous_verdict"] = f"reason: {v.reason}\nevidence: {v.evidence}\nsuggestion: {v.suggestion}"

 # 유효한 verdict 값(스킬에허가된 status を明示)
 valid_statuses = list(step.on.keys())

 header = "\n".join(f"- {k}: {v}" for k, v in variables.items())

 return f"""스킬 `{step.skill}` 를 실행해 주세요.

## 세션시작프로토콜
1. GitHub Issue #{issue} を読み, 현재의진척를把握한다
2. git log --oneline -10 で最近의 변경를확인한다
3. 이하의컨텍스트변수를확인한다
4. 상기를踏이전て, 스킬의指示에 따라작업를 실행한다

## 컨텍스트변수
{header}

## 출력요건
실행완료후, 이하의 YAML 형식로 verdict 를 출력해 주세요:

---VERDICT---
status: {" | ".join(valid_statuses)}
reason: "판정이유"
evidence: |
 구체적근거(복수행가능.抽象表現금지)
suggestion: "다음アクション提案"(ABORT/BACK時필수)
---END_VERDICT---
"""
```

> **스킬실행모델**: 하네스는스킬명를 참조한다만로, CLI 이 `cwd=workdir` 로 실행된다際に
> `.claude/skills/{skill_name}/SKILL.md`(Claude Code)또는 `.agents/skills/{skill_name}/SKILL.md`
> (Codex/Gemini)를프로젝트설정로서자동로드한다.하네스이 skill loader / prompt assembler を
> 再구현한다것을명확에避ける.

### V6 에서의설계지식의상속

`dao_harness/` はスクラップ빌드だが, V6(`bugfix_agent/`)의 설계지식는상속한다.
V6 의 코드참조는 `git show v6.0:<path>` 로 행う:

| V6 모듈 | 상속한다지식 | V7 로 의 구현선 |
|---------------|------------|--------------|
| `bugfix_agent/cli.py` | 스트리밍실행, 행단위 flush 패턴 | `dao_harness/cli.py` — `stream_and_log()` + CLI 별어댑터 |
| `bugfix_agent/verdict.py` | 4필드형식, 회復不能에러의분류 | `dao_harness/verdict.py` — YAML 파서에刷新 |
| `bugfix_agent/run_logger.py` | JSONL 로그, 即時 flush | `dao_harness/logger.py` — 이벤트名改名 + 코스트·duration 추가 |
| `bugfix_agent/errors.py` | 에러분류의セマンティクス | `dao_harness/errors.py` — 10 클래스에再編 |
| `bugfix_agent/config.py` | TOML 설정의패턴 | `dao_harness/workflow.py` — YAML 로더에 치환 |
| `bugfix_agent/state.py` | *(상속없음)* | `dao_harness/state.py` — issue-scoped state 에 전面刷新 |
| `bugfix_agent/handlers/` | *(상속없음)* | 스킬側의 책무 |
| `bugfix_agent/tools/` | *(상속없음)* | `dao_harness/cli.py` — `build_*_args` 함수 |
| `bugfix_agent/prompts/` | *(상속없음)* | 스킬側의 책무 |

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.

### Small 테스트

- **워크플로우 YAML 파서**: 정상系·이상系(부정한 전이, 존재하지 않는다스텝참조, agent 불일치 resume)
- **워크플로우밸리데이터**: 정적검증규칙(스텝검증 + 사이클검증)의 테스트.사이클의 entry/loop 존재확인, 脱出口의 유무, loop 말미 RETRY 전이선의 정합성
- **Verdict 파서**: 딜리미터추출, YAML 해석에 의한4필드추출(status/reason/evidence/suggestion), 복수행 evidence/suggestion(YAML block scalar `|`)의 정상해석, verdict 未検出(VerdictNotFound), status 값부정(InvalidVerdictValue — 회復不能), 필수필드欠損(VerdictParseError), ABORT 時 suggestion 필수, 부정 YAML 입력시의 에러ハンドリング
- **CLI 별어댑터**: 각어댑터(Claude/Codex/Gemini)× extract_session_id / extract_text / extract_cost の組み合わせ.実際의 CLI JSONL 샘플를입력와한デ코드검증
- **CLI 인수ビルダー**: 각 agent(claude/codex/gemini)× 신규/resume × model/effort/max_budget_usd/max_turns/timeout × execution_policy(auto/sandbox/interactive)의組み合わせ.agent 비대응필드이無視된다것의 검증를 포함.Gemini 의 `-p` 플래그부여, Codex 의 `--dangerously-bypass-approvals-and-sandbox` 플래그부여를 검증
- **스킬존재검증**: agent 별디렉토리(`.claude/skills/` vs `.agents/skills/`)의 올바른해결, 존재하지 않는다스킬(SkillNotFound), 경로트래버설방어(SecurityError)
- **세션상태관리**: save/load(JSON rehydrate 포함하다), 사이클イテレーションカウント, 세션 ID 검색, `last_transition_verdict` 의 저장·복원
- **사이클상한판정**: `max_iterations` 도달시의 `on_exhaust` verdict 発행
- **프롬프트구축**: 컨텍스트변수전개, 스킬명참조, `previous_verdict` 의 주입조건(resume 지정스텝만)
- **`--from` / `--step` 시작로직**: 시작스텝결정, 불존재스텝의에러, `--step` 시의単発종료
- **resume ガード**: `MissingResumeSessionError` 의 raise 조건

### Medium 테스트

- **CLI 스트리밍통합테스트**: 목 CLI 프로세스이 JSONL 를 순차출력한다환경로, `stream_and_log()` の即時 flush·어댑터デ코드·파일출력를 검증.타임아웃시의 `threading.Event` 통지·SIGTERM → SIGKILL 처리·메인스레드로의 `StepTimeoutError` raise, CLI 未설치시의 CLINotFoundError も검증
- **워크플로우실행테스트**: 목 CLI 로 완전한 워크플로우(design → review → implement → ...)를 실행し, 상태전이·리트라이·abort 를 검증.`--from` 도중재개(전단스킵 + state 복원), `--step` 単発실행(전이せず종료), resume 스텝로 session_id 欠損時의 `MissingResumeSessionError` も검증
- **세션상태영속화**: issue-scoped state 의 저장·읽기·도중재개의통합테스트.`StepRecord` / `Verdict` 의 JSON rehydrate 검증, `--from` 再실행로의state복원
- **로그출력통합테스트**: run.log(워크플로우계층)과 stdout.log / console.log(스텝계층)의 쓰기·구조·即時 flush 의 검증

### Large 테스트

- **実 CLI E2E 테스트**: 実際의 Claude Code / Codex CLI 를 사용하여, 단일스텝(design 만등)를 실행し, verdict 파싱까지의일련의流れ를 검증
- **워크플로우 E2E 테스트**: 簡易워크플로우(2-3 스텝)를実 CLI 로 실행し, 세션 resume·verdict 전이를 검증
- **기존 프로젝트 호환테스트**: kamo2 의 `.claude/skills/` 를 사용한실행테스트

### 스킵한다サイズ

없음.모두의サイズ의 테스트를구현한다.

## 영향문서

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 있음 | 신아키텍처의 ADR 를 추가 |
| docs/ARCHITECTURE.md | 있음 | 하네스아키텍처의기재에전面개정 |
| docs/dev/development_workflow.md | 있음 | 하네스経由의 자동실행플로우를追記 |
| docs/dev/skill-authoring.md | 있음 | **신규생성**.스킬 작성 매뉴얼(AI 참조전제) |
| docs/dev/workflow-authoring.md | 있음 | **신규생성**.워크플로우 정의 매뉴얼(AI 참조전제) |
| docs/cli-guides/ | 없음 | 최신화완료, 그まま유지 |
| docs/dev/testing-convention.md | 없음 | 그まま유지 |
| docs/guides/ | 없음 | git worktree 등는공통, 그まま유지 |
| CLAUDE.md | 있음 | Essential Commands·경로변경(`bugfix_agent/` → `dao_harness/`) |
| pyproject.toml | 있음 | 패키지名·엔트리 포인트변경(`dao_harness`) |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) | 검증방법 | 검증일 |
|--------|----------|-------------------|---------|--------|
| Claude Code CLI `--help` (v2.1.71) | 로컬실행결과 | `-p --output-format stream-json --verbose` 로 JSONL 스트리밍실행.`--model`, `--effort`, `--max-budget-usd`, `--max-turns`, `--permission-mode bypassPermissions` 로 제어.`stream-json` 는 `--verbose` 필수(없음だ와 에러) | `claude --help` 실행 | 2026-03-09 |
| Codex CLI `exec --help` (v0.112.0) | 로컬실행결과 | resume 시에 `--json`, `-m`, `--ephemeral`, `-o` 이 사용가능(v0.63.0 時点의 제약이해소).`-c key=value` 로 config.toml 값의 CLI 오버라이드이가능(`-c 'model_reasoning_effort="high"'`).`--dangerously-bypass-approvals-and-sandbox` 로 전승인·샌드박스를바이패스.`-s workspace-write` 로 샌드박스내자동실행.`--help` に"Use a dotted path (foo.bar.baz) to override nested values. The value portion is parsed as TOML."와 기재 | `codex exec --help` 실행 | 2026-03-09 |
| Codex `--json` 스트리밍동작 | 로컬실행결과 | `codex exec --json` 이 행단위로 JSONL 를 순차출력한다것을実機확인.이벤트: `thread.started` → `item.completed` → `turn.completed`.`thread_id` 로 세션 ID 취득 | 実機테스트실행 | 2026-03-09 |
| Codex `model_reasoning_effort` 설정 | `~/.codex/config.toml` | `model_reasoning_effort = "high"` 이 config.toml で実際에 사용되어 있다것을확인.`-c` 플래그로오버라이드가능 | 파일확인 + `--help` | 2026-03-09 |
| Gemini CLI `--help` (v0.31.0) | 로컬실행결과 | `-p` 로 비인터랙티브모드(headless).`-o stream-json` 로 JSONL 스트리밍출력.`--approval-mode yolo` 로 전승인자동화.`--allowed-tools` 는 비추천로 Policy Engine(TOML)로의移행이추천 | `gemini --help` 실행 | 2026-03-09 |
| Gemini stream-json 동작 | 로컬실행결과 | `gemini -o stream-json` 이 행단위로 JSONL 를 순차출력한다것을実機확인.이벤트: `init`(session_id 포함하다)→ `message` → `response` | 実機테스트실행 | 2026-03-09 |
| Claude Code CLI 가이드 | `docs/cli-guides/claude-code-cli-guide.md` | stream-json 이벤트구조(system/init → assistant → result), session_id 취득방법, `total_cost_usd` 필드, `--verbose` 필수제약 | 문서참조 | 2026-03-09 |
| Codex CLI 가이드 | `docs/cli-guides/codex-cli-session-guide.md` | JSONL 이벤트구조(thread.started → item.completed → turn.completed), resume 시의 설정인수인계, profile 의 `model_reasoning_effort` 설정예 | 문서참조 | 2026-03-09 |
| Gemini CLI 가이드 | `docs/cli-guides/gemini-cli-session-guide.md` | stream-json 이벤트구조(init → message → response), Policy Engine 사양, 샌드박스설정 | 문서참조 | 2026-03-09 |
| 스킬파일형식 | `/home/aki/dev/kamo2/.claude/skills/`, `/home/aki/dev/kamo2/.agents/skills/` | 両디렉토리에동일내용의 `SKILL.md`(YAML frontmatter + Markdown)이배치되어 있다것을実機확인.Claude Code 는 `.claude/skills/`, Codex/Gemini 는 `.agents/skills/` 를 참조 | `ls`, `head` で実機확인 | 2026-03-09 |
| 현행오케스트레이터 | `bugfix_agent/` | verdict 4필드형식(`bugfix_agent/verdict.py`), 에러 계층(`bugfix_agent/errors.py`: VerdictParseError, InvalidVerdictValueError, AgentAbortError), 스트리밍실행(`bugfix_agent/cli.py`: format_jsonl_line), JSONL 로그(`bugfix_agent/run_logger.py`), 프롬프트구성(`prompts/_common.md`, `_review_preamble.md`, `_footer_verdict.md`)를조사し상속 | 소스코드読解 | 2026-03-09 |
| 테스트 규약 | `docs/dev/testing-convention.md` | S/M/L 테스트サイズ정의, 스킵판정기준 | 문서참조 | — |
| 개발워크플로우 | `docs/dev/development_workflow.md` | 현행의 6 페이즈플로우정의, GitHub Issue 활용패턴(本文업데이트 + 코멘트) | 문서참조 | — |
| Anthropic 하네스설계 | [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | "an initializer agent that sets up the environment on the first run, and a coding agent that is tasked with making incremental progress in every session, while leaving clear artifacts for the next session"— 2에이전트패턴, progress file, 세션시작프로토콜(pwd→git log→feature list→init.sh→E2E test), 1기능1세션제약.JSON でのフィーチャー리스트관리("the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files") | Web Fetch | 2026-03-09 |
| Agent Harness Infrastructure | [The Agent Harness: Why 2026 is About Infrastructure](https://www.hugo.im/posts/agent-harness-infrastructure) | "The Agent Harness is the Operating System. The LLM is just the CPU."— 3계층분리(Framework/Runtime/Harness), 3계층메모리모델(Episodic/Semantic/Procedural), Durable Execution 패턴, "Build for Impermanence"원칙 | Web Fetch | 2026-03-09 |
| Agent Harness 2026 | [The importance of Agent Harness in 2026](https://www.philschmid.de/agent-harness-2026) | "Capabilities that required complex, hand-coded pipelines in 2024 are now handled by a single context-window prompt in 2026"— 경량설계의근거.Atomic Tool Design, 실행トラジェクトリのデータ수집 | Web Fetch | 2026-03-09 |

> **本하네스로정의한사양**: verdict 딜리미터형식(`---VERDICT---` / `---END_VERDICT---`), verdict 4필드(status/reason/evidence/suggestion), 세션시작프로토콜は本설계로정의한도의이며, 외부一次정보源는 없다.현행오케스트레이터의 verdict 프로토콜를 상속·확장한설계.
