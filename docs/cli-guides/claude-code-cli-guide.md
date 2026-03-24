# Claude Code CLI 가이드

## 개요

Claude Code CLI 의 포괄적인레퍼런스.
세션관리, Permissions설정, JSON출력, 서브에이전트, 실전적인사용패턴를기재.

**대상버전**: Claude Code v2.1.71+
**--help 취득日**: 2026-03-09(v2.1.71 의 로컬환경로취득)
**공식문서**: https://docs.anthropic.com/claude-code

---

## 1. 기본명령어구조

### 1.1 인터랙티브모드(기본값)

```bash
claude [OPTIONS] [PROMPT]
```

### 1.2 비인터랙티브모드(파이프용)

```bash
claude -p [OPTIONS] "프롬프트"
```

`-p` / `--print` 옵션로응답를출력하여종료.Agent SDK 에서의プ로그ラム적 이용에도 대응.

### 1.3 기타명령어

| 명령어 | 설명 |
|---------|------|
| `claude update` | 최신버전에업데이트 |
| `claude auth login` | Anthropic어카운트에로그인(`--email`, `--sso` 옵션) |
| `claude auth logout` | 로그아웃 |
| `claude auth status` | 인증상태를JSON표시(`--text` 로 텍스트 표시) |
| `claude agents` | 설정완료서브에이전트목록(소스별그룹표시) |
| `claude mcp` | MCP 서버설정 |
| `claude remote-control` | Claude.ai / Claude 앱에서의리모트제어세션시작 |

---

## 2. 이용가능한 파라미터

### 2.1 주요옵션

| 옵션 | 축약형 | 설명 | 예 |
|-----------|--------|------|-----|
| `--print` | `-p` | 비인터랙티브모드 | `-p "질문"` |
| `--model` | - | 사용모델(에일리어스또는풀모델명) | `--model opus` |
| `--output-format` | - | 출력형식(`-p` 필수) | `--output-format json` |
| `--input-format` | - | 입력형식(`-p` 필수) | `--input-format stream-json` |
| `--continue` | `-c` | 최신세션를계속 | `-c "이어서의 질문"` |
| `--resume` | `-r` | 세션ID또는이름로재개 | `-r "auth-refactor"` |
| `--session-id` | - | 특정의 세션ID를 사용(UUID형식) | `--session-id <uuid>` |
| `--fork-session` | - | 새로운세션ID로 재개(`-r`/`-c` 과 병용) | `--resume abc --fork-session` |
| `--from-pr` | - | PR번호/URL에 연결된세션를재개 | `--from-pr 123` |
| `--system-prompt` | - | 시스템프롬프트전체를치환 | `--system-prompt "..."` |
| `--system-prompt-file` | - | 파일부터시스템프롬프트를읽기(치환) | `--system-prompt-file ./prompt.txt` |
| `--append-system-prompt` | - | 기본값프롬프트에추가 | `--append-system-prompt "..."` |
| `--append-system-prompt-file` | - | 파일부터프롬프트를추가읽기 | `--append-system-prompt-file ./rules.txt` |
| `--add-dir` | - | 추가디렉토리접근 | `--add-dir ../apps ../lib` |
| `--verbose` | - | 상세로그출력(턴마다의 출력) | `--verbose` |
| `--debug` | `-d` | 디버그모드(카테고리필터가능) | `--debug "api,mcp"` |
| `--debug-file` | - | 디버그로그를지정파일에출력(암묵적에디버그모드유효) | `--debug-file ./debug.log` |
| `--effort` | - | 세션의에포트레벨(low, medium, high) | `--effort high` |
| `--version` | `-v` | 버전표시 | `-v` |

### 2.2 신기능옵션

| 옵션 | 설명 | 예 |
|-----------|------|-----|
| `--agent` | 세션로사용하는 에이전트를지정 | `--agent my-custom-agent` |
| `--agents` | 커스텀서브에이전트를JSON정의 | `--agents '{"reviewer":{...}}'` |
| `--max-budget-usd` | API호출의코스트상한(`-p` 필수) | `--max-budget-usd 5.00` |
| `--max-turns` | 에이전트턴수의 상한(`-p` 필수) | `--max-turns 3` |
| `--json-schema` | 구조화 출력의JSON스키마(`-p` 필수) | `--json-schema '{"type":"object",...}'` |
| `--fallback-model` | 과부하시의 폴백모델(`-p` 필수) | `--fallback-model sonnet` |
| `--worktree` | `-w` | 격리된git worktree로 기동 | `-w feature-auth` |
| `--teammate-mode` | 에이전트팀의 표시모드 | `--teammate-mode tmux` |
| `--no-session-persistence` | 세션영속화무효(`-p` 필수) | `--no-session-persistence` |
| `--include-partial-messages` | 부분스트리밍이벤트 출력(`-p` + `stream-json`) | `--include-partial-messages` |
| `--file` | 기동시에 다운로드하는 파일리소스(file_id:상대경로형식) | `--file file_abc:doc.txt` |
| `--settings` | 추가설정파일또는JSON문자열 | `--settings ./settings.json` |
| `--setting-sources` | 읽어들이는설정소스(user,project,local) | `--setting-sources user,project` |
| `--chrome` | Chrome 브라우저통합를유효화 | `--chrome` |
| `--no-chrome` | Chrome 브라우저통합를무효화 | `--no-chrome` |
| `--ide` | IDE자동접속 | `--ide` |
| `--betas` | 베타기능헤더(API키유저만) | `--betas interleaved-thinking` |
| `--init` | 초기화훅를 실행하여인터랙티브모드시작 | `--init` |
| `--init-only` | 초기화훅를 실행하여종료 | `--init-only` |
| `--maintenance` | 메인터넌스훅를 실행하여종료 | `--maintenance` |
| `--remote` | claude.ai 로 웹세션 생성 | `--remote "Fix the bug"` |
| `--teleport` | 웹세션를로컬터미널로 재개 | `--teleport` |
| `--disable-slash-commands` | 스킬·명령어를무효화 | `--disable-slash-commands` |
| `--strict-mcp-config` | `--mcp-config` 의 MCP서버만사용 | `--strict-mcp-config` |
| `--mcp-config` | MCP서버설정파일 | `--mcp-config ./mcp.json` |
| `--permission-prompt-tool` | 권한프롬프트를처리하는 MCP도구 | `--permission-prompt-tool mcp_auth` |
| `--plugin-dir` | 플러그인디렉토리읽기 | `--plugin-dir ./my-plugins` |
| `--allow-dangerously-skip-permissions` | 권한바이패스를옵션로서 유효화 | `--permission-mode plan --allow-dangerously-skip-permissions` |
| `--replay-user-messages` | 유저메시지의리플레이 | `--replay-user-messages` |

### 2.3 출력형식옵션(`--print` 필수)

| 옵션 | 설명 |
|-----------|------|
| `--output-format text` | 텍스트형식(기본값) |
| `--output-format json` | JSON형식(단일결과) |
| `--output-format stream-json` | 스트리밍JSON(NDJSON형식) |

### 2.4 입력형식옵션(`--print` 필수)

| 옵션 | 설명 |
|-----------|------|
| `--input-format text` | 텍스트입력(기본값) |
| `--input-format stream-json` | NDJSON형식로스트리밍입력(멀티에이전트파이프라인용) |

### 2.5 도구제어옵션

| 옵션 | 설명 | 예 |
|-----------|------|-----|
| `--allowedTools` | 허가하는 도구(권한프롬프트없음로 실행) | `--allowedTools "Bash(git log *)" "Read"` |
| `--disallowedTools` | 금지하는 도구(컨텍스트부터제외) | `--disallowedTools "Bash" "Edit"` |
| `--tools` | 이용가능도구를 제한 | `--tools "Bash,Edit,Read"` |

**주의**: `--allowedTools` 은 퍼미션의자동승인, `--tools` 은 이용 가능한 도구 자체의 제한.용도이다르다.

### 2.6 권한옵션

| 옵션 | 설명 |
|-----------|------|
| `--permission-mode default` | 기본값(初회사용時에 확인) |
| `--permission-mode acceptEdits` | 파일편집를자동승인 |
| `--permission-mode plan` | 플랜모드(분석만, 변경불가) |
| `--permission-mode dontAsk` | 확인없음(사전 허가 완료도구만실행, 그 외는 모두 거부) |
| `--permission-mode bypassPermissions` | 전권한체크를스킵(컨테이너/VM등의격리환경만) |
| `--dangerously-skip-permissions` | 전권한체크를스킵(위험) |
| `--allow-dangerously-skip-permissions` | 권한바이패스를옵션유효화(다른 모드와 조합 가능) |

---

## 3. Permissions설정

### 3.1 패턴구문

**v2.1.x 이후의와일드카드구문**:

| 패턴 | 결과 | 비고 |
|---------|------|------|
| `Bash(rm *)` | ✅ 블록성공 | 스페이스+`*` でワードバウンダリ |
| `Bash(git commit *)` | ✅ 매치 | `git commit -m "msg"` 등에매치 |
| `Bash(ls*)` | ✅ 매치 | `ls`, `lsof` 両方에 매치 |
| `Bash(* --help *)` | ✅ 매치 | 선두·중간·말미의와일드카드대응 |

**レガシー구문**: `Bash(rm:*)` のコロン구문는비추천だが引き続き동작한다.

### 3.2 설정파일우선順位

| 파일 | 스코프 | 우선度 |
|---------|---------|--------|
| `managed-settings.json` | 企業관리(덮어쓰기불가) | 최고 |
| CLI인수(`--allowedTools`등) | 세션一時 | 高 |
| `.claude/settings.local.json` | 로컬프로젝트 | 中高 |
| `.claude/settings.json` | 프로젝트공유 | 中 |
| `~/.claude/settings.json` | 유저전체 | 低 |

### 3.3 처리順序

```
PreToolUse Hook → Deny Rules → Ask Rules → Allow Rules → Permission Mode Check
```

**Deny Rules 이 최우선**로 처리된다.어떤레벨로도Deny된도구는他의 레벨로허가할 수 없다.

### 3.4 도구별패턴

| 도구 | 패턴예 | 설명 |
|--------|-----------|------|
| `Bash` | `Bash(npm run *)` | 와일드카드대응 |
| `Read` | `Read(./.env)`, `Read(~/Documents/*.pdf)` | gitignore사양경로 |
| `Edit` | `Edit(/src/**/*.ts)` | 프로젝트루트상대 |
| `WebFetch` | `WebFetch(domain:example.com)` | ド메인지정 |
| `Agent` | `Agent(Explore)`, `Agent(my-agent)` | 서브에이전트제어 |
| `mcp__*` | `mcp__puppeteer__puppeteer_navigate` | MCP도구제어 |

**경로記法의 주의**:
- `/path` → 프로젝트루트상대(**NOT** 絶対경로)
- `//path` → 파일시스템루트에서의絶対경로
- `~/path` → ホーム디렉토리상대

### 3.5 ベストプラクティス

#### 보안重視(エンタープライズ용)

```json
{
 "permissions": {
 "deny": [
 "Read(.env)", "Read(.env.*)", "Edit(.env)", "Write(.env)",
 "Read(~/.aws/**)", "Read(~/.ssh/**)",
 "Bash(sudo *)", "Bash(su *)", "Bash(curl *)", "Bash(wget *)",
 "Bash(rm *)", "Bash(chmod *)", "WebFetch"
 ]
 }
}
```

#### 개발효율重視(개人개발용)

```json
{
 "permissions": {
 "deny": [
 "Bash(sudo *)", "Bash(su *)", "Bash(chmod *)", "Bash(chown *)",
 "Bash(dd *)", "Bash(mkfs *)", "Bash(fdisk *)",
 "Bash(shutdown *)", "Bash(reboot *)", "Bash(halt *)", "Bash(poweroff *)",
 "Bash(curl *)", "Bash(wget *)", "Bash(git config *)"
 ]
 }
}
```

### 3.6 주의점

1. **`Read` 를 블록하여도 `Bash(cat *)` で読める** → 완전보호에는両方블록필요
2. **Bash 패턴는와일드카드매치** → `Bash(rm *)` 는 `rm`, `rm -rf` 등에매치.`Bash(ls *)` 는 `lsof` に는 매치하지 않는다(스페이스+`*`)
3. **도구별에 개별설정이필요** → `Read`, `Write`, `Edit` 는 별々의 도구
4. **シェル演算子を認識** → `Bash(safe-cmd *)` 는 `safe-cmd && other-cmd` 를 허가하지 않는다

### 3.7 비인터랙티브모드로의제한

`-p` 모드로는Bash명령어이기본값로블록된다.

**해결策**: `~/.claude/settings.json` 에 `permissions.allow` 를 추가：

```json
{
 "permissions": {
 "allow": [
 "Bash(gh *)", "Bash(git *)", "Read", "Write", "Edit"
 ],
 "deny": [...]
 }
}
```

---

## 4. 세션관리

### 4.1 세션계속옵션

| 옵션 | 설명 | 용도 |
|-----------|------|------|
| `-c, --continue` | 최신의세션를계속 | 단일에이전트 |
| `-r, --resume [sessionId/name]` | 지정세션를재개(ID또는이름) | 복수에이전트관리 |
| `--session-id <uuid>` | 특정UUID로 세션시작 | 事前にID지정 |
| `--fork-session` | 新ID로 분岐(resume/continue과 병용) | 세션의복사 |
| `--from-pr <number/url>` | PR紐づき세션를재개 | PR연계워크플로우 |
| `--no-session-persistence` | 세션영속화무효(`-p` 필수) | 일시적한 처리 |

### 4.2 세션ID의취득방법

JSON출력부터 `session_id` 필드를추출：

```bash
SESSION_ID=$(claude -p --output-format json "태스크시작" | jq -r '.session_id')
echo $SESSION_ID
# 출력예: 4c5a56e4-7a81-4603-a105-947e81bbfd6a
```

### 4.3 세션인수인계의예

```bash
# 신규세션시작, ID를 취득
SESSION_ID=$(claude -p --output-format json "1+1は？" | jq -r '.session_id')

# 같은세션를계속(최신세션)
claude -p -c "그答えに2を足すと？"

# 세션ID를 명시적에지정
claude -p -r "$SESSION_ID" "더욱10を足すと？"

# 세션를분岐(새로운ID로 계속)
claude -p -r "$SESSION_ID" --fork-session "별의 계산를하여"

# PR紐づき세션를재개
claude --from-pr 123 "PR의리뷰を続けて"
```

### 4.4 세션영속화의제어

```bash
# 세션를저장하지 않는다(일시적처리용)
claude -p --no-session-persistence "일시적한 질문"
```

---

## 5. JSON출력의상세

### 5.1 기본JSON출력(`--output-format json`)

실행명령어：
```bash
claude -p --output-format json "2+2は？"
```

출력(정형완료)：
```json
{
 "type": "result",
 "subtype": "success",
 "is_error": false,
 "duration_ms": 3371,
 "duration_api_ms": 10013,
 "num_turns": 1,
 "result": "4입니다.",
 "session_id": "4c5a56e4-7a81-4603-a105-947e81bbfd6a",
 "total_cost_usd": 0.233663,
 "usage": {
 "input_tokens": 3,
 "cache_creation_input_tokens": 31675,
 "cache_read_input_tokens": 0,
 "output_tokens": 7,
 "server_tool_use": {
 "web_search_requests": 0,
 "web_fetch_requests": 0
 },
 "service_tier": "standard",
 "cache_creation": {
 "ephemeral_1h_input_tokens": 0,
 "ephemeral_5m_input_tokens": 31675
 }
 },
 "modelUsage": {
 "claude-opus-4-6": {
 "inputTokens": 6,
 "outputTokens": 35,
 "cacheReadInputTokens": 0,
 "cacheCreationInputTokens": 36215,
 "webSearchRequests": 0,
 "costUSD": 0.22724875,
 "contextWindow": 200000
 },
 "claude-haiku-4-5-20251001": {
 "inputTokens": 3,
 "outputTokens": 194,
 "cacheReadInputTokens": 0,
 "cacheCreationInputTokens": 4353,
 "webSearchRequests": 0,
 "costUSD": 0.00641425,
 "contextWindow": 200000
 }
 },
 "permission_denials": [],
 "uuid": "1f79c5e0-2a13-4b03-b276-5308297e3b8e"
}
```

### 5.2 JSON출력의필드설명

#### 탑레벨필드

| 필드 | 설명 |
|-----------|------|
| `type` | 결과타입(`"result"`) |
| `subtype` | 결과서브타입(`"success"` / `"error"`) |
| `is_error` | 에러か어떻게인가 |
| `duration_ms` | 総실행時間(ミリ초) |
| `duration_api_ms` | API호출時間(ミリ초) |
| `num_turns` | 턴수(会話の往復数) |
| `result` | 최종회答텍스트 |
| `session_id` | 세션ID(UUID형식) |
| `total_cost_usd` | 総코스트(USD) |
| `uuid` | 이리퀘스트의一意ID |

#### usage 필드

| 필드 | 설명 |
|-----------|------|
| `input_tokens` | 입력토큰수 |
| `cache_creation_input_tokens` | 캐시생성토큰수 |
| `cache_read_input_tokens` | 캐시읽기토큰수 |
| `output_tokens` | 출력토큰수 |
| `server_tool_use.web_search_requests` | Web검색리퀘스트수 |
| `server_tool_use.web_fetch_requests` | Webフェッチ리퀘스트수 |
| `service_tier` | 서비스계층(`"standard"` 등) |

#### modelUsage 필드

모델마다의상세한 사용量：

| 필드 | 설명 |
|-----------|------|
| `inputTokens` | 입력토큰수 |
| `outputTokens` | 출력토큰수 |
| `cacheReadInputTokens` | 캐시읽기 |
| `cacheCreationInputTokens` | 캐시생성 |
| `webSearchRequests` | Web검색수 |
| `costUSD` | 그모델의코스트 |
| `contextWindow` | 컨텍스트ウィンドウサイズ |

### 5.3 스트리밍JSON출력(`--output-format stream-json`)

실행명령어：
```bash
claude -p --output-format stream-json --verbose "2+2は？"
```

출력(JSONL형식 - 복수이벤트)：

**이벤트1: 초기화**
```json
{
 "type": "system",
 "subtype": "init",
 "cwd": "/home/user/project",
 "session_id": "565b60b3-1ee7-43da-9001-03e4ff9b40ee",
 "tools": ["Agent", "Bash", "Glob", "Grep", "Read", "Edit", "Write", "..."],
 "mcp_servers": [
 {"name": "context7", "status": "connected"}
 ],
 "model": "claude-opus-4-6",
 "permissionMode": "default",
 "slash_commands": ["compact", "context", "cost", "..."],
 "agents": ["general-purpose", "Explore", "Plan", "..."],
 "claude_code_version": "2.1.71"
}
```

**이벤트2: アシスタント응답**
```json
{
 "type": "assistant",
 "message": {
 "model": "claude-opus-4-6",
 "id": "msg_0125ShwoNM22AEWJtiLyCYcN",
 "type": "message",
 "role": "assistant",
 "content": [{"type": "text", "text": "4입니다."}],
 "stop_reason": null,
 "usage": {
 "input_tokens": 3,
 "cache_creation_input_tokens": 31823,
 "output_tokens": 2
 }
 },
 "session_id": "565b60b3-1ee7-43da-9001-03e4ff9b40ee"
}
```

**이벤트3: 결과**
```json
{
 "type": "result",
 "subtype": "success",
 "result": "4입니다.",
 "session_id": "565b60b3-1ee7-43da-9001-03e4ff9b40ee",
 "total_cost_usd": 0.203442,
 "usage": {"..."},
 "modelUsage": {"..."}
}
```

#### stream-json 이벤트타입

| type | subtype | 설명 |
|------|---------|------|
| `system` | `init` | 초기화정보(도구, MCP, 설정등) |
| `system` | `compact_boundary` | コンパクション발생 |
| `assistant` | - | アシスタント의 응답메시지 |
| `result` | `success` / `error` | 최종결과 |

### 5.4 구조화 출력(`--json-schema`)

에이전트완료後にJSON스키마에沿った검증완료JSON출력를취득：

```bash
claude -p --json-schema '{
 "type": "object",
 "properties": {
 "summary": {"type": "string"},
 "issues": {"type": "array", "items": {"type": "string"}}
 },
 "required": ["summary", "issues"]
}' "이프로젝트의문제点를 분석하여"
```

### 5.5 스트림チェイニング(`--input-format stream-json`)

에이전트間의 파이프라인를구축：

```bash
claude -p --output-format stream-json "코드를분석" \
 | claude -p --input-format stream-json --output-format stream-json "결과를처리" \
 | claude -p --input-format stream-json "최종レポート"
```

---

## 6. 서브에이전트

### 6.1 개요

서브에이전트는独自의 컨텍스트ウィンドウ, 시스템프롬프트, 도구접근를 가진다特화타입AIアシスタント.태스크에応じてClaude 이 자동적에 위임한다.

### 6.2 ビルト인서브에이전트

| 에이전트 | 모델 | 도구 | 용도 |
|-------------|--------|--------|------|
| **Explore** | Haiku | 읽기전용 | 코드ベース검색·분석 |
| **Plan** | 상속 | 읽기전용 | 플랜모드시의 조사 |
| **general-purpose** | 상속 | 전도구 | 복잡な멀티스텝태스크 |
| **Bash** | 상속 | 터미널 | 별컨텍스트로의명령어실행 |
| **Claude Code Guide** | Haiku | - | Claude Code 기능의질문대응 |

### 6.3 커스텀서브에이전트정의

#### 파일ベース(Markdown파일 + YAML frontmatter)

저장場所:

| 場所 | 스코프 | 우선度 |
|------|---------|--------|
| `--agents` CLI 플래그 | 현세션만 | 최고 |
| `.claude/agents/` | 프로젝트 | 高 |
| `~/.claude/agents/` | 유저전체 | 中 |
| 플러그인의 `agents/` | 플러그인유효범위 | 低 |

#### frontmatter 필드

| 필드 | 필수 | 설명 |
|-----------|------|------|
| `name` | Yes | 一意識별子(小문자+ハイフン) |
| `description` | Yes | 위임판단에사용하다自然언어의설명 |
| `tools` | No | 사용가능도구.생략時는 전도구상속 |
| `disallowedTools` | No | 금지도구 |
| `model` | No | `sonnet`, `opus`, `haiku`, `inherit`(기본값: `inherit`) |
| `permissionMode` | No | 권한모드 |
| `maxTurns` | No | 최대턴수 |
| `skills` | No | プリ로드한다스킬 |
| `mcpServers` | No | MCP 서버 |
| `hooks` | No | ライフ사이클훅 |
| `memory` | No | 영속메모리스코프(`user`, `project`, `local`) |
| `background` | No | 백그라운드실행(`true`/`false`) |
| `isolation` | No | `worktree` 로 격리된작업복사로 실행 |

#### 파일예

```markdown
---
name: code-reviewer
description: Expert code review specialist. Use proactively after code changes.
tools: Read, Glob, Grep, Bash
model: sonnet
---

You are a senior code reviewer. Focus on code quality, security, and best practices.
Review checklist:
- Code clarity and readability
- Error handling
- Security vulnerabilities
- Test coverage
```

### 6.4 CLI에서의서브에이전트정의(`--agents`)

```bash
claude --agents '{
 "code-reviewer": {
 "description": "Expert code reviewer. Use proactively after code changes.",
 "prompt": "You are a senior code reviewer.",
 "tools": ["Read", "Grep", "Glob", "Bash"],
 "model": "sonnet"
 },
 "debugger": {
 "description": "Debugging specialist for errors and test failures.",
 "prompt": "You are an expert debugger. Analyze errors and provide fixes."
 }
}'
```

### 6.5 메인에이전트로서의기동(`--agent`)

```bash
# 특정의 에이전트를메인로서기동
claude --agent my-custom-agent "태스크를 실행하여"
```

`--agent` 로 기동한에이전트는 `Agent(agent_type)` 구문로서브에이전트의생성를제한할 수 있다.

---

## 7. Worktree & 병렬실행

### 7.1 Git Worktree 통합(`--worktree` / `-w`)

```bash
# 이름付きworktree로 기동(.claude/worktrees/feature-auth/ 에 생성)
claude -w feature-auth

# 자동命名でworktree생성
claude -w

# worktree + tmux 세션
claude -w feature-auth --teammate-mode tmux
```

### 7.2 에이전트팀표시모드(`--teammate-mode`)

| 모드 | 설명 |
|--------|------|
| `auto` | 기본값(자동선택) |
| `in-process` | 프로세스내표시 |
| `tmux` | tmux 세션로표시 |

### 7.3 서브에이전트의 worktree 격리

```yaml
---
name: experimental-refactor
description: Experimental code refactoring in isolation
isolation: worktree
---
```

---

## 8. 실전적인사용패턴

### 8.1 단일에이전트(シンプル)

```bash
# 세션시작
claude -p "태스크1를 시작"

# 최신세션를계속
claude -p -c "이어서의 작업"
```

### 8.2 복수에이전트의병렬실행

```bash
#!/bin/bash

# 에이전트1: 코드 리뷰
SESSION_REVIEW=$(claude -p --output-format json \
 --system-prompt "あなた는 코드리뷰어입니다" \
 "리뷰를 시작" | jq -r '.session_id')

# 에이전트2: 테스트생성
SESSION_TEST=$(claude -p --output-format json \
 --system-prompt "あなた는 테스트エンジニア입니다" \
 "테스트생성를시작" | jq -r '.session_id')

echo "Review Session: $SESSION_REVIEW"
echo "Test Session: $SESSION_TEST"

# 각세션를개별에계속
claude -p -r "$SESSION_REVIEW" "src/main.py 를 리뷰하여"
claude -p -r "$SESSION_TEST" "ユニット테스트를추가하여"
```

### 8.3 코스트관리패턴

```bash
# 코스트상한付き로 실행
claude -p --max-budget-usd 5.00 "복잡한 리팩터링태스크"

# 코스트를 취득하여기록
RESULT=$(claude -p --output-format json "태스크")
COST=$(echo "$RESULT" | jq '.total_cost_usd')
SESSION=$(echo "$RESULT" | jq -r '.session_id')
echo "Session: $SESSION, Cost: \$$COST"
```

### 8.4 모델전환패턴

```bash
# 軽い태스크는Haiku
claude -p --model haiku "簡単な질문"

# 복잡한 태스크는Opus
claude -p --model opus "복잡한 분석"

# Sonnetでバランス
claude -p --model sonnet "통상의태스크"

# 폴백付き(과부하時にsonnetへ자동전환)
claude -p --model opus --fallback-model sonnet "중요한 태스크"

# opusplan: 플랜時Opus, 실행時Sonnet
claude --model opusplan "설계와구현"
```

### 8.5 턴수제한패턴

```bash
# 최대3턴로 종료(無限ループ방지)
claude -p --max-turns 3 "簡単な수정"
```

### 8.6 커스텀에이전트에 의한CI/CD파이프라인

```bash
# 세션영속화없음로CI실행
claude -p --no-session-persistence \
 --max-budget-usd 2.00 \
 --max-turns 5 \
 --output-format json \
 --allowedTools "Bash(npm *)" "Read" "Grep" "Glob" \
 "테스트를 실행하여결과를보고"
```

### 8.7 Worktree を使った병렬 개발

```bash
# 기능A: worktree + tmux
claude -w feature-a --teammate-mode tmux "인증기능를구현"

# 기능B: 별의 worktree
claude -w feature-b --teammate-mode tmux "API엔드포인트를구현"
```

---

## 9. 이용가능한 모델

### 9.1 모델에일리어스

| 에일리어스 | 현재의모델 | 특징 |
|-----------|-------------|------|
| `default` | 어카운트타입의존 | Max/Team Premium → Opus 4.6, Pro/Team Standard → Sonnet 4.6 |
| `sonnet` | Sonnet 4.6 (`claude-sonnet-4-6`) | バランス타입·日常コーディング |
| `opus` | Opus 4.6 (`claude-opus-4-6`) | 高성능·복잡な推論 |
| `haiku` | Haiku 4.5 | 경량·고속·低코스트 |
| `sonnet[1m]` | Sonnet 4.6(1M컨텍스트) | 大규모코드ベース용 |
| `opusplan` | Opus(plan) + Sonnet(실행) | 플랜時にOpus의推論力, 실행時にSonnet의효율 |

### 9.2 확장컨텍스트

Opus 4.6 과 Sonnet 4.6 는 **100万토큰의컨텍스트ウィンドウ** 를 지원(베타).

```bash
# 1M 컨텍스트를 사용
claude --model sonnet[1m]
```

- 200K토큰까지는통상料金
- 200K超はロング컨텍스트料金이 적용
- `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` 로 무효화가능

### 9.3 Effort Level(適応적推論)

태스크의복잡さに応じて推論の深さ를 제어：

| 레벨 | 설명 |
|--------|------|
| `low` | 고속·低코스트(簡単な태스크용) |
| `medium` | バランス(Opus 4.6 의 기본값) |
| `high` | 깊은推論(복잡한 문제용) |

설정방법：
- **세션中**: `/model` でスライダー調整
- **환경변수**: `CLAUDE_CODE_EFFORT_LEVEL=low|medium|high`
- **설정파일**: `"effortLevel": "medium"`
- **키ワード**: `ultrathink` 로 일시적에 high effort

### 9.4 환경변수에 의한모델제어

| 환경변수 | 설명 |
|---------|------|
| `ANTHROPIC_MODEL` | 기본값모델설정 |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | `opus` 에일리어스의 모델지정 |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | `sonnet` 에일리어스의 모델지정 |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | `haiku` 에일리어스의 모델지정 |
| `CLAUDE_CODE_SUBAGENT_MODEL` | 서브에이전트의모델지정 |
| `CLAUDE_CODE_EFFORT_LEVEL` | Effort Level 설정 |
| `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING` | `1` で適応적推論를 무효화 |
| `CLAUDE_CODE_DISABLE_1M_CONTEXT` | `1` で1M컨텍스트를무효화 |

---

## 10. Codex CLI 와 의 비교

| 기능 | Claude Code | Codex CLI |
|------|------------|-----------|
| 비인터랙티브 | `-p` | `exec` |
| 세션계속(최신) | `-c` / `--continue` | `exec resume --last` |
| 세션계속(ID지정) | `-r <id>` / `--resume` | `exec resume <id>` |
| JSON출력 | `--output-format json` | `--json` |
| 스트리밍 | `--output-format stream-json` | JSONL형식(기본값) |
| 모델지정 | `--model` | `-m` |
| 시스템프롬프트 | `--system-prompt` | `-c` 로 설정 |
| 도구제어 | `--allowedTools` / `--tools` | MCP설정 |
| 코스트정보 | `total_cost_usd` | `usage.input_tokens` 등 |
| 코스트상한 | `--max-budget-usd` | 없음 |
| 턴상한 | `--max-turns` | 없음 |
| 작업디렉토리 | カレント고정 / `--add-dir` | `-C` 로 지정 |
| 서브에이전트 | `--agent` / `--agents` | 없음 |
| Worktree통합 | `--worktree` / `-w` | 없음 |

### 主な차이

1. **세션ID형식**
 - Claude Code: UUID형식(`4c5a56e4-7a81-4603-a105-947e81bbfd6a`)
 - Codex CLI: UUID형식(`019ac5b0-190b-75c0-bf3e-5f1acf69fcce`)

2. **JSON구조**
 - Claude Code: 단일JSON오브젝트 or JSONL
 - Codex CLI: JSONL(常에 이벤트ベース)

3. **코스트정보**
 - Claude Code: `total_cost_usd` で総코스트, `modelUsage` 로 모델별코스트
 - Codex CLI: 토큰수만(코스트계산는별途필요)

4. **에이전트기능**
 - Claude Code: 서브에이전트, 에이전트팀, worktree 격리
 - Codex CLI: シンプルな단일에이전트

---

## 11. トラブルシューティング

### 11.1 stream-json 로 에러

```
Error: When using --print, --output-format=stream-json requires --verbose
```

→ `--verbose` 옵션를추가：
```bash
claude -p --output-format stream-json --verbose "질문"
```

### 11.2 세션계속이 느린

`-c` 로 의 계속는過去의 컨텍스트를읽어들이는위해時間がかかる경우이 있다.

→ 짧은세션로는신규시작의方이 고속한 경우도.

### 11.3 권한에러

```bash
# 권한를완화(위험：격리환경만)
claude -p --permission-mode bypassPermissions "태스크"

# 또는특정도구만허가
claude -p --allowedTools "Read" "Glob" "Grep" "조사태스크"
```

### 11.4 코스트초과

```bash
# 예산상한를설정
claude -p --max-budget-usd 1.00 "태스크"
```

### 11.5 서브에이전트이使われ없다

→ 서브에이전트의 `description` 필드를구체적에기술.`"Use proactively"` 를 포함하다와자동위임されやすい.

### 11.6 Worktree 의 경합

→ `claude -w <name>` 로 이름를明示지정.자동命名의 경우는 `.claude/worktrees/` 를 확인.

---

## 12. 참고링크

- [Claude Code 공식문서](https://docs.anthropic.com/claude-code)
- [서브에이전트](https://code.claude.com/docs/en/sub-agents)
- [모델설정](https://code.claude.com/docs/en/model-config)
- [권한설정](https://code.claude.com/docs/en/permissions)
- [Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview)
- [구조화 출력](https://platform.claude.com/docs/en/agent-sdk/structured-outputs)
- [Claude API 레퍼런스](https://platform.claude.com/docs/en/api)
- [Anthropic 価格表](https://www.anthropic.com/pricing)

---

## 13. 一次정보와검증상황

| 정보 | 一次정보源 | 검증방법 | 검증일 |
|------|-----------|---------|--------|
| 명령어옵션 | `claude --help` (v2.1.71) | 로컬실행 | 2026-03-09 |
| JSON출력포맷 | 実機검증(v2.0.55時点) | 로컬실행 | 2025-11-27 |
| stream-json 포맷 | 実機검증(v2.0.55時点) | 로컬실행 | 2025-11-27 |
| 세션관리 | 実機검증(v2.0.55時点) | 로컬실행 | 2025-11-27 |
| 서브에이전트 | Web검색(공식문서) | 未実機검증 | 2026-03-09 |
| Worktree통합 | Web검색 | 未実機검증 | 2026-03-09 |
| Effort Level | Web검색 + `claude --help` | 부분검증 | 2026-03-09 |
| 모델에일리어스 | Web검색 | 未実機검증 | 2026-03-09 |
| 퍼미션구문(와일드카드) | Web검색 | 未実機검증 | 2026-03-09 |
| 확장컨텍스트(1M) | Web검색 | 未実機검증 | 2026-03-09 |

> **주의**: "未実機검증"의 항목는Web검색결과에 기반한.버전업에 의해사양이변경되어 있다가능性이 있다.
> 実機로 검증하는 경우는 `claude --help` 로 최신사양를확인한다것.
> 참고URLが実在한다かは未검증.접근할 수 없다경우는공식문서(https://docs.anthropic.com/claude-code)부터辿る것.

---

## 변경履歴

| 日付 | 내용 |
|------|------|
| 2026-03-09 | `--file`형식수정, `--effort`/`--debug-file`추가, 一次정보섹션추가, 공식URL를 수정 |
| 2026-03-09 | v2.1.71+대응: 서브에이전트, worktree통합, effort level, 1M컨텍스트, 新CLI옵션多数추가, 와일드카드구문업데이트, 모델정보업데이트 |
| 2025-11-27 | 初版생성 |
