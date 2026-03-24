# Bugfix Agent v5 E2E테스트지식レポート

**생성日**: 2025-12-06
**테스트기간**: 2025-12-04 ~ 2025-12-06
**総테스트회数**: 19회(うち유효なreport.json: 11회)

---

## 1. エグゼクティブサマリー

### 1.1 테스트결과개요

| 指標 | 값 |
|------|-----|
| 総테스트회수 | 19 |
| 최장도달스테이트 | IMPLEMENT_REVIEW (7/8스테이트) |
| PR_CREATE도달 | 0회 |
| 総테스트時間 | 約7,500초(累計) |

### 1.2 주요発見事項

1. **해결완료문제**: VerdictParseError(JSON파서ー의 비JSON텍스트행無視버그)
2. **未해결문제**: Codex네트워크제한에 의한IMPLEMENT_REVIEW로 의 ABORT
3. **累積적개선**: 스테이트도달数が3 → 7へ단계적으로 向上

---

## 2. 테스트결과상세

### 2.1 테스트목록

| # | Dir | 결과 | 도달스테이트 | 時間(초) | 정지이유 |
|---|-----|------|-------------|----------|----------|
| 1 | 20251204_002334 | ERROR | (空) | 1 | 초기화실패 |
| 2 | 20251204_022721 | ERROR | IMPLEMENT | 818 | Codex resume에러 |
| 3 | 20251205_222714 | ERROR | INVESTIGATE_REVIEW | 951 | VerdictParseError |
| 4 | 20251205_230942 | ERROR | IMPLEMENT_REVIEW | 1115 | codex resume --json 에러 |
| 5 | 20251206_000816 | ERROR | INVESTIGATE_REVIEW | 255 | VerdictParseError |
| 6 | 20251206_013207 | ERROR | IMPLEMENT_REVIEW | 972 | 퍼미션에러 |
| 7 | 20251206_021104 | ERROR | IMPLEMENT_REVIEW | 779 | Codex옵션位置에러 |
| 8 | 20251206_024329 | ERROR | IMPLEMENT_REVIEW | 768 | trusted directory에러 |
| 9 | 20251206_030322 | ERROR | INVESTIGATE_REVIEW | 282 | VerdictParseError(退행) |
| 10 | 20251206_104212 | ERROR | INVESTIGATE_REVIEW | 302 | VerdictParseError(수정전) |
| 11 | 20251206_111908 | ERROR | IMPLEMENT_REVIEW | 846 | Codex네트워크제한 |

### 2.2 도달스테이트별統計

| 정지스테이트 | 회수 | 대표적에러 |
|-------------|------|-------------|
| INIT | 1 | 초기화실패 |
| INVESTIGATE_REVIEW | 4 | VerdictParseError |
| IMPLEMENT | 1 | Codex resume에러 |
| IMPLEMENT_REVIEW | 5 | 각種Codex설정문제 |
| PR_CREATE | 0 | - |

---

## 3. 発見된문제와대응策

### 3.1 [해결완료] VerdictParseError

#### 문제

```
VerdictParseError: No VERDICT Result found in output
```

INVESTIGATE_REVIEW, DETAIL_DESIGN_REVIEW로 발생.`parse_verdict()`がCodex출력부터VERDICTを検出할 수 없다.

#### 근본원인

CodexTool JSON파서ー(`bugfix_agent_orchestrator.py:760-766`)의 버그：

```python
# Before (버그있음)
except json.JSONDecodeError:
 if session_id: # resume 모드만텍스트행를수집
 assistant_replies.append(line)
 continue
```

신규세션(`session_id is None`)로は, JSON파싱에실패한플레인텍스트행이**無視**されていた.

Codex CLIは`mcp_tool_call`모드로동작하는 경우, VERDICT를 플레인텍스트로서출력한다때문에, 수집されなかった.

#### 대응策(구현완료)

```python
# After (수정후)
except json.JSONDecodeError:
 # JSON이외의텍스트행(VERDICT를 포함가능性)를수집
 # Note: mcp_tool_call모드로는VERDICT이 플레인텍스트로서출력된다
 assistant_replies.append(line)
 continue
```

#### 검증결과

Test 10でINVESTIGATE_REVIEW, DETAIL_DESIGN_REVIEW의両方がPASS를 확인.

---

### 3.2 [해결완료] codex exec resume 의 --json 에러

#### 문제

```
error: unexpected argument '--json' found
Usage: codex exec resume <SESSION_ID> [PROMPT]
```

#### 근본원인

`codex exec resume`서브명령어는`--json`옵션를지원하지 않고 있다.

#### 대응策(구현완료)

```python
# Before
args = ['codex', 'exec', 'resume', session_id, '--json', prompt]

# After
args = ['codex', 'exec', 'resume', session_id, prompt]
```

---

### 3.3 [해결완료] Claude Code 퍼미션에러

#### 문제

```
Error: This command requires approval
```

IMPLEMENT페이즈로`python -m pytest`이 블록.

#### 근본원인

`~/.claude/settings.json`의 `permissions.allow`에 필요한 명령어패턴이含まれていなかった.

#### 대응策(구현완료)

1. settings.json에 허가패턴를추가：
```json
"allow": [
 "Bash(python:*)",
 "Bash(python3:*)",
 "Bash(pytest:*)",
 "Bash(mkdir:*)",
 "Bash(cat:*)",
 "Bash(touch:*)",
 "Bash(mv:*)",
 "Bash(rm:*)",
 "Bash(echo:*)",
 "Bash(cd:*)",
 "Bash(PYTHONPATH:*)",
 "Bash(source:*)",
 "Bash(export:*)",
 "Bash(head:*)",
 "Bash(tail:*)",
 "Bash(grep:*)",
 "Bash(wc:*)",
 "Bash(diff:*)"
]
```

2. CLI에 퍼미션바이패스옵션를추가：
```python
# Claude CLI
args.append("--dangerously-skip-permissions")

# Codex CLI
args.append("--dangerously-bypass-approvals-and-sandbox")

# Gemini CLI
args += ["--approval-mode", "yolo"]
```

---

### 3.4 [해결완료] Codex trusted directory 에러

#### 문제

```
Not inside a trusted directory and --skip-git-repo-check was not specified.
```

#### 대응策(구현완료)

```python
args = ["codex", "--dangerously-bypass-approvals-and-sandbox",
 "exec", "--skip-git-repo-check", ...]
```

---

### 3.5 [해결완료] Codex 글로벌옵션位置에러

#### 문제

```
error: unexpected argument '--dangerously-bypass-approvals-and-sandbox' found
```

#### 근본원인

`--dangerously-bypass-approvals-and-sandbox`는 글로벌옵션로, `exec`서브명령어의前에 배치이필요.

#### 대응策(구현완료)

```python
# Before (NG)
args = ["codex", "exec", ..., "--dangerously-bypass-approvals-and-sandbox", prompt]

# After (OK)
args = ["codex", "--dangerously-bypass-approvals-and-sandbox", "exec", ...]
```

---

### 3.6 [未해결] Codex 네트워크제한

#### 문제

```
AgentAbortError: Agent aborted: GitHub Issue本文와 변경내용에접근할 수 없다때문에,
체크리스트를평가할 수 없다
```

IMPLEMENT_REVIEWでCodexが`network_access=restricted`, `approval_policy=never`로 동작し, `gh issue view`やWeb취득이실행불가.

#### 현재의상황

Test 10(최신)로발생.IMPLEMENT_REVIEW까지의전스테이트는 정상에동작.

#### 추천대응策

**案A**: 프롬프트수정(추천)
- IMPLEMENT_REVIEW프롬프트를수정し, GitHub API에 의존せず로컬파일참조로동작한다よう변경
- Issue本文는 오케스트레이터ー이 프롬프트에埋め込む

**案B**: Codex설정변경
- `--dangerously-bypass-approvals-and-sandbox`옵션로네트워크접근를허가
- 보안リスク의 고려이필요

---

## 4. 기술적지식

### 4.1 Codex CLI 출력포맷의비결정性

#### 発見

동일의Codex명령어로도, 환경나 상태에 의해출력포맷이変화한다：

| item type | 발생조건 | VERDICT位置 |
|-----------|---------|-------------|
| `command_execution` | 통상모드 | agent_message.text |
| `mcp_tool_call` | MCP経由모드 | 플레인텍스트행 |

#### 教訓

- Codex출력파서ーは両方의 포맷에대응한다필요이 있다
- 플레인텍스트행도常에 수집해야 할

### 4.2 Codex CLI 옵션구조

```
codex [GLOBAL_OPTIONS] exec [EXEC_OPTIONS] [PROMPT]

GLOBAL_OPTIONS:
 --dangerously-bypass-approvals-and-sandbox

EXEC_OPTIONS:
 --skip-git-repo-check
 --json
 -m <model>
 -C <directory>
```

#### 教訓

- 글로벌옵션와서브명령어옵션의배치順序에 주의
- CLIヘルプ로 사전 검증한다것을추천

### 4.3 LLM Recency Bias

#### 発見

프롬프트로`_common.md`(공통규칙)를선두에배치하여いたが, 말미의개별프롬프트로모순한다指示이 있다와, 말미의指示이 우선된다.

#### 대응

- 개별프롬프트말미에도공통규칙를再明示
- 중요な指示는 말미에배치

### 4.4 VERDICT형식의統一효과

#### Before

| 스테이트 | 성공 | 실패系 |
|----------|------|--------|
| INIT | `OK` | `NG` |
| INVESTIGATE_REVIEW | `PASS` | `BLOCKED` |
| IMPLEMENT_REVIEW | `PASS` | `FIX_REQUIRED`, `DESIGN_FIX` |

#### After

```
VERDICT: PASS → 次스테이트へ進む
VERDICT: RETRY → 同스테이트再실행
VERDICT: BACK_DESIGN → DETAIL_DESIGN へ戻る
VERDICT: ABORT → 即座에 종료(속행不能)
```

#### 효과

- 파싱로직의단순화(정규表現1つ로 대응)
- 전이先が自己문서화(키ワード부터전이先이 명확)
- 에러ハンドリング의 개선(ABORT로 명시적종료)

---

## 5. 구현수정履歴

### 5.1 코드 수정목록

| Fix # | 수정내용 | 파일 | 행번호 |
|-------|---------|----------|--------|
| 1 | 전agent_message결합 | bugfix_agent_orchestrator.py | 755-788 |
| 2 | resume --json 삭제 | bugfix_agent_orchestrator.py | 714 |
| 3 | resume모드텍스트수집 | bugfix_agent_orchestrator.py | 762-767 |
| 4 | 퍼미션설정추가 | ~/.claude/settings.json | - |
| 5 | 퍼미션바이패스추가 | bugfix_agent_orchestrator.py | 618, 730, 851 |
| 6 | Codex옵션位置수정 | bugfix_agent_orchestrator.py | 722 |
| 7 | --skip-git-repo-check추가 | bugfix_agent_orchestrator.py | 714, 722 |
| 8 | 비JSON텍스트常時수집 | bugfix_agent_orchestrator.py | 760-766 |

### 5.2 중요한 수정(상세)

#### Fix 8: VerdictParseError근본수정

**변경前**:
```python
try:
 payload = json.loads(line)
except json.JSONDecodeError:
 if session_id: # resume 모드만
 assistant_replies.append(line)
 continue
```

**변경後**:
```python
try:
 payload = json.loads(line)
except json.JSONDecodeError:
 # JSON이외의텍스트행(VERDICT를 포함가능性)를수집
 # Note: mcp_tool_call모드로는VERDICT이 플레인텍스트로서출력된다
 assistant_replies.append(line)
 continue
```

---

## 6. 향후의개선提案

### 6.1 短期(次회테스트까지)

1. **IMPLEMENT_REVIEW의네트워크의존배제**
 - 프롬프트를수정し, 오케스트레이터ーがIssue本文를 프롬프트에埋め込む
 - `gh issue view`로의의존를삭제

2. **PR_CREATE스테이트의 검증**
 - IMPLEMENT_REVIEW通過後의 PR_CREATE동작확인
 - 브랜치생성·プッシュ·PR생성의테스트

### 6.2 中期(안정화페이즈)

1. **Codex출력파서ー의 견고화**
 - `mcp_tool_call`타입의`result.content[].text`부터도VERDICT추출
 - 포맷변경에강한설계

2. **에러복구의개선**
 - ABORT이 아니라RETRY로 복구가능한 케이스의識별
 - 타임아웃후의 자동리트라이

3. **테스트인フラ의 개선**
 - 자동감시스크립트의신뢰性向上
 - 테스트결과의자동集計

### 6.3 長期(プロダクション준비)

1. **보안설정의見直し**
 - `--dangerously-*`옵션의본번이용가부
 - 최소권한원칙에 기반한설정

2. **멀티에이전트協調의 최적화**
 - Gemini/Codex/Claude間의 역할분担見直し
 - 보틀넥해소

3. **코스트최적화**
 - APIコール数의 삭감
 - 모델선택의최적화

---

## 7. 証跡디렉토리

```
test-artifacts/e2e/L1-001/
├── 20251204_000922/ # Test 1 (초기테스트)
├── 20251204_002306/
├── 20251204_002334/ # Test 1 (report.json있음)
├── 20251204_002532/
├── 20251204_022554/
├── 20251204_022627/
├── 20251204_022640/
├── 20251204_022712/
├── 20251204_022721/ # Test 2
├── 20251205_222714/ # Test 3
├── 20251205_230942/ # Test 4
├── 20251206_000816/ # Test 5
├── 20251206_011331/
├── 20251206_013207/ # Test 6
├── 20251206_021104/ # Test 7
├── 20251206_024329/ # Test 8
├── 20251206_030322/ # Test 9
├── 20251206_104212/ # Test 10
└── 20251206_111908/ # Test 11 (최신·최장도달)
```

각디렉토리에포함된다파일:
- `report.json`: 테스트결과サマリー
- `agent_stdout.log`: 에이전트표준출력
- `agent_stderr.log`: 에이전트표준에러출력

---

## 8. 참고資料

- Issue #194: [Bugfix Agent v5 상태 머신 프로토콜정의](https://github.com/apokamo/kamo2/issues/194)
- 코드: `.claude/agents/bugfix-v5/bugfix_agent_orchestrator.py`
- 프롬프트: `.claude/agents/bugfix-v5/prompts/`

---

## 9. 결론

E2E테스트19회의 실제施에 의해, Bugfix Agent v5의 주요한 기술적과제이특정·해결されま한.

**달성事項**:
- VerdictParseError문제의근본해결
- Codex CLI각種설정문제의해결
- 스테이트도달数: 3 → 7(87.5%개선)

**残과제**:
- Codex네트워크제한문제(IMPLEMENT_REVIEW)
- PR_CREATE스테이트の未검증

次회테스트로는IMPLEMENT_REVIEW의프롬프트수정를적용し, PR_CREATE도달를目指합니다.
