# Gemini CLI 세션관리가이드

## 개요

Gemini CLI 의 세션관리기능에関한다조사결과를まとめた資料.
비인터랙티브모드로의세션인수인계やJSON출력의상세를기재.

**조사日**: 2026-03-09
**--help 취득버전**: v0.31.0(로컬환경, 2026-03-09 취득)
**Web검색에 의한최신정보**: v0.32.1(2026-03-04 릴리스)
**공식문서**: https://geminicli.com/docs/
**GitHub**: https://github.com/google-gemini/gemini-cli

---

## 1. 기본명령어구조

### 1.1 인터랙티브모드(기본값)

```bash
gemini [OPTIONS]
```

### 1.2 비인터랙티브모드

```bash
gemini "프롬프트" # 位置인수(추천)
gemini -p "프롬프트" # -p 옵션(비추천)
echo "프롬프트" | gemini # stdin
```

**주의**: `-p` / `--prompt` 는 비추천.位置인수의사용이추천되어 있다.

---

## 2. 이용가능한 파라미터

### 2.1 주요옵션

| 옵션 | 축약형 | 타입 | 기본값 | 설명 |
|-----------|--------|-----|-----------|------|
| `--model` | `-m` | string | `auto` | 사용모델 |
| `--output-format` | `-o` | string | `text` | 출력형식(`text` / `json` / `stream-json`) |
| `--resume` | `-r` | string | — | 세션재개 |
| `--prompt` | `-p` | string | — | 프롬프트(**비추천**) |
| `--prompt-interactive` | `-i` | string | — | 프롬프트실행후인터랙티브계속 |
| `--sandbox` | `-s` | boolean | `false` | 샌드박스모드 |
| `--approval-mode` | — | string | `default` | 도구승인모드 |
| `--yolo` | `-y` | boolean | `false` | 전アクション자동승인(**비추천**: `--approval-mode yolo` 를 사용) |
| `--debug` | `-d` | boolean | `false` | 디버그모드 |
| `--version` | `-v` | — | — | 버전표시 |
| `--help` | `-h` | — | — | ヘルプ표시 |
| `--screen-reader` | — | boolean | — | アクセシビリティ모드 |
| `--experimental-acp` | — | boolean | — | ACP(Agent Code Pilot)모드 |
| `--raw-output` | — | boolean | `false` | 모델출력의サニタイズ무효화(예: ANSI이스케이프シーケンス를 허가).**경고**: 신뢰할 수 없다모델출력로는보안リスク있음 |
| `--accept-raw-output-risk` | — | boolean | `false` | `--raw-output` 사용시의 보안경고를抑制 |
| `--experimental-zed-integration` | — | boolean | — | Zed エディタ통합모드(Web검색정보, v0.31.0 의 --help に未기재) |

### 2.2 세션관리옵션

| 옵션 | 설명 | 예 |
|-----------|------|-----|
| `--resume` | 세션재개 | `-r latest` / `-r 3` / `-r <uuid>` |
| `--list-sessions` | 세션목록표시 | `--list-sessions` |
| `--delete-session` | 세션삭제 | `--delete-session 3` |

### 2.3 출력형식옵션

| 옵션 | 설명 |
|-----------|------|
| `-o text` | 텍스트형식(기본값) |
| `-o json` | JSON형식(단일결과) |
| `-o stream-json` | 스트리밍JSON(JSONL) |

### 2.4 승인모드옵션

| 옵션 | 설명 |
|-----------|------|
| `--approval-mode default` | 승인를求める(기본값) |
| `--approval-mode auto_edit` | 편집도구(`write_file`, `replace`)자동승인, シェル명령어는要승인 |
| `--approval-mode yolo` | 전도구자동승인(샌드박스이자동유효화) |
| `-y` / `--yolo` | 전アクション자동승인(**비추천**: `--approval-mode yolo` 를 추천) |

### 2.5 도구·확장기능옵션

| 옵션 | 설명 | 예 |
|-----------|------|-----|
| `--allowed-tools` | 확인없음로 실행가능한 도구(**비추천**: Policy Engine 를 사용) | `--allowed-tools run_shell_command` |
| `--policy` | 유저정의ポリシー파일(v0.30.0+) | `--policy ./my-policy.toml` |
| `--allowed-mcp-server-names` | 허가하는 MCP서버 | `--allowed-mcp-server-names server1` |
| `--extensions` | 사용한다확장기능 | `-e ext1 ext2` |
| `--list-extensions` | 확장기능목록표시 | `-l` |
| `--include-directories` | 추가ワーク스페이스디렉토리 | `--include-directories /path1,/path2` |

---

## 2.6 비인터랙티브모드로의 도구제한(중요)

**최종조사日**: 2026-03-09

### 2.6.1 문제의배경

비인터랙티브모드(`gemini "프롬프트"` 와 `gemini -o stream-json "프롬프트"`)로は, **보안上의 이유로도구의 이용이제한된다**.

인터랙티브모드로이용가능한 이하의도구이, 기본값로는무효화되어 있다：

| 도구명 | 기능 | 비인터랙티브시의 기본값 |
|---------|------|-------------------------------|
| `run_shell_command` | シェル명령어실행(`gh`, `git`, `npm`, `uv` 등) | 무효 |
| `write_file` | 파일쓰기 | 무효 |
| `replace` | 파일내텍스트치환 | 무효 |
| `read_file` | 파일읽기 | 유효 |
| `list_directory` | 디렉토리목록 | 유효 |
| `glob` | 파일검색 | 유효 |

### 2.6.2 에러예

```bash
# 실패한다예
gemini -o stream-json "gh issue view 182 --json title 를 실행하여"
```

```json
{
 "type": "tool_result",
 "status": "error",
 "error": {
 "type": "tool_not_registered",
 "message": "Tool \"run_shell_command\" not found in registry."
 }
}
```

### 2.6.3 해결策

#### 방법1: `--allowed-tools` 플래그(レガシー, 비추천)

v0.30.0 이후 `--allowed-tools` 는 비추천.단하위 호환性때문引き続き동작한다：

```bash
# レガシー방식(동작는한다이비추천)
gemini --allowed-tools run_shell_command -o stream-json "gh issue view 182 --json title 를 실행하여"
```

#### 방법2: Policy Engine(v0.30.0+ 추천)

ポリシー파일(TOML)로도구허가를선언적에관리한다：

```bash
# ポリシー디렉토리의생성
mkdir -p ~/.gemini/policies
```

```toml
# ~/.gemini/policies/allow-shell.toml
[[rule]]
toolName = "run_shell_command"
decision = "allow"
priority = 100

[[rule]]
toolName = "write_file"
decision = "allow"
priority = 100
```

```bash
# Policy Engine 방식
gemini -o stream-json "gh issue view 182 --json title 를 실행하여"
```

ポリシー파일는 `~/.gemini/policies/` 에 배치すれば자동읽기된다.`--policy` 플래그로명시적에지정한다것도가능.

#### 방법3: `--approval-mode yolo`

```bash
# 전도구자동승인(샌드박스이자동유효화된다)
gemini --approval-mode yolo -o stream-json "gh issue view 182 --json title 를 실행하여"
```

### 2.6.4 Policy Engine 의 기지의문제(v0.30.0+)

**중요**: 비인터랙티브모드 + `--approval-mode auto_edit` の組み合わせでは, Policy Engine 의 `allow` 규칙이無視된다기지의문제이 있다([Issue #20469](https://github.com/google-gemini/gemini-cli/issues/20469)).

원인: CLI 의 설정레이어이 `auto_edit` 모드 + 비인터랙티브時にハード코드된제외리스트를적용し, `run_shell_command` 이 도구레지스트리에등록되지 않는다.Policy Engine 의 규칙보다도이제외이우선된다.

**회피策**: 비인터랙티브모드로는 `--approval-mode yolo` 를 사용한다인가, レガシー의 `--allowed-tools` 플래그를병용한다.

### 2.6.5 `run_shell_command` 의 상세

#### 인수

| 인수 | 필수 | 타입 | 설명 |
|-----|------|-----|------|
| `command` | 필수 | string | 실행한다シェル명령어 |
| `description` | 임의 | string | 유저확인용텍스트 |
| `dir_path` | 임의 | string | 실행디렉토리(絶対경로또는ワーク스페이스루트상대) |
| `is_background` | 임의 | boolean | 백그라운드실행 |

#### 반환값

```json
{
 "Command": "git status",
 "Directory": "/path/to/project",
 "Stdout": "...",
 "Stderr": "...",
 "Exit Code": 0,
 "Background PIDs": []
}
```

#### 설정에 의한명령어제한

```json
// settings.json
{
 "tools": {
 "core": ["run_shell_command(git)", "run_shell_command(npm)"],
 "exclude": ["run_shell_command(rm)"]
 }
}
```

프리픽스매치ング로 제어.블록리스트는アロー리스트에우선한다.명령어체인(`&&`, `||`, `;`)는각컴포넌트이개별에검증된다.

#### 실행가능한 명령어예

| 카테고리 | 명령어예 | 검증결과 |
|---------|-----------|---------|
| **GitHub CLI** | `gh issue view`, `gh pr create`, `gh api` | 성공 |
| **Git** | `git status`, `git log`, `git diff`, `git add`, `git commit` | 성공 |
| **Python개발** | `pytest`, `python3`, `pip install`, `uv` | 성공 |
| **Node.js개발** | `npm install`, `npm test`, `npm run build` | 성공 |
| **Docker** | `docker compose up -d`, `docker ps` | 성공 |
| **파일조작** | `ls`, `find`, `cat`, `mkdir`, `rm`, `touch`, `mv`, `cp` | 성공 |

### 2.6.6 제약事項

| 제약 | 설명 | 대처法 |
|-----|------|--------|
| **비대화타입만** | `vim`, `nano`, 대화타입シェル(`python` REPL)는실행불가 | `enableInteractiveShell: true` 로 대응가능(인터랙티브모드시만) |
| **프롬프트회피** | 유저입력待ち의 명령어는실패 | `-y`, `--yes`, `--force` 등의플래그사용 |
| **배경프로세스** | 長時間실행는 `is_background: true` 로 배경실행 | PID 이 반환된다 |
| **환경변수** | 실행시에 `GEMINI_CLI=1` 이 자동설정된다 | 스크립트内で検出가능 |

### 2.6.7 보안고려事項

| 방식 | 플래그/설정 | 보안 | 추천度 |
|-----|-----------|------------|--------|
| **Policy Engine** | `~/.gemini/policies/*.toml` | 高(선언적·細粒度제어) | 추천(v0.30.0+) |
| **ホワイト리스트** | `--allowed-tools run_shell_command` | 中(필요한 도구만허가, 비추천) | レガシー |
| **YOLO** | `--approval-mode yolo` | 低(전도구자동승인, 샌드박스자동유효화) | 주의 |
| **기본값** | 없음 | 최고(도구제한) | 안전 |

**주의**: `--approval-mode yolo` 는 개발·테스트시만사용.본번워크플로우로는 Policy Engine 에 의한ポリシー관리를추천.

### 2.6.8 bugfix-agent 로 의 구현

`bugfix_agent_orchestrator.py` 의 `GeminiTool.run()` で는 이하처럼구현：

```python
# CLI 인수를구축
args = ["gemini", "-o", "stream-json"]
if self.model != "auto":
 args += ["-m", self.model]
if session_id:
 args += ["-r", session_id]
# Enable run_shell_command tool for gh/shell operations in non-interactive mode
# Note: Gemini CLI restricts tools by default in non-interactive mode for security.
# Using --allowed-tools whitelist is the recommended approach.
# TODO: v0.30.0+ 로 는 Policy Engine 로의移행를검토
args += ["--allowed-tools", "run_shell_command"]
args.append(full_prompt)
```

이구현에 의해, INVESTIGATE / IMPLEMENT / PR_CREATE 스테이트로 `gh` 명령어이정상에동작한다.

**移행가이드**: v0.30.0+ 로 는 `--allowed-tools` 는 비추천.이하의ポリシー파일로동등의제어이가능：

```toml
# .gemini/policies/bugfix-agent.toml(ワーク스페이스레벨)
[[rule]]
toolName = "run_shell_command"
decision = "allow"
priority = 100
```

---

## 3. Policy Engine(v0.30.0+)

### 3.1 개요

Policy Engine 는 `--allowed-tools` に代わる선언적한 도구제어メカニズム.TOML 파일로규칙를 정의し, 도구실행의허가·거부·확인를細粒度로 제어한다.

### 3.2 ポリシー파일의배치

| ティア | 배치場所 | 우선度(ベース) |
|-------|---------|---------------|
| Default | CLI 組み込み | 1 |
| Extension | 확장기능정의 | 2 |
| Workspace | `$WORKSPACE_ROOT/.gemini/policies/*.toml` | 3 |
| User | `~/.gemini/policies/*.toml` | 4 |
| Admin (Linux) | `/etc/gemini-cli/policies/*.toml` | 5 |
| Admin (macOS) | `/Library/Application Support/GeminiCli/policies/*.toml` | 5 |

최종우선度 = `tier_base + (toml_priority / 1000)`

### 3.3 규칙구문

```toml
# 기본규칙
[[rule]]
toolName = "run_shell_command"
decision = "allow"
priority = 100

# 명령어프리픽스에 의한제한
[[rule]]
toolName = "run_shell_command"
commandPrefix = "git "
decision = "allow"
priority = 200

# 정규表現에 의한제한
[[rule]]
toolName = "run_shell_command"
commandRegex = "^(git|gh|npm|pytest) "
decision = "allow"
priority = 200

# MCP 도구의 제어
[[rule]]
mcpName = "my-server"
toolName = "search"
decision = "allow"
priority = 200

# 복수도구로의적용
[[rule]]
toolName = ["write_file", "replace"]
decision = "ask_user"
priority = 10

# 와일드카드
[[rule]]
toolName = "my-server__*"
decision = "allow"
priority = 150
```

### 3.4 결정타입

| Decision | 동작 | 비인터랙티브시 |
|----------|------|-------------------|
| `allow` | 자동실행 | 자동실행 |
| `deny` | 블록(deny_message 를 모델에반환) | 블록 |
| `ask_user` | 유저에 확인를求める | **거부로서扱われる** |

### 3.5 비인터랙티브모드용추천설정

```toml
# ~/.gemini/policies/non-interactive.toml

# シェル명령어를허가(git, gh に限定)
[[rule]]
toolName = "run_shell_command"
commandRegex = "^(git|gh) "
decision = "allow"
priority = 200

# 파일쓰기를허가
[[rule]]
toolName = ["write_file", "replace"]
decision = "allow"
priority = 100

# 기타シェル명령어는거부
[[rule]]
toolName = "run_shell_command"
decision = "deny"
deny_message = "Only git and gh commands are allowed in non-interactive mode"
priority = 50
```

---

## 4. 세션관리

### 4.1 세션계속옵션

| 지정방법 | 설명 | 예 |
|---------|------|-----|
| `latest` | 최신의세션를재개 | `-r latest` |
| 번호 | 번호로세션지정 | `-r 3` |
| UUID | UUID로 세션지정 | `-r 9d4614fb-e818-45fc-afab-77924f34a5a5` |

### 4.2 세션목록의확인

```bash
gemini --list-sessions
```

출력예：
```
Available sessions for this project (3):

 1. https://github.com/apokamo/kamo2/issues/184#issuecomment-... (2 days ago) [0de5286d-a4c6-4f03-9643-cf234bd232e8]
 2. 현재의ドル円を調べて (23 hours ago) [ff240b43-faa2-4136-ada3-cc90fda7ce44]
 3. 2+2は？ (Just now) [9d4614fb-e818-45fc-afab-77924f34a5a5]
```

### 4.3 세션ID의취득방법

#### JSON출력부터취득(단일결과)

```bash
# JSONにはsession_idが含まれ없다이, --list-sessions로 확인가능
gemini "태스크시작" -o json
gemini --list-sessions | tail -1 # 최신세션를확인
```

#### stream-json출력부터취득

```bash
SESSION_ID=$(gemini "태스크시작" -o stream-json 2>&1 | \
 grep '"type":"init"' | jq -r '.session_id')
echo $SESSION_ID
# 출력예: 0a1bbf60-f74d-44c1-bd2c-15eeaf376d38
```

### 4.4 세션인수인계의예

```bash
# 신규세션시작
gemini "1+1は？" -o json

# 최신세션를계속
gemini -r latest -p "그答えに2を足すと？" -o json

# 번호로세션지정
gemini -r 3 -p "더욱10を足すと？" -o json

# UUID로 세션지정
gemini -r 9d4614fb-e818-45fc-afab-77924f34a5a5 -p "이어서의 계산" -o json
```

**주의**: resume時는 `-p` 로 프롬프트를지정한다인가, stdin로 전달하다필요이 있다.

### 4.5 세션의삭제

```bash
gemini --delete-session 3 # 번호로삭제
```

---

## 5. JSON출력의상세

### 5.1 기본JSON출력(`-o json`)

실행명령어：
```bash
gemini "2+2は？" -o json
```

출력(정형완료)：
```json
{
 "response": "4입니다.",
 "stats": {
 "models": {
 "gemini-2.5-flash-lite": {
 "api": {
 "totalRequests": 1,
 "totalErrors": 0,
 "totalLatencyMs": 1650
 },
 "tokens": {
 "prompt": 3154,
 "candidates": 50,
 "total": 3312,
 "cached": 0,
 "thoughts": 108,
 "tool": 0
 }
 },
 "gemini-2.5-flash": {
 "api": {
 "totalRequests": 1,
 "totalErrors": 0,
 "totalLatencyMs": 2864
 },
 "tokens": {
 "prompt": 7584,
 "candidates": 3,
 "total": 7625,
 "cached": 0,
 "thoughts": 38,
 "tool": 0
 }
 }
 },
 "tools": {
 "totalCalls": 0,
 "totalSuccess": 0,
 "totalFail": 0,
 "totalDurationMs": 0,
 "totalDecisions": {
 "accept": 0,
 "reject": 0,
 "modify": 0,
 "auto_accept": 0
 },
 "byName": {}
 },
 "files": {
 "totalLinesAdded": 0,
 "totalLinesRemoved": 0
 }
 }
}
```

### 5.2 JSON출력의필드설명

#### 탑레벨필드

| 필드 | 설명 |
|-----------|------|
| `response` | 최종회答텍스트 |
| `stats` | 統計정보 |

#### stats.models 필드(모델마다)

| 필드 | 설명 |
|-----------|------|
| `api.totalRequests` | API리퀘스트수 |
| `api.totalErrors` | 에러수 |
| `api.totalLatencyMs` | 레이턴시(ミリ초) |
| `tokens.prompt` | 프롬프트토큰수 |
| `tokens.candidates` | 候補토큰수 |
| `tokens.total` | 総토큰수 |
| `tokens.cached` | 캐시토큰수 |
| `tokens.thoughts` | 思考토큰수 |
| `tokens.tool` | 도구토큰수 |

#### stats.tools 필드

| 필드 | 설명 |
|-----------|------|
| `totalCalls` | 도구호출수 |
| `totalSuccess` | 성공수 |
| `totalFail` | 실패수 |
| `totalDurationMs` | 総실행時間 |
| `totalDecisions` | 승인판정統計 |
| `byName` | 도구별統計 |

#### stats.files 필드

| 필드 | 설명 |
|-----------|------|
| `totalLinesAdded` | 추가행수 |
| `totalLinesRemoved` | 삭제행수 |

### 5.3 스트리밍JSON출력(`-o stream-json`)

실행명령어：
```bash
gemini "3+3は？" -o stream-json
```

출력(JSONL형식 - 각행이1이벤트)：

**이벤트1: 초기화**
```json
{
 "type": "init",
 "timestamp": "2025-11-27T14:32:31.077Z",
 "session_id": "0a1bbf60-f74d-44c1-bd2c-15eeaf376d38",
 "model": "auto"
}
```

**이벤트2: 유저메시지**
```json
{
 "type": "message",
 "timestamp": "2025-11-27T14:32:31.077Z",
 "role": "user",
 "content": "3+3は？"
}
```

**이벤트3: アシスタント응답**
```json
{
 "type": "message",
 "timestamp": "2025-11-27T14:32:35.403Z",
 "role": "assistant",
 "content": "3+3は6입니다.",
 "delta": true
}
```

**이벤트4: 결과**
```json
{
 "type": "result",
 "timestamp": "2025-11-27T14:32:35.407Z",
 "status": "success",
 "stats": {
 "total_tokens": 10971,
 "input_tokens": 10738,
 "output_tokens": 57,
 "duration_ms": 4330,
 "tool_calls": 0
 }
}
```

#### stream-json 이벤트타입

| type | 설명 |
|------|------|
| `init` | 초기화(세션ID, 모델등) |
| `message` | 메시지(user/assistant) |
| `tool_use` | 도구호출(도구명, 파라미터) |
| `tool_result` | 도구실행결과(성공/에러) |
| `result` | 최종결과(統計정보포함하다) |

---

## 6. 이용가능한 모델

### 6.1 모델목록(v0.32.1 時点)

| 모델 | 설명 | 비고 |
|--------|------|------|
| `auto` | 자동선택(기본값) | 태스크복잡度に応じて라우팅 |
| `gemini-3.1-pro-preview` | 최신·최고성능(プ리뷰) | v0.31.0+ 일부유저에 제공 |
| `gemini-3-pro` | 高성능(Gemini 3世代) | v0.22.0+ 無料枠있음 |
| `gemini-3-flash` | 고속(Gemini 3世代) | v0.21.0+ |
| `gemini-2.5-pro` | 高성능(Gemini 2.5世代) | Gemini 3 Pro 의 제한도달시의 폴백 |
| `gemini-2.5-flash` | 고속·バランス타입 | シンプル태스크의기본값 |
| `gemini-2.5-flash-lite` | 경량·最速 | — |

### 6.2 Auto 라우팅

`auto` 모드로는, 프롬프트의복잡度에 기반하여모델이자동선택된다：

- **シンプルな프롬프트**: Gemini 2.5 Flash / 3 Flash
- **복잡한 프롬프트**: Gemini 3 Pro(유효시)/ Gemini 2.5 Pro

JSON 출력의 `stats.models` 필드로実際에 사용된모델를확인가능.

### 6.3 日次사용제한

- Gemini 3 Pro / 3.1 Pro Preview には日次사용제한있음
- 제한도달시는 Gemini 2.5 Pro 에 폴백
- Gemini 2.5 Pro にも独自の日次제한있음
- 용량에러時は指数バック오프에 의한리트라이옵션있음

### 6.4 비추천모델

| 모델 | 상태 | 移행선 |
|--------|------|--------|
| `gemini-3-pro-preview` | 2026-03-09 에 셧다운 | `gemini-3.1-pro-preview` |

---

## 7. 샌드박스모드

### 7.1 개요

샌드박스모드는, シェル명령어나 파일조작를컨테이너内로 격리실행한다기능.ホスト시스템로의영향를방지한다.

### 7.2 유효화방법

```bash
# 명령어플래그
gemini -s -p "analyze the code structure"

# 환경변수
export GEMINI_SANDBOX=true
gemini -p "run the test suite"

# settings.json
# { "sandbox": true }
```

환경변수의값: `true` / `docker` / `podman` / `sandbox-exec` / `runsc` / `lxc`

### 7.3 샌드박스방식

| 방식 | プラットフォーム | 격리레벨 | 설명 |
|-----|---------------|-----------|------|
| **macOS Seatbelt** | macOS | 中 | `sandbox-exec` 에 의한プロ파일ベース제어 |
| **Docker/Podman** | クロスプラットフォーム | 高 | 컨테이너ベース의 격리 |
| **gVisor/runsc** | Linux | 최고 | 유저스페이스カーネル에 의한완전격리 |
| **LXC/LXD** | Linux(실험적) | 高 | 풀시스템컨테이너 |

### 7.4 커스텀 Dockerfile

프로젝트고유의샌드박스이필요한 경우：

```dockerfile
# .gemini/sandbox.Dockerfile
FROM gemini-cli-sandbox:latest
RUN apt-get update && apt-get install -y python3 python3-pip
```

### 7.5 주의事項

- `--approval-mode yolo` 사용時는 샌드박스이자동유효화된다
- `SANDBOX_FLAGS` 환경변수로 Docker/Podman 에 커스텀플래그를주입가능
- `.gemini/.env` でCLI고유의환경변수를설정(프로젝트루트의 `.env` は読み込まれ없다)

---

## 8. MCP 서버지원

### 8.1 설정방법

`settings.json` 의 `mcpServers` でMCP서버를설정：

```json
{
 "mcpServers": {
 "serverName": {
 "command": "path/to/server",
 "args": ["--arg1", "value1"],
 "env": {"API_KEY": "$MY_API_TOKEN"},
 "cwd": "./server-directory",
 "timeout": 30000,
 "trust": false
 }
 }
}
```

### 8.2 トランスポート타입

| 타입 | 설정プロパティ | 설명 |
|-------|-------------|------|
| **Stdio** | `command` | 서브프로세스를기동し stdin/stdout 로 통신 |
| **SSE** | `url` | Server-Sent Events 엔드포인트 |
| **HTTP Streaming** | `httpUrl` | Streamable HTTP トランスポート |

### 8.3 CLI 에 의한추가

```bash
gemini mcp add [options] <name> <commandOrUrl> [args...]

# Stdio 서버(기본값)
gemini mcp add my-server python -m my_mcp_server

# SSE 서버
gemini mcp add -t sse my-sse-server http://localhost:8080/sse

# HTTP 서버
gemini mcp add -t http my-http-server http://localhost:3000/mcp
```

### 8.4 설정プロパティ

| プロパティ | 필수 | 타입 | 설명 |
|-----------|------|-----|------|
| `command` | いずれか1つ | string | Stdio 용의 실행경로 |
| `url` | いずれか1つ | string | SSE 엔드포인트 |
| `httpUrl` | いずれか1つ | string | HTTP Streaming 엔드포인트 |
| `args` | 임의 | string[] | 명령어인수 |
| `headers` | 임의 | object | 커스텀 HTTP 헤더 |
| `env` | 임의 | object | 환경변수(`$VAR` 전개대응) |
| `cwd` | 임의 | string | 작업디렉토리 |
| `timeout` | 임의 | number | 타임아웃(ms, 기본값 600,000) |
| `trust` | 임의 | boolean | 확인프롬프트를바이패스 |
| `includeTools` | 임의 | string[] | 도구의アロー리스트 |
| `excludeTools` | 임의 | string[] | 도구의 블록리스트 |

### 8.5 보안

- 환경변수는자동전개(POSIX: `$VAR`, Windows: `%VAR%`)
- API 키나 토큰 등의機密변수는ベース환경부터자동제거
- 명시적에 `env` 로 설정한변수만 MCP 서버에渡된다

---

## 9. 확장기능(Extensions)

### 9.1 개요

확장기능는, 프롬프트·MCP 서버·커스텀명령어를패키지화하여 Gemini CLI 의 기능를확장한다구조.

### 9.2 主な명령어

```bash
gemini --list-extensions # 확장기능목록
gemini -e ext1 ext2 # 확장기능를지정하여기동
gemini extensions config <ext> # 확장기능의설정관리
```

### 9.3 주요한 공식확장기능(v0.32.1 時点)

- Conductor: 플랜ニング支援
- Endor Labs: 코드분석
- Rill: データ분석
- Browserbase: Web 인タラクション
- Eleven Labs: 音声

### 9.4 v0.32.0+ 의 개선

- 확장기능의병렬읽기에 의해기동이고속화
- 커스텀テーマ의 확장기능정의(v0.28.0+)
- 확장기능설정의설치시프롬프트(v0.28.0+)
- 機密설정의시스템키체인저장

---

## 10. Plan Mode(v0.29.0+)

### 10.1 개요

Plan Mode は, 태스크실행前にGeminiと協力하여구현計画를 설계한다기능.

### 10.2 사용방법

```bash
# 인터랙티브모드로 /plan 명령어
/plan

# 또는自然언어로
"start a plan for refactoring the authentication module"
```

### 10.3 워크플로우

1. 태스크의설명를입력
2. Gemini 이 코드ベース를 분석し, 질문나 선택肢を提示
3. 유저이 방침를선택
4. 구현計画이 Markdown 파일로서생성
5. 외부エディタで計画의 확인·편집이가능(v0.32.0+)

### 10.4 Agent Skills 와 의 통합

Plan Mode 内로 스킬를유효화하면, 専門적인 지식이リサーチ·설계·計画페이즈를支援한다.

---

## 11. Agent Skills(v0.23.0+ 실험적, v0.26.0+ 기본값유효)

### 11.1 개요

Agent Skills は, 보안감사·クラウド배포·코드ベース移행 등의専門적인 능력를온デマンド로 제공한다구조.일반적인 컨텍스트파일와異되어, 필요時에 만컨텍스트ウィンドウ에 로드된다.

### 11.2 組み込み스킬

- `pr-creator`: PR 생성支援(v0.25.0+)
- `skill-creator`: 커스텀스킬생성支援(v0.26.0+)

### 11.3 関連명령어

```bash
/skills reload # 스킬의재읽기
/skills install <name> # 스킬의설치
/skills uninstall <name> # 스킬의アン설치
/agents refresh # 에이전트의업데이트
```

---

## 12. Hooks(v0.31.0+)

### 12.1 개요

`gemini hooks` 명령어는 Gemini CLI 의 훅기능를관리한다.Claude Code 에서의移행를지원한다 `migrate` 서브명령어이제공되어 있다.

### 12.2 명령어

```bash
gemini hooks <command> # 훅관리(에일리어스: hook)

# 서브명령어
gemini hooks migrate # Claude Code 의 훅를 Gemini CLI に移행
```

### 12.3 Claude Code 에서의移행

`gemini hooks migrate` 를 실행한다와, Claude Code 로 설정완료의 훅(pre-tool-use, post-tool-use 등)를 Gemini CLI 의 훅형식로 변환·移행한다.기존의 Claude Code 유저이 Gemini CLI に移행할 때에便利.

---

## 13. 인터랙티브명령어목록

v0.32.1 로 이용가능한 주요スラッシュ명령어：

| 명령어 | 설명 | 추가버전 |
|---------|------|--------------|
| `/help` | ヘルプ표시 | — |
| `/plan` | Plan Mode 를 시작 | v0.29.0 |
| `/model` | 모델전환 | — |
| `/settings` | 설정エディタ를 열다 | — |
| `/stats` | 세션統計표시 | — |
| `/rewind` | 会話履歴を巻き戻す | v0.27.0 |
| `/introspect` | 디버그정보표시 | v0.26.0 |
| `/prompt-suggest` | 프롬프트提案 | v0.28.0 |
| `/logout` | 인증정보클리어 | v0.23.0 |
| `/skills reload` | 스킬재읽기 | v0.24.0 |
| `/agents refresh` | 에이전트업데이트 | v0.24.0 |

---

## 14. 3CLI비교表

| 기능 | Gemini CLI (v0.32.1) | Claude Code | Codex CLI |
|------|---------------------|-------------|-----------|
| 비인터랙티브 | 位置인수 / `-p` | `-p` | `exec` |
| 세션계속(최신) | `-r latest` | `-c` | `resume --last` |
| 세션계속(ID지정) | `-r <번호/UUID>` | `-r <uuid>` | `resume <uuid>` |
| 세션목록 | `--list-sessions` | 없음 | 없음 |
| 세션삭제 | `--delete-session` | 없음 | 없음 |
| JSON출력 | `-o json` | `--output-format json` | `--json` |
| 스트리밍 | `-o stream-json` | `--output-format stream-json` | JSONL(기본값) |
| 모델지정 | `-m` | `--model` | `-m` |
| 자동승인 | `--approval-mode yolo` | `--permission-mode` | `--full-auto` |
| 도구제어 | Policy Engine(TOML) | — | — |
| 샌드박스 | `-s`(Docker/Podman/gVisor/Seatbelt/LXC) | — | — |
| MCP 지원 | `settings.json` / `gemini mcp add` | `claude mcp add` | — |
| Plan Mode | `/plan` | — | — |
| Agent Skills | 組み込み + 커스텀 | — | — |
| 코스트정보 | 없음 | `total_cost_usd` | 없음 |

### 主な차이

1. **세션관리**
 - Gemini: 번호·UUID両方로 지정가능, 목록·삭제기능있음
 - Claude: UUID만, 목록기능없음
 - Codex: UUID만, 목록기능없음

2. **세션ID의취득**
 - Gemini: `--list-sessions` 또는 stream-json의 `init` 이벤트
 - Claude: JSON출력의 `session_id`
 - Codex: JSON출력의 `thread_id`

3. **멀티모델**
 - Gemini: `auto` 로 복수모델자동라우팅(3世代 + 2.5世代)
 - Claude: 단일모델(전환는수동)
 - Codex: 단일모델(전환는수동)

4. **resume時의 프롬프트지정**
 - Gemini: `-p` 또는 stdin 필수
 - Claude: 位置인수또는 `-r` 후에에직접
 - Codex: 位置인수

5. **도구제어(v0.30.0+ の変화점)**
 - Gemini: Policy Engine 로 TOML ベース의 선언적제어, ティア별우선度
 - Claude: 組み込み의 권한관리
 - Codex: `--full-auto` 만

---

## 15. 실전적인사용패턴

### 15.1 단일에이전트(シンプル)

```bash
# 세션시작
gemini "태스크1를 시작"

# 최신세션를계속
gemini -r latest -p "이어서의 작업"
```

### 15.2 복수에이전트의병렬실행

```bash
#!/bin/bash

# 에이전트1를 시작
gemini "코드 리뷰를시작" -o json
# --list-sessions 로 번호를확인

# 에이전트2를 시작
gemini "테스트생성를시작" -o json

# 세션목록를확인
gemini --list-sessions
# 출력:
# 1. 코드 리뷰를시작 (Just now) [uuid-1]
# 2. 테스트생성를시작 (Just now) [uuid-2]

# 각세션를번호로계속
gemini -r 1 -p "src/main.py 를 리뷰하여"
gemini -r 2 -p "ユニット테스트를추가하여"
```

### 15.3 stream-json부터세션ID취득

```bash
# 세션ID를 취득
SESSION_ID=$(gemini "태스크시작" -o stream-json 2>&1 | \
 grep '"type":"init"' | jq -r '.session_id')

# UUID로 세션계속
gemini -r "$SESSION_ID" -p "이어서의 작업" -o json
```

### 15.4 비인터랙티브 + Policy Engine

```bash
# ワーク스페이스ポリシー로 도구제어
mkdir -p .gemini/policies

cat > .gemini/policies/automation.toml << 'EOF'
[[rule]]
toolName = "run_shell_command"
commandRegex = "^(git|gh|pytest|ruff) "
decision = "allow"
priority = 200

[[rule]]
toolName = ["write_file", "replace", "read_file", "list_directory", "glob"]
decision = "allow"
priority = 100
EOF

# ポリシー이 자동적용된다
gemini -o stream-json "pytest 를 실행하여결과를보고하여"
```

### 15.5 샌드박스 + 자동승인

```bash
# 안전한 자동실행(샌드박스内로 전도구허가)
gemini --approval-mode yolo -o json "리팩터링를실시하여"
# --approval-mode yolo 時는 샌드박스이자동유효화
```

---

## 16. トラブルシューティング

### 16.1 resume時에 에러

```
When resuming a session, you must provide a message via --prompt (-p) or stdin
```

→ `-p` 로 프롬프트를지정：
```bash
gemini -r latest -p "이어서의 질문"
```

### 16.2 인증에러

```
Loaded cached credentials.
```
이메시지는정상.에러의 경우는 `gemini auth` で再인증.
`/logout` 명령어로인증정보를클리어하여부터재인증한다것도가능.

### 16.3 세션를 찾를 찾을 수 없다

```bash
gemini --list-sessions # 현재의세션를확인
```

세션는프로젝트디렉토리마다에관리된다.

### 16.4 비인터랙티브모드로도구이使え없다

```
Tool "run_shell_command" not found in registry.
```

→ 섹션 2.6.3 의 해결策를 참조.Policy Engine 또는レガシー의 `--allowed-tools` 로 도구를 유효화한다.

### 16.5 Policy Engine 의 규칙이無視된다

`--approval-mode auto_edit` + 비인터랙티브모드의組み合わせ로 발생.섹션 2.6.4 의 회피策를 참조.

### 16.6 샌드박스모드의문제

```bash
# 디버그모드로상세로그를확인
DEBUG=1 gemini -s -p "command"
```

- WSL 환경의 Docker Desktop 없음로 는 Docker 샌드박스이실패하는 경우이 있다
- `.gemini/.env` でCLI고유의환경변수를설정(프로젝트루트의 `.env` は読み込まれ없다)

---

## 17. 참고링크

- [Gemini CLI GitHub](https://github.com/google-gemini/gemini-cli)
- [Gemini CLI 공식문서](https://geminicli.com/docs/)
- [Gemini CLI チートシート](https://geminicli.com/docs/cli/cli-reference/)
- [Policy Engine 레퍼런스](https://geminicli.com/docs/reference/policy-engine/)
- [MCP 서버설정](https://geminicli.com/docs/tools/mcp-server/)
- [샌드박스모드](https://geminicli.com/docs/cli/sandbox/)
- [Plan Mode](https://geminicli.com/docs/cli/plan-mode/)
- [Agent Skills](https://geminicli.com/docs/cli/skills/)
- [シェル도구](https://geminicli.com/docs/tools/shell/)
- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API 문서](https://ai.google.dev/gemini-api/docs/models)

---

## 18. 一次정보와검증상황

| 정보 | 一次정보源 | 검증방법 | 검증일 |
|------|-----------|---------|--------|
| 명령어옵션 | `gemini --help` (v0.31.0) | 로컬실행 | 2026-03-09 |
| 서브명령어 | `gemini skills --help`, `gemini hooks --help` (v0.31.0) | 로컬실행 | 2026-03-09 |
| JSON출력포맷 | 実機검증(v0.18.0時点) | 로컬실행 | 2025-11-27 |
| stream-json 포맷 | 実機검증(v0.18.0時点) | 로컬실행 | 2025-11-27 |
| 세션관리 | 実機검증(v0.18.0時点) | 로컬실행 | 2025-11-27 |
| 비인터랙티브모드의도구제한 | 実機검증(v0.18.0時点) | 로컬실행 | 2025-11-30 |
| Policy Engine | Web검색 | 未実機검증 | 2026-03-09 |
| 모델목록(Gemini 3系) | Web검색 | 未実機검증 | 2026-03-09 |
| 샌드박스모드 | Web검색 | 未実機검증 | 2026-03-09 |
| MCP 지원 | Web검색 | 未実機검증 | 2026-03-09 |
| 확장기능 | Web검색 | 未実機검증 | 2026-03-09 |
| Plan Mode | Web검색 | 未実機검증 | 2026-03-09 |
| Agent Skills | Web검색 | 未実機검증 | 2026-03-09 |

> **주의**: "未実機검증"의 항목는Web검색결과에 기반한.버전업에 의해사양이변경되어 있다가능性이 있다.
> 実機로 검증하는 경우는 `gemini --help` 로 최신사양를확인한다것.
> 참고URLが実在한다かは未검증.特에 `geminicli.com` ド메인의 URLは要확인.

---

## 변경履歴

| 日付 | 내용 |
|------|------|
| 2025-11-27 | 初版생성(v0.18.0 대상) |
| 2025-11-30 | 섹션 2.6"비인터랙티브모드로의 도구제한"추가.`--allowed-tools` 플래그에 의한 `run_shell_command` 유효화절차, `gh`/`uv` 등의검증결과, 보안고려事項를 상세에기재.bugfix-agent 로 의 구현방법를추가. |
| 2026-03-09 | v0.32.1 대응에전面업데이트.主な변경: (1) Policy Engine(v0.30.0+)섹션추가, `--allowed-tools` 비추천화를反映, (2) 모델목록를 Gemini 3/3.1 Pro Preview 추가로업데이트, (3) 샌드박스모드상세섹션추가(Docker/Podman/gVisor/Seatbelt/LXC), (4) MCP 서버지원상세섹션추가(Stdio/SSE/HTTP Streaming), (5) 확장기능섹션추가, (6) Plan Mode(v0.29.0+)섹션추가, (7) Agent Skills(v0.23.0+)섹션추가, (8) 인터랙티브명령어목록추가, (9) 3CLI비교表를 업데이트, (10) トラブルシューティングを拡充.v0.18.0 부터 v0.32.1 間의 주요한 변경(14버전분)를反映. |
| 2026-03-09 | `--raw-output` / `--accept-raw-output-risk` 추가, 버전表記를 `--help` 취득版(v0.31.0)とWeb검색版(v0.32.1)에분리, `--experimental-zed-integration` に未기재注記추가, `gemini hooks` 명령어섹션추가, 一次정보와검증상황섹션추가. |
