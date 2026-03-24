# [설계] V5/V6 VERDICT 판정機構의 V7 복원

Issue: #77

## 개요

V7 `kuku_harness.verdict` 의 엄밀일치파서ーを, V5/V6 로 100 회이상의 E2E 테스트에 기반하여설계된ハイブリッド폴백판정機構에 치환하다.출력흔들림로 workflow 전체이致命정지한다現状を解지우다る.

## 배경·목적

#73 의 `issue-pr` 스텝로 PR 생성自体는 성공한에도かかわらず, 에이전트출력의終端이 `---END VERDICT---`(언더스코어누락)だった위해 `VerdictNotFound` 로 workflow 전체이 ERROR 에 되었다.

V7 の現행파서ー는 이하의정규表現만로동작하고 있다:

```python
VERDICT_PATTERN = re.compile(
 r"---VERDICT---\s*\n(.*?)\n\s*---END_VERDICT---",
 re.DOTALL,
)
```

한편 V5/V6 では, strict → relaxed → AI formatter retry 의 3 단계폴백이설계·구현되어 있으며, delimiter 흔들림·필드라벨흔들림·노이즈혼입에 대한耐性を持っていた.今회는이회復전략를 V7 의 아키텍처에適合한다形로 복원한다.

## 인터페이스

### 입력

```python
def parse_verdict(
 output: str,
 valid_statuses: set[str],
 *,
 ai_formatter: Callable[[str], str] | None = None,
 max_retries: int = 2,
) -> Verdict:
```

| 인수 | 타입 | 설명 |
|------|-----|------|
| `output` | `str` | CLI 프로세스의전출력텍스트 |
| `valid_statuses` | `set[str]` | 스텝의 `on` 필드에정의된 verdict 값의집합 |
| `ai_formatter` | `Callable[[str], str] \| None` | Step 3 用 AI 정형함수(생략시는 Step 2 까지로정지) |
| `max_retries` | `int` | Step 3 의 최대리트라이회수(기본값: 2) |

### 출력

```python
@dataclass
class Verdict:
 status: str # "PASS" | "RETRY" | "BACK" | "ABORT" 등
 reason: str # 판정이유
 evidence: str # 판정근거
 suggestion: str # 다음アクション提案(ABORT/BACK 는 필수, 他は空문자허용)
```

반환값의 `Verdict` dataclass 는 변경없음.

### 예외

| 예외 | 폴백대상 | 의미 |
|------|-------------------|------|
| `VerdictNotFound` | いいえ(전스텝실패후) | 출력부터 verdict 를 추출로きなかった |
| `VerdictParseError` | いいえ(전스텝실패후) | 필수필드欠損또는구조해석에러 |
| `InvalidVerdictValue` | **いいえ(即座에 raise)** | 부정한 verdict 값.프롬프트위반.리트라이대상외 |

`InvalidVerdictValue` 만, 어떤스텝로발생하여も即座에 raise 한다.이것는 V5/V6 에서의설계방침를상속：포맷흔들림는회復대상だが, 의미적으로 부정한 값는即실패.

### 사용예

```python
# runner.py 부터호출(기존의호출는그まま동작)
verdict = parse_verdict(
 result.full_output,
 valid_statuses=set(current_step.on.keys()),
)

# AI formatter 付き(将来의 확장)
verdict = parse_verdict(
 result.full_output,
 valid_statuses=set(current_step.on.keys()),
 ai_formatter=my_formatter_func,
 max_retries=2,
)
```

## 제약·전제 조건

- V7 의 verdict 포맷는 YAML ベース(`status:`, `reason:`, `evidence:`, `suggestion:`)를표준으로 한다
- V5/V6 의 `Result:` / `Status:` 패턴도폴백로대응한다(에이전트이구포맷로출력한 경우로의備え)
- `InvalidVerdictValue` 는 전스텝로即座에 raise(V5/V6 와 동일방침)
- `valid_statuses` 에 의한검증로직는변경하지 않는다
- runner.py 는 `create_verdict_formatter` 로 생성한 AI formatter 를 `parse_verdict` に渡し, 3 단계모두를実운용経路로 유효에한다

## 방침

### 3 단계폴백전략

```
Step 1: Strict Parse(현행 V7 상당)
 ├─ 성공 → Verdict 반환
 ├─ InvalidVerdictValue → 即 raise(회復不能)
 └─ VerdictNotFound / VerdictParseError → Step 2 へ

Step 2: Relaxed Parse(V5/V6 由来의 완화판정)
 ├─ 성공 → Verdict 반환
 ├─ InvalidVerdictValue → 即 raise(회復不能)
 └─ 실패 → Step 3 へ(ai_formatter 未제공라면 raise)

Step 3: AI Formatter Retry(V5/V6 由来의 최종수단)
 ├─ 성공 → Verdict 반환
 ├─ InvalidVerdictValue → 即 raise(회復不能)
 └─ 전리트라이실패 → VerdictParseError raise
```

### Step 1: Strict Parse

현행 V7 와 동일.`---VERDICT---` 과 `---END_VERDICT---` 의 엄밀일치 + YAML 파싱.

```python
STRICT_PATTERN = re.compile(
 r"---VERDICT---\s*\n(.*?)\n\s*---END_VERDICT---",
 re.DOTALL,
)
```

### Step 2: Relaxed Parse

2 단계의폴백부터成る.

**2a. Delimiter 완화**

이하의バリエーション를 허용한다정규表現로 verdict 블록를추출:

```python
RELAXED_PATTERN = re.compile(
 r"---\s*VERDICT\s*---\s*\n(.*?)\n\s*---\s*END[\s_]VERDICT\s*---",
 re.DOTALL | re.IGNORECASE,
)
```

| 허용한다흔들림 | 예 |
|-------------|-----|
| 언더스코어/스페이스 | `---END_VERDICT---`, `---END VERDICT---` |
| 大문자소문자 | `---verdict---`, `---Verdict---` |
| delimiter 전후의공백 | `--- VERDICT ---` |

추출된블록내의 YAML 파싱를試みる.

**2b. Key-Value 패턴추출**

YAML 파싱에실패한 경우, V5/V6 由来의 정규表現패턴로 `status` 값를탐색한다.

**V5/V6 의 안전策를 상속**: 패턴自体를 `valid_statuses` 부터동적에생성し, 유효한 verdict 값만를매치대상에한다.이것에 의해 `Status: 200` 와 `Result = success` 와 같은無関係な문자열에 의한 false positive 를 구조적으로 배제한다(`legacy/bugfix_agent/verdict.py:61-78` 의 설계방침).

```python
def _build_relaxed_status_patterns(valid_statuses: set[str]) -> list[re.Pattern[str]]:
 """valid_statuses 부터 relaxed 패턴를동적에생성."""
 alt = "|".join(re.escape(s) for s in sorted(valid_statuses))
 templates = [
 rf"status:\s*({alt})",
 rf"Status:\s*({alt})",
 rf"Result:\s*({alt})",
 rf"-\s*Result:\s*({alt})",
 rf"-\s*Status:\s*({alt})",
 rf"\*\*Status\*\*:\s*({alt})",
 rf"스테이터스:\s*({alt})",
 rf"Status\s*=\s*({alt})",
 rf"Result\s*=\s*({alt})",
 ]
 return [re.compile(t, re.IGNORECASE) for t in templates]
```

패턴이유효값만에매치한다때문에, relaxed parse 로 `InvalidVerdictValue` 는 발생하지 않는다(구조적으로 불가능).

status 이외의필드(reason, evidence, suggestion)も마찬가지에패턴로탐색한다.**단, reason 또는 evidence 이 추출로きなかった경우는 Verdict 를 생성せず, Step 3(AI formatter)에フォールスルー한다**.이유: V7 로 는 `previous_verdict` 로서다음스텝에伝搬된다위해(`kuku_harness/prompt.py:35-40`), 合成문자열를 포함불완전한 Verdict 를 반환하다와, fix 스킬이実在하지 않는다指摘를 근거에동작한다위험이 있다.

### Step 3: AI Formatter Retry

`ai_formatter` 이 제공된경우만실행.V5/V6 의 설계를踏襲:

1. 입력텍스트를 head + tail 전략로 truncate(1/3 head + 2/3 tail.verdict 는 말미에出現しやすい위해 tail 重視)
2. `ai_formatter(truncated_text)` 를 호출, 정형된텍스트를취득
3. 정형결과에 대해 Step 1 → Step 2 を再실행
4. 실패한 경우 `max_retries` 회까지繰り반환하다
5. 전리트라이실패로 `VerdictParseError` 를 raise

```python
AI_FORMATTER_MAX_INPUT_CHARS: int = 8000 # V5/V6 와 동일
```

### 모듈구조

변경대상는이하의 4 파일:

| 파일 | 변경내용 |
|----------|----------|
| `kuku_harness/verdict.py` | 3 단계폴백파서ー + formatter 팩토리 |
| `kuku_harness/runner.py` | formatter 생성·주입 |
| `kuku_harness/cli.py` | 비 JSON 행의수집(출력수집레이어의복원) |
| `kuku_harness/adapters.py` | Codex `mcp_tool_call` 등의추가 item type 에서의텍스트추출 |

```python
# verdict.py 내부구성
_extract_block_strict(output) -> str # Step 1: delimiter 엄밀추출
_extract_block_relaxed(output) -> str # Step 2a: delimiter 완화추출
_parse_yaml_fields(block) -> Verdict # YAML 필드해석(기존의 _parse_fields 改名)
_build_relaxed_status_patterns(valid_statuses) -> list[...] # Step 2b: 패턴동적생성
_parse_relaxed_fields(text, valid_statuses) -> Verdict # Step 2b: regex 필드추출
_validate(verdict, valid_statuses) -> None # 검증(기존의まま)
parse_verdict(output, valid_statuses, *, ai_formatter, max_retries) -> Verdict # 공개 API

FORMATTER_PROMPT: str # Step 3 용프롬프트(V5/V6 由来, V7 YAML 형식에適合)
create_verdict_formatter(agent, model, workdir, valid_statuses) -> Callable # 팩토리함수
```

### Step 3 의 실제운용통합: `create_verdict_formatter` 과 runner.py 변경

V5/V6 で는 각핸들러이 `create_ai_formatter(ctx.reviewer, ...)` 로 formatter 를 생성し `parse_verdict` に渡하여いた(`legacy/bugfix_agent/handlers/init.py:38-40` 등).V7 でも같은패턴를踏襲한다.

**`verdict.py` 에 추가한다 `create_verdict_formatter` 팩토리함수**:

```python
FORMATTER_PROMPT = Template(
 "이하의출력부터 VERDICT 를 추출し, 정확한 YAML 포맷로출력해 주세요.\n"
 "\n"
 "## 입력\n"
 "$raw_output\n"
 "\n"
 "## 출력포맷(엄밀에 따라ください)\n"
 "---VERDICT---\n"
 "status: <$valid_statuses_str のいずれか1つ>\n"
 'reason: "판정이유"\n'
 'evidence: "판정근거"\n'
 'suggestion: "다음アクション提案"\n'
 "---END_VERDICT---\n"
 "\n"
 "중요: status 행는必ず $valid_statuses_str のいずれか를 출력해 주세요.그것이외의값는사용금지입니다.\n"
)

def create_verdict_formatter(
 agent: str,
 valid_statuses: set[str],
 *,
 model: str | None = None,
 workdir: Path | None = None,
) -> Callable[[str], str]:
 """AI verdict formatter 를 생성한다.

 경량한 CLI 호출로출력를정형한다.
 스텝실행의 execute_cli 와 는 독립한簡易프로세스.

 Args:
 agent: CLI 에이전트명 ("claude" | "codex" | "gemini")
 valid_statuses: 스텝의 on 에 정의된 verdict 값의집합.
 formatter prompt に埋め込み, 스텝이受理하지 않는다값의출력를방지한다.
 model: 모델지정(생략時는 에이전트기본값)
 workdir: 작업디렉토리(생략時はカレント)

 Returns:
 Callable[[str], str]: parse_verdict 의 ai_formatter 인수에전달하다함수
 """
 statuses_str = "|".join(sorted(valid_statuses))

 def formatter(raw_output: str) -> str:
 prompt = FORMATTER_PROMPT.safe_substitute(
 raw_output=raw_output,
 valid_statuses_str=statuses_str,
 )
 args = _build_formatter_cli_args(agent, model, prompt)
 try:
 result = subprocess.run(
 args,
 capture_output=True,
 text=True,
 timeout=60,
 cwd=workdir,
 )
 except subprocess.TimeoutExpired as e:
 raise VerdictParseError(f"Formatter timed out: {e}") from e
 if result.returncode != 0:
 raise VerdictParseError(
 f"Formatter failed (exit {result.returncode}): {result.stderr[:300]}"
 )
 if not result.stdout.strip():
 raise VerdictParseError("Formatter returned empty output")
 return result.stdout

 return formatter
```

`_build_formatter_cli_args` 는 `cli.py` 의 agent 별인수구축를簡略화한것.streaming/logging 불필요때문 `-p` (print) 모드로호출하다.

**`runner.py` 의 변경**:

```python
from .verdict import parse_verdict, create_verdict_formatter

# 메인ループ内, CLI 실행後:
valid = set(current_step.on.keys())
formatter = create_verdict_formatter(
 agent=current_step.agent,
 valid_statuses=valid,
 model=current_step.model,
 workdir=self.workdir,
)
verdict = parse_verdict(
 result.full_output,
 valid_statuses=valid,
 ai_formatter=formatter,
)
```

`valid_statuses` 는 `parse_verdict` 과 `create_verdict_formatter` の両方에 같은값를전달하다.이것에 의해 formatter prompt 이 출력한다 status 값이常에 스텝의 `on` 정의와일치し, `InvalidVerdictValue` 即 raise 에 의한 Step 3 自体의 failure 화를 방지한다.

`parse_verdict` のシグネチャ自体는 하위 호환를유지(`ai_formatter=None` 이 기본값)한다때문에, 테스트코드등의기존호출는변경불필요.

### 출력수집레이어의복원: `cli.py` / `adapters.py` 변경

parser 만強화하여も, `parse_verdict()` に届く `full_output` 에 VERDICT 텍스트이含まれなければ無의미.legacy の一次정보는출력수집레이어의회復이 전제이다것을明記하고 있다(`legacy/docs/TEST_DESIGN.md:166-194`, `legacy/docs/E2E_TEST_FINDINGS.md:82-94`).

**문제 1: `cli.py` 의 `stream_and_log()` 이 비 JSON 행를破棄**

현행 `kuku_harness/cli.py:99-102`:
```python
try:
 event: dict[str, Any] = json.loads(line)
except json.JSONDecodeError:
 continue # ← 비 JSON 행는모두捨て하고 있다
```

V5/V6 의 지식로는, Codex 이 `mcp_tool_call` 모드로동작하는 경우, VERDICT 이 플레인텍스트(비 JSON)로서 stdout 에 출력된다것이확인되어 있다(`legacy/docs/E2E_TEST_FINDINGS.md` Section 3.1, Section 4.1).

수정방침:
```python
try:
 event: dict[str, Any] = json.loads(line)
except json.JSONDecodeError:
 # 비 JSON 행도수집(VERDICT 이 플레인텍스트로출력된다경우로의備え)
 stripped = line.strip()
 if stripped:
 texts.append(stripped)
 # console.log にも쓰기(디버그시에 full_output 와 동등의정보를확인가능에한다)
 if f_con:
 f_con.write(stripped + "\n")
 continue
```

이것에 의해비 JSON 행이 `full_output` 과 `console.log` の両方に含まれ, downstream 의 `parse_verdict()` 이 VERDICT を検出가능이 된다.디버그시도 `console.log` 로 비 JSON 행由来의 텍스트를확인할 수 있다.

**문제 2: `CodexAdapter` 이 `agent_message` / `reasoning` 이외의 item type を無視**

현행 `kuku_harness/adapters.py:55-61`:
```python
def extract_text(self, event: dict[str, Any]) -> str | None:
 if event.get("type") == "item.completed":
 item = event.get("item", {})
 if item.get("type") in ("agent_message", "reasoning"):
 text = item.get("text")
 return text if text else None
 return None
```

V5/V6 로 는 `mcp_tool_call` item type 의 `result.content[].text` 에 도 VERDICT 이 포함된다것이확인되어 있다(`legacy/docs/TEST_DESIGN.md` Section 2.5).

수정방침: `CodexAdapter.extract_text()` 로 `mcp_tool_call` 의 `result.content` 부터도텍스트를추출한다.

```python
def extract_text(self, event: dict[str, Any]) -> str | None:
 if event.get("type") == "item.completed":
 item = event.get("item", {})
 item_type = item.get("type")
 if item_type in ("agent_message", "reasoning"):
 text = item.get("text")
 return text if text else None
 if item_type == "mcp_tool_call":
 # mcp_tool_call 의 result.content 부터텍스트를추출
 result = item.get("result", {})
 contents = result.get("content", [])
 texts = [c["text"] for c in contents if c.get("type") == "text" and "text" in c]
 return "\n".join(texts) if texts else None
 return None
```

이것들 2 つ의 변경에 의해, VERDICT 텍스트이어떤와 같은출력형식로出現하여도 `full_output` 에 수집され, `parse_verdict()` 에 도달한다.

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.
> AI 는 테스트를생략한다傾向이 있다때문에, 설계단계로명확에정의し, 생략의여지를배제한다.
> 상세는 [테스트 규약](../../../docs/dev/testing-convention.md) 참조.

### Small 테스트

`tests/test_verdict_parser.py` 를 확장.V5/V6 의 E2E 테스트지식에 기반한케이스를망라한다.

**Step 1 (Strict) — 기존테스트를유지**:
- 정상한 YAML verdict 블록의추출(전 status 값: PASS, RETRY, BACK, ABORT)
- ABORT/BACK 의 suggestion 필수체크
- VerdictNotFound(블록없음, 空출력)
- InvalidVerdictValue(부정 status)
- VerdictParseError(필수필드欠損, 부정 YAML)
- 출력도중에 verdict 이 있다케이스
- 복수 verdict 블록(선두우선)

**Step 2a (Delimiter 완화) — 신규**:
- `---END VERDICT---`(스페이스区切り, #73 実事예)
- `---end_verdict---`(小문자)
- `--- VERDICT ---`(전후스페이스)
- `---VERDICT---` + `---END VERDICT---`(시작는정상, 終端만흔들림)
- delimiter 전후에余분な空행나 로그행이 있다경우

**Step 2b (Key-Value 패턴) — 신규, V5/V6 由来**:
- `Result: PASS` 패턴
- `- Result: PASS` 리스트형식
- `Status: PASS` レガシー형식
- `- Status: PASS` 리스트형식
- `**Status**: PASS` Markdown 強調형식
- `스테이터스: PASS` 日本語
- `Status = PASS` / `Result = PASS` 대입형식
- reason / evidence / suggestion 의 패턴추출
- status 만추출가능로 reason/evidence 이 누락 → Step 3 へフォールスルー(ai_formatter 없음라면 VerdictParseError)
- **false positive 배제**: `Status: 200`, `Result = success` 등의無関係문자列는 패턴에매치하지 않는다것을확인(valid_statuses 제한)

**Step 3 (AI Formatter) — 신규**:
- ai_formatter 성공케이스(정형결과이 strict parse 가능)
- ai_formatter 성공케이스(정형결과이 relaxed parse 로 만성공)
- ai_formatter 전리트라이실패 → VerdictParseError
- ai_formatter 未제공로 Step 2 も실패 → VerdictParseError
- max_retries=1 로 1 회만리트라이
- max_retries < 1 로 ValueError
- **formatter prompt 의 valid_statuses 제한**: `valid_statuses={"PASS", "ABORT"}` 로 생성한 formatter 이 `BACK` 와 `RETRY` 를 포함 prompt を出さ없다것을확인

**출력수집레이어 — 신규**:
- `stream_and_log()` 이 비 JSON 행를 `full_output` 에 포함하다것(`cli.py` 변경의회帰테스트)
- `CodexAdapter.extract_text()` 이 `mcp_tool_call` item type 부터텍스트를추출한다것
- JSON 행 + 비 JSON 행이혼재한다 stdout で, 모두의 텍스트이 `full_output` 에 결합된다것
- 비 JSON 행내의 VERDICT 블록이 `parse_verdict()` で正しく추출된다것(수집→파싱의결합)

**横断테스트**:
- InvalidVerdictValue 는 Step 1 (strict) 과 Step 3 (formatter) で即 raise(strict 는 `_validate` 経由, formatter 는 정형결과의재파싱시에 `_validate` 経由)
- Step 2b (relaxed pattern) 로 는 `InvalidVerdictValue` 이 구조적으로 발생하지 않는다것을확인(패턴自体이 valid_statuses 에 제한되어 있다위해)
- relaxed pattern 의 false positive 배제: `Status: 200`, `Result = success`, `status: running` 등이매치하지 않는다것을확인
- 입력텍스트의 truncation(8000 문자超의 텍스트)
- 노이즈혼입(verdict 블록전후에로그출력, 思考트레이스)
- verdict 이 출력도중(비말미)에있다케이스 + 말미에노이즈

### Medium 테스트

`tests/test_verdict_integration.py` 를 신규생성.

- `runner.py` 의 `parse_verdict` 호출와의결합테스트
 - 정상한 verdict → 스텝전이이正しく동작
 - relaxed parse 로 회復한 verdict → 스텝전이이正しく동작
 - Step 3 (AI formatter) 로 회復한 verdict → 스텝전이이正しく동작
 - VerdictNotFound → runner 이 적절에에러ハンドリング
- `create_verdict_formatter` 의 팩토리결합테스트
 - 각에이전트(claude/codex/gemini)용의 CLI 인수이正しく구축된다것
 - subprocess 호출를목し, formatter が正しく프롬프트를구축·결과를 반환한다것
 - `valid_statuses={"PASS", "ABORT"}` 로 생성한 formatter 의 prompt 에 `RETRY`/`BACK` が含まれ없다것
- 출력수집레이어의결합테스트(`cli.py` + `adapters.py`)
 - Codex 의 `mcp_tool_call` 이벤트부터텍스트이 `full_output` 에 포함된다것(subprocess 를 목)
 - 비 JSON 행이혼재한다 stdout 부터 verdict 이 `parse_verdict()` 로 추출할 수 있다것
- `state.py` 로의 verdict 영속화(relaxed parse 결과를 포함)
- `previous_verdict` 伝搬테스트: relaxed parse 결과의 reason/evidence が次스텝에渡されても정상에동작한다것
- `logger.py` 로의 verdict 로그출력
- 実際의 스킬출력템플릿(`.claude/skills/` 의 파일)부터추출한샘플로파싱

### Large 테스트

`tests/test_verdict_e2e.py` 를 신규생성.

- 実際의 에이전트출력로그(`test-artifacts/` 에 저장)를使った파싱테스트
 - #73 で実際에 출력된 `---END VERDICT---` 케이스
 - 将来의 회帰테스트用に実출력샘플를픽스처로서저장
- `kuku run` 명령어로 workflow 를 실행し, verdict 파싱이전스텝로성공한다것을확인
 - CLI を実際에 기동한다위해 Large サイズ

## 영향문서

이변경에 의해업데이트이필요에된다가능性의 있다문서를列挙한다.

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 없음 | 기존의판정機構의 복원이며, 신규技術選定이 아니다 |
| docs/ARCHITECTURE.md | 있음 | Verdict 판정機構섹션신설(폴백전략, 출력수집계층와의의존, parser/runner 책무분리, Troubleshooting), 전체플로우図의 CLIEventAdapter 설명수정 |
| docs/dev/skill-authoring.md | 있음 | verdict 블록의 stdout 출력규약를追記(Issue 코멘트는 verdict 출력의대체이 아니다것을明記) |
| docs/cli-guides/ | 없음 | CLI 사양변경없음 |
| CLAUDE.md | 없음 | 규약변경없음 |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| V5/V6 verdict 구현 | `legacy/bugfix_agent/verdict.py` | 3 단계폴백(strict → relaxed → AI formatter)의 참조구현.RELAXED_PATTERNS 정의, AI_FORMATTER_MAX_INPUT_CHARS=8000, InvalidVerdictValueError の即 raise 방침 |
| V5/V6 아키텍처 | `legacy/docs/ARCHITECTURE.ja.md` Section 10 | 에러ハンドリング와 폴백의설계思想."포맷흔들림는회復대상, 의미적으로 부정한 값는即실패"의 방침 |
| E2E 테스트지식 | `legacy/docs/E2E_TEST_FINDINGS.md` | 19 회의 E2E 테스트로発見된출력패턴.Codex mcp_tool_call 모드로의플레인텍스트출력, VerdictParseError 근본원인(섹션 3.1), 비 JSON 텍스트행의常時수집의필요性 |
| 테스트설계書 | `legacy/docs/TEST_DESIGN.md` | CodexTool JSON 파싱사양(섹션 2.5)."Step 1 (Strict Parse) → Step 2 (Relaxed Parse) → Step 3 (AI Formatter)"아래에流처리플로우 |
| #73 실행로그 | Issue #77 코멘트 | `---END VERDICT---`(스페이스区切り)에 의한 VerdictNotFound 의 실제事예."출력흔들림로 workflow が即死하지 않는다"것이最중요요건 |
| V7 현행구현 | `kuku_harness/verdict.py` | 엄밀일치만(`VERDICT_PATTERN` 정규表現).완화파싱·폴백없음 |
| V7 프롬프트伝搬 | `kuku_harness/prompt.py:35-40` | `previous_verdict` 로서 reason/evidence/suggestion を次스텝에그まま주입.合成문자열를 포함 verdict は下流스텝의판단를歪める근거 |
| V5/V6 핸들러통합패턴 | `legacy/bugfix_agent/handlers/init.py:38-40`, `design.py:78-79`, `implement.py:90-91` | 각핸들러로 `create_ai_formatter(ctx.reviewer, ...)` 를 생성し `parse_verdict` 에 전달하다통합패턴의 실제예.V7 runner.py 로 의 통합설계의근거 |
| V5/V6 relaxed pattern 제한 | `legacy/bugfix_agent/verdict.py:61-78`, `legacy/docs/ARCHITECTURE.ja.md` Section 10 | relaxed pattern 는 유효 verdict 값만에제한(`PASS\|RETRY\|BACK_DESIGN\|ABORT`).false positive 방지의설계방침 |
| V5/V6 비 JSON 행수집 | `legacy/docs/TEST_DESIGN.md:166-194`, `legacy/docs/E2E_TEST_FINDINGS.md:82-94` | Codex `mcp_tool_call` 모드로는 VERDICT 이 플레인텍스트화し得る위해"무효한 JSON 행는스킵せず수집"이 필요.출력수집레이어를含めた복원의근거 |
| V7 출력수집(현행) | `kuku_harness/cli.py:99-102`, `kuku_harness/adapters.py:55-61` | 현행는비 JSON 행를 `continue` で破棄, CodexAdapter 는 `agent_message`/`reasoning` 만추출.`mcp_tool_call` や플레인텍스트 VERDICT 는 `full_output` 에 도달하지 않는다 |
| V7 워크플로우정의 | `workflows/feature-development.yaml` | 스텝마다의 `valid_statuses` 이 다르다(예: design 는 `PASS\|ABORT` 만, implement 는 `PASS\|RETRY\|BACK\|ABORT`).formatter prompt 를 `valid_statuses` ベース에 한다근거 |

> **중요**: 설계판단의근거와된다一次정보를必ず기재해 주세요.
> - URL만로없이, **근거(인용/要約)** も기재필수
> - 리뷰時に一次정보의기재이 없다경우, 설계 리뷰는중단され합니다
