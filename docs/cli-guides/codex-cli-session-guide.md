# Codex CLI 세션관리가이드

## 개요

OpenAI Codex CLI 의 세션관리기능에関한다조사결과를まとめた資料.
복수에이전트의병렬실행나 세션인수인계의ベストプラクティス를 기재.

**조사日**: 2026-03-09
**대상버전**: OpenAI Codex CLI v0.112.0
**공식레퍼런스**: https://developers.openai.com/codex/cli/reference/
**--help 취득日**: 2026-03-09(v0.112.0 의 로컬환경로취득)

---

## 1. 기본명령어구조

### 1.1 주요명령어목록

| 명령어 | 에일리어스 | 설명 |
|----------|-----------|------|
| `codex exec` | `codex e` | 비인터랙티브실행 |
| `codex exec resume` | - | 세션재개 |
| `codex fork` | - | 세션フォーク(신스레드에분岐) |
| `codex apply` | `codex a` | Codex Cloud 태스크의 diff 를 적용 |
| `codex cloud` | - | Cloud 태스크관리 |
| `codex cloud exec` | - | Cloud 태스크의직접실행 |
| `codex cloud list` | - | Cloud 태스크목록 |
| `codex resume` | - | 인터랙티브세션재개 |
| `codex mcp` | - | MCP 서버관리 |
| `codex features` | - | フィーチャー플래그관리 |
| `codex login` | - | OAuth / API 키인증 |
| `codex logout` | - | 인증정보의삭제 |
| `codex completion` | - | シェル보완스크립트생성 |
| `codex app` | - | デスク탑클라이언트기동(macOS 만) |
| `codex app-server` | - | 앱서버를로컬기동(실험적) |

### 1.2 신규세션시작

```bash
codex exec [OPTIONS] [PROMPT]
```

### 1.3 세션재개

```bash
codex exec resume [OPTIONS] [SESSION_ID] [PROMPT]
```

### 1.4 세션フォーク

```bash
codex fork [OPTIONS] [SESSION_ID]
```

전의 인터랙티브세션를새로운스레드에フォーク(元のトラン스크립트를보유).

---

## 2. 이용가능한 파라미터

### 2.1 글로벌플래그(전서브명령어공통)

| 옵션 | 축약형 | 설명 | 예 |
|-----------|--------|------|-----|
| `--model` | `-m` | 사용모델 | `-m gpt-5.4` |
| `--cd` | `-C` | 작업디렉토리 | `-C /path/to/project` |
| `--sandbox` | `-s` | 샌드박스ポリシー | `-s workspace-write` |
| `--config` | `-c` | 설정오버라이드 | `-c key=value` |
| `--enable` | - | 기능를유효화 | `--enable web_search_request` |
| `--disable` | - | 기능를무효화 | `--disable feature_name` |
| `--image` | `-i` | 画像添付 | `-i image.png` |
| `--full-auto` | - | 低摩擦모드(`--ask-for-approval on-request` のショートカット) | 승인없음로 실행 |
| `--ask-for-approval` | `-a` | 승인타이밍제어 | `-a never` |
| `--add-dir` | - | 추가의쓰기가능디렉토리 | `--add-dir /other/path` |
| `--profile` | `-p` | 설정プロ파일읽기 | `-p my-profile` |
| `--oss` | - | 로컬 OSS 모델プロバイダー사용 | Ollama / LM Studio |
| `--search` | - | ライブ Web 검색를 유효화 | - |
| `--no-alt-screen` | - | 대체スクリーン모드무효화 | - |
| `--dangerously-bypass-approvals-and-sandbox` | `--yolo` | 전승인·샌드박스를바이패스(위험) | - |

### 2.2 `codex exec` 고유의옵션

| 옵션 | 축약형 | 설명 | 예 |
|-----------|--------|------|-----|
| `--json` | `--experimental-json` | JSONL형식로출력 | 세션ID추출에사용 |
| `--output-last-message` | `-o` | 최종메시지를파일출력 | `-o result.txt` |
| `--output-schema` | - | JSON Schema 에 의한리스폰스검증 | `--output-schema schema.json` |
| `--ephemeral` | - | 세션파일를디스크에영속화하지 않는다 | CI 용 |
| `--color` | - | ANSI カラー출력제어 | `--color never` |
| `--skip-git-repo-check` | - | Git리포지토리外로 의 실행허가 | - |

### 2.3 `codex exec resume` 의 옵션

`codex exec resume --help`(v0.112.0)로확인완료의 옵션목록：

| 옵션 | 축약형 | 설명 | 예 |
|-----------|--------|------|-----|
| `--last` | - | 최신세션를재개 | `--last` |
| `--all` | - | 현재의디렉토리외의 세션도대상 | `--all` |
| `--config` | `-c` | 설정오버라이드 | `-c key=value` |
| `--enable` | - | 기능를유효화 | `--enable web_search_request` |
| `--disable` | - | 기능를무효화 | `--disable feature_name` |
| `--image` | `-i` | フォロー업에画像添付 | `-i screenshot.png` |
| `--model` | `-m` | 사용모델 | `-m gpt-5.3-codex` |
| `--full-auto` | - | 低摩擦모드 | 승인없음로 실행 |
| `--dangerously-bypass-approvals-and-sandbox` | - | 전승인·샌드박스를바이패스 | - |
| `--skip-git-repo-check` | - | Git리포지토리外로 의 실행허가 | - |
| `--ephemeral` | - | 세션파일를디스크에영속화하지 않는다 | CI 용 |
| `--json` | - | JSONL형식로출력 | 세션ID추출에사용 |
| `--output-last-message` | `-o` | 최종메시지를파일출력 | `-o result.txt` |
| `SESSION_ID` | - | 특정세션ID | UUID형식 |
| `PROMPT` | - | フォロー업프롬프트 | stdin 부터도파이프가능 |

#### 주의: `exec resume` 로 사용**할 수 없다**옵션

- `--output-schema` → exec 고유(resume で는 사용불가)

> 글로벌플래그(`--model`, `--sandbox`, `--config` 등)는세션시작시의 설정를이어받다.
> resume 시에 `-m` 로 모델를직접변경가능(`-c model=` 로 의 회피는불필요).

#### `--json` 옵션의 resume 대응상황

v0.112.0 에서 `--json` 이 `codex exec resume` でも사용가능이다것을확인완료.
이전의버전(v0.63.0 時点)로는 resume 시에 `--json` 이 사용로きなかったが, 이제약는 v0.112.0 로 해소되어 있다.

### 2.4 `codex fork` 의 옵션

| 옵션 | 설명 |
|-----------|------|
| `--all` | 현재의디렉토리외의 세션도표시 |
| `--last` | ピッカー를 스킵し최신세션를フォーク |
| `SESSION_ID` | 특정세션를지정하여フォーク |

### 2.5 `codex cloud exec` 의 옵션

| 옵션 | 설명 | 예 |
|-----------|------|-----|
| `--env` | 환경ID(필수) | `--env env_abc123` |
| `--attempts` | アシスタント試행회수(1-4) | `--attempts 3` |
| `QUERY` | 태스크프롬프트 | `"버그를수정하여"` |

### 2.6 `codex cloud list` 의 옵션

| 옵션 | 설명 |
|-----------|------|
| `--cursor` | ページネーションカーソル |
| `--env` | 환경로필터 |
| `--json` | 機械가독출력 |
| `--limit` | 최대건수(1-20) |

---

## 3. 세션ID의취득방법

### 3.1 표준출력부터확인

`codex exec` 실행時에 헤더로서표시된다：

```
OpenAI Codex v0.112.0
--------
workdir: /home/aki/project
model: gpt-5.4
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR] (network access enabled)
session id: 019ac592-167e-7ac2-94c5-38ffcd86fbd0 ← 여기
--------
```

### 3.2 JSON출력부터プ로그ラム적으로 취득

```bash
SESSION_ID=$(codex exec -m gpt-5.4 --json "태스크" 2>&1 | \
 grep '"type":"thread.started"' | jq -r '.thread_id')
```

#### JSON출력의전체예(명령어실행를 포함경우)

실행명령어：
```bash
codex exec -m gpt-5.4 --json "pwd를 실행하여" 2>&1 | jq '.'
```

출력(JSONL형식 - 각행이1つ의 JSON이벤트, 이하는정형완료)：

```json
{
 "type": "thread.started",
 "thread_id": "019ac5b0-190b-75c0-bf3e-5f1acf69fcce"
}
{
 "type": "turn.started"
}
{
 "type": "item.completed",
 "item": {
 "id": "item_0",
 "type": "reasoning",
 "text": "**Executing command**"
 }
}
{
 "type": "item.started",
 "item": {
 "id": "item_1",
 "type": "command_execution",
 "command": "/bin/bash -lc pwd",
 "aggregated_output": "",
 "exit_code": null,
 "status": "in_progress"
 }
}
{
 "type": "item.completed",
 "item": {
 "id": "item_1",
 "type": "command_execution",
 "command": "/bin/bash -lc pwd",
 "aggregated_output": "/home/aki/project\n",
 "exit_code": 0,
 "status": "completed"
 }
}
{
 "type": "item.completed",
 "item": {
 "id": "item_2",
 "type": "agent_message",
 "text": "/home/aki/project"
 }
}
{
 "type": "turn.completed",
 "usage": {
 "input_tokens": 44105,
 "cached_input_tokens": 42752,
 "output_tokens": 53
 }
}
```

#### 이벤트타입의설명

| type | 설명 |
|------|------|
| `thread.started` | 세션시작.`thread_id` 이 세션ID와 된다 |
| `turn.started` | 턴(会話の1往復)의 시작 |
| `item.started` | アイテム(アクション)의 시작.主에 명령어실행로사용 |
| `item.completed` | アイテム의 완료.推論·명령어실행·회答 등 |
| `turn.completed` | 턴의 종료.토큰사용量를 포함 |
| `turn.failed` | 턴의 실패 |
| `error` | 에러이벤트 |

#### item.type 의 종류

| item.type | 설명 | 이벤트 |
|-----------|------|---------|
| `reasoning` | 에이전트의推論·思考스텝 | `completed` 만 |
| `command_execution` | シェル명령어의실행 | `started` → `completed` |
| `agent_message` | 유저로의최종회答 | `completed` 만 |
| `file_change` | 파일변경 | `completed` 만 |
| `mcp_tool_call` | MCP 도구호출 | `started` → `completed` |
| `web_search` | Web 검색 | `completed` 만 |
| `plan_update` | 플랜업데이트 | `completed` 만 |

#### command_execution 의 상세필드

| 필드 | 설명 | 예 |
|-----------|------|-----|
| `command` | 실행된명령어 | `"/bin/bash -lc pwd"` |
| `aggregated_output` | 명령어의표준출력전체 | `"/home/aki/project\n"` |
| `exit_code` | 종료코드(실행중는 `null`) | `0` (성공), `1` (실패) |
| `status` | 실행상태 | `"in_progress"` → `"completed"` |

**주의**: `aggregated_output` に는 명령어의출력전체이포함된다때문에, `ls` 와 `cat` 등를 실행한다과 JSON 이 비常に大きく된다.

#### turn.completed 의 usage 필드

| 필드 | 설명 | 용도 |
|-----------|------|------|
| `input_tokens` | 입력토큰수 | 코스트계산 |
| `cached_input_tokens` | 캐시완료토큰수 | 課金대상외(코스트삭감) |
| `output_tokens` | 출력토큰수 | 코스트계산 |

```bash
# 토큰사용量의 추출
codex exec -m gpt-5.4 --json "질문" 2>&1 | \
 grep '"type":"turn.completed"' | jq '.usage'
```

#### 세션ID추출의ワンライナー

```bash
# jq 를 사용
codex exec -m gpt-5.4 --json "태스크" 2>&1 | \
 grep '"type":"thread.started"' | jq -r '.thread_id'

# jq 없음로 추출(sed사용)
codex exec -m gpt-5.4 --json "태스크" 2>&1 | \
 grep '"type":"thread.started"' | sed 's/.*"thread_id":"\([^"]*\)".*/\1/'
```

#### item 数の目安

| 태스크의복잡さ | item数 | 主な内訳 |
|---------------|--------|----------|
| 단순한 질문회答 | 2 | reasoning(1) + agent_message(1) |
| 명령어1회실행 | 3-4 | reasoning + command_execution + agent_message |
| 복수스텝 | 5+ | 각스텝마다에 reasoning + 실행이증가 |

---

## 4. stdout/stderr 의 출력분리

Codex CLI 는 헤더정보와최종응답를다르다스트림에출력한다.

| 출력선 | 내용 |
|--------|------|
| **stderr** | 버전, workdir, model, session id, 프롬프트, thinking, exec, codex응답, tokens |
| **stdout** | 최종응답만 |

### 4.1 プ로그ラム적인 처리예

```python
# session_id 는 stderr 부터추출
for line in stderr.splitlines():
 if line.startswith("session id:"):
 session_id = line.split(":", 1)[1].strip()
 break

# 리뷰결과는 stderr + stdout 를 결합하여검색
full_output = f"{stderr}\n{stdout}".strip()
```

**주의**: `--json` 모드로는 전출력이 stdout 에 JSONL 형식로출력된다.

---

## 5. 세션설정의인수인계동작

### 5.1 인수인계목록

| 설정항목 | 시작시지정 | resume時 | 비고 |
|---------|-----------|----------|------|
| `cwd` (`-C`) | `-C /path` | **자동인수인계** | 변경불가 |
| `sandbox` (`-s`) | `-s workspace-write` | **자동인수인계** | 변경불가 |
| `model` (`-m`) | `-m gpt-5.4` | **자동인수인계** | `-m` 로 직접변경가능 |
| `features` (`--enable`) | `--enable web_search_request` | **자동인수인계** | 추가/변경가능 |
| 기타 `-c` 설정 | `-c key=value` | **자동인수인계** | 추가/변경가능 |
| Git 컨텍스트 | 자동 | **자동인수인계** | v0.111.0 로 수정 |
| 앱(플러그인) | 자동 | **자동인수인계** | v0.111.0 로 수정 |

### 5.2 검증결과

세션시작시에 `--enable web_search_request` 를 지정한 경우, resume時에 지정하지 않아도Web검색이 유효의まま유지된다것을확인완료.

> **v0.111.0 수정**: resume 시에 Git 컨텍스트와앱이壊れる문제이수정된.

---

## 6. 실전적인사용패턴

### 6.1 단일에이전트(シンプル)

```bash
# 세션시작
codex exec -m gpt-5.4 "태스크1를 시작"

# 최신세션를인수인계
codex exec resume --last "이어서의 작업"
```

### 6.2 복수에이전트의병렬실행

```bash
#!/bin/bash

# 에이전트1: 코드 리뷰담당
SESSION_REVIEW=$(codex exec \
 -m gpt-5.4 \
 -C /home/aki/project \
 -s workspace-write \
 --json "코드 리뷰를시작" 2>&1 | \
 grep '"type":"thread.started"' | jq -r '.thread_id')

# 에이전트2: 테스트담당
SESSION_TEST=$(codex exec \
 -m gpt-5.4 \
 -C /home/aki/project \
 -s workspace-write \
 --json "테스트생성를시작" 2>&1 | \
 grep '"type":"thread.started"' | jq -r '.thread_id')

# 에이전트3: 문서담당(Web검색유효)
SESSION_DOCS=$(codex exec \
 -m gpt-5.4 \
 -C /home/aki/project \
 -s workspace-write \
 --search \
 --json "문서생성를시작" 2>&1 | \
 grep '"type":"thread.started"' | jq -r '.thread_id')

echo "Review Session: $SESSION_REVIEW"
echo "Test Session: $SESSION_TEST"
echo "Docs Session: $SESSION_DOCS"

# 각세션를개별에계속
codex exec resume "$SESSION_REVIEW" "src/main.py 를 리뷰하여"
codex exec resume "$SESSION_TEST" "ユニット테스트를추가하여"
codex exec resume "$SESSION_DOCS" "README.md를 업데이트하여"
```

### 6.3 세션환경의완전고정(ベストプラクティス)

```bash
# 모두의 설정를세션시작時에 지정
SESSION_ID=$(codex exec \
 -m gpt-5.4 \
 -C /home/aki/project \
 -s workspace-write \
 --search \
 --json "프로젝트분석를시작" 2>&1 | \
 grep '"type":"thread.started"' | jq -r '.thread_id')

# resume時는 프롬프트만(설정는모두引き継がれる)
codex exec resume "$SESSION_ID" "의존 관계를조사하여"
codex exec resume "$SESSION_ID" "보안취약성를체크하여"

# 필요에応じて모델를업그레이드
codex exec resume "$SESSION_ID" \
 -m gpt-5.3-codex \
 "복잡한 리팩터링를提案하여"
```

### 6.4 プ로그ラム적구현패턴

v0.112.0 로 는 `--json` 이 resume でも사용가능한 때문에, 신규·resume で統一적으로 扱える.

```python
def build_codex_args(session_id: str | None, model: str, workdir: str, sandbox: str) -> list[str]:
 """Codex CLI 의 인수를구축한다(신규·resume 공통로 --json 사용가능)"""
 if session_id:
 args = ["codex", "exec", "resume", session_id, "--json"]
 else:
 args = [
 "codex", "exec",
 "-m", model,
 "-C", workdir,
 "-s", sandbox,
 "--search",
 "--json",
 ]
 return args
```

**ポ인ト**:
- 신규·resume とも에 `--json` 로 구조화 출력이가능
- 세션ID는 `thread.started` 이벤트의 `thread_id` 부터취득
- `--output-schema` 만 exec 고유(resume で는 사용불가)

### 6.5 CI/CD 로 의 사용

```bash
# API 키를환경변수로설정(추천)
CODEX_API_KEY=<key> codex exec \
 --json \
 --ephemeral \
 --full-auto \
 -s workspace-write \
 -o result.txt \
 "테스트를 실행하여レポート를 생성"

# --output-last-message 과 --json 의 병용로
# 機械가독한 이벤트스트림와최종サマリの両方를 취득
```

### 6.6 세션フォーク

```bash
# 최신세션를フォーク(새로운스레드에분岐)
codex fork --last

# 특정의 세션를フォーク
codex fork <SESSION_ID>

# 인터랙티브세션内로 는 /fork スラッシュ명령어도사용가능
```

### 6.7 プロ파일의활용

```bash
# プロ파일를 사용하여세션시작
codex exec -p my-review-profile "코드 리뷰를 실행"

# プロ파일의설정예(~/.codex/config.toml)
# [profiles.my-review-profile]
# model = "gpt-5.4"
# model_reasoning_effort = "high"
# web_search = "cached"
```

### 6.8 로컬 LLM 의 사용

```bash
# --oss 플래그로로컬모델를 사용
codex exec --oss "태스크를 실행"

# Ollama プロバイダー의 설정예(~/.codex/config.toml)
# [model_providers.ollama]
# name = "Ollama"
# base_url = "http://localhost:11434/v1"
#
# [profiles.gpt-oss-120b-ollama]
# model_provider = "ollama"
# model = "gpt-oss:120b"

# プロ파일와組み合わせ
codex exec -p gpt-oss-120b-ollama "로컬로분석"
```

---

## 7. 이용가능한 모델

### 7.1 추천모델

| 모델 | 특징 | 용도 |
|--------|------|------|
| `gpt-5.4` | フラッグシップ.コーディング + 強力な推論 + エージェンティック | **最も추천** |
| `gpt-5.3-codex` | 業界최고水準のコーディング特화모델 | 복잡なソフトウェアエンジニアリング |
| `gpt-5.3-codex-spark` | 텍스트전용.거의即座の反復에 최적화 | 고속イテレーション(ChatGPT Pro 限定) |

### 7.2 기타모델

| 모델 | 특징 | 상태 |
|--------|------|------|
| `gpt-5.2-codex` | 高度なコーディング모델 | gpt-5.3-codex に後継 |
| `gpt-5.2` | 범용모델 | gpt-5.4 に後継 |
| `gpt-5.1-codex-max` | 長期エージェンティック태스크최적화 | 이용가능 |
| `gpt-5.1` | クロスド메인 + エージェンティック | 이용가능 |
| `gpt-5.1-codex` | 長時間エージェンティック태스크 | 後継있음 |
| `gpt-5-codex` | 初代エージェンティックバリアント | レガシー |
| `gpt-5-codex-mini` | 小타입·低코스트 | レガシー |
| `gpt-5` | 推論重視 | レガシー |

> **주의**: 구가이드로기재하여いた `gpt-5.1-codex-mini` 는 `gpt-5-codex-mini` の誤記의 가능性있음.
> 최신의추천는 `gpt-5.4`(범용)또는 `gpt-5.3-codex`(コーディング特화).

---

## 8. Web검색기능

### 8.1 유효화방법

```bash
# 추천: --search 플래그(ライブ검색)
codex exec --search "질문"

# --enable 플래그로도유효화가능
codex exec --enable web_search_request "질문"

# 설정파일로제어
# web_search = "disabled" | "cached" | "live"
```

### 8.2 Web검색의 출력예

```
🌐 Searched: current USD JPY exchange rate today
```

> **주의**: 기본값로캐시완료검색이 유효.`--search` でライブ검색에 전환.

---

## 9. 샌드박스ポリシー

| ポリシー | 설명 |
|---------|------|
| `read-only` | 읽기전용(기본값) |
| `workspace-write` | 작업디렉토리 + /tmp 로의쓰기허가 |
| `danger-full-access` | 풀접근(위험) |

### 9.1 추가의쓰기디렉토리

```bash
# --add-dir 로 추가의디렉토리에쓰기허가를 부여
codex exec -s workspace-write --add-dir /other/project "クロス프로젝트변경"
```

### 9.2 샌드박스의상세

`workspace-write` で는 기본값로네트워크접근이유효：
```
sandbox: workspace-write [workdir, /tmp, $TMPDIR] (network access enabled)
```

> **v0.110.0**: Linux 로 의 읽기전용접근이개선.`~/.ssh` 등의機密디렉토리를 제외.

### 9.3 승인ポリシー

| 값 | 설명 |
|----|------|
| `untrusted` | 모두의アクション에 승인를요구 |
| `on-request` | 리퀘스트시만승인(`--full-auto` 의 기본값) |
| `never` | 승인없음(`--yolo` 와 동등) |

---

## 10. MCP(Model Context Protocol)지원

### 10.1 개요

MCP 서버를접속하여추가도구나 컨텍스트를 Codex 에 제공가능.

### 10.2 CLI 로 의 관리

```bash
# MCP 서버를추가
codex mcp add context7 -- npx -y @upstash/context7-mcp

# 인터랙티브세션内로 확인
# /mcp スラッシュ명령어
```

### 10.3 설정파일로의구성

```toml
# ~/.codex/config.toml(글로벌)
# 또는 .codex/config.toml(프로젝트스코프, 신뢰완료프로젝트만)

[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]

[mcp_servers.my-server]
command = "node"
args = ["server.js"]
bearer_token_env_var = "MY_SERVER_TOKEN" # 임의: 인증토큰
# http_headers = { "X-Custom" = "value" } # 임의: 커스텀헤더
```

### 10.4 서버타입

| 타입 | 설명 |
|--------|------|
| STDIO | 로컬프로세스로서기동(`command` 로 지정) |
| Streamable HTTP | アドレス로 접속(URL 로 지정) |

---

## 11. スラッシュ명령어

인터랙티브세션内로 사용가능한 명령어.

### 11.1 세션·모델제어

| 명령어 | 설명 |
|---------|------|
| `/model` | アクティブ모델의전환(推論努力레벨도설정가능) |
| `/personality` | コミュニケーションスタイルの調整 |
| `/plan` | 플랜모드에전환(실행前に計画を提案) |
| `/experimental` | 실험적기능의유효화(멀티에이전트등) |
| `/permissions` | 승인ポリシー의 변경 |

### 11.2 ナビゲーション·스레드

| 명령어 | 설명 |
|---------|------|
| `/fork` | 현재의会話를 새로운스레드에クローン |
| `/new` | 새로운会話를 시작(같은 CLI 세션内) |
| `/resume` | 저장완료세션의トラン스크립트를再읽기 |
| `/agent` | スポーン된서브에이전트스레드間의 전환 |

### 11.3 리뷰·분석

| 명령어 | 설명 |
|---------|------|
| `/review` | ワーキングツリー의 평가(동작변경와테스트에초점) |
| `/diff` | Git 변경의표시(未추적파일를 포함) |
| `/compact` | 가능視会話を要約하여토큰를解放 |
| `/status` | 세션설정와토큰사용量를 표시 |

### 11.4 유틸리티

| 명령어 | 설명 |
|---------|------|
| `/mention` | 특정파일를会話に添付 |
| `/mcp` | 설정완료 MCP 도구목록 |
| `/apps` | コネクター의 참조·삽입 |
| `/init` | `AGENTS.md` スキャフォールド의 생성 |
| `/copy` | 최신의응답를클립보드에복사 |
| `/ps` | 백그라운드터미널의 상태와最近의 출력 |
| `/debug-config` | 설정레이어와診断정보의표시 |
| `/statusline` | 푸터스테이터스ラ인의 커스터마이즈 |
| `/feedback` | メンテナーに診断정보를송신 |
| `/clear` | 터미널リ세트＋신규チャット |
| `/logout` | 로컬인증정보의클리어 |
| `/quit`, `/exit` | CLI 를 종료 |

---

## 12. Codex Cloud

### 12.1 개요

`codex cloud` 명령어로クラウド태스크를터미널부터관리.인수없음로 인터랙티브ピッカー이 열다.

### 12.2 태스크의실행

```bash
# クラウド로 태스크를 실행
codex cloud exec --env ENV_ID "버그를수정하여"

# Best-of-N(복수試행)
codex cloud exec --env ENV_ID --attempts 3 "최적화案を提案하여"
```

### 12.3 결과의적용

```bash
# クラウド태스크의 diff 를 로컬에적용
codex apply <TASK_ID>
```

### 12.4 태스크목록

```bash
# 最近의 태스크를확인
codex cloud list --limit 10

# JSON 로 출력
codex cloud list --json --env ENV_ID
```

---

## 13. 플러그인시스템(v0.110.0+)

### 13.1 개요

스킬, MCP エントリ, 앱コネクター를 설정또는로컬マーケットプレース부터읽기.

### 13.2 `@plugin` メンション(v0.112.0+)

チャット内로 `@plugin_name` 처럼플러그인를직접참조し, 関連한다 MCP/앱/스킬컨텍스트를자동적으로 포함하다것이가능.

### 13.3 멀티에이전트(v0.110.0+)

- `/agent` ベース의 서브에이전트유효화
- 승인프롬프트대응
- 序数ニックネーム(ordinal nicknames)로의 에이전트관리

---

## 14. トラブルシューティング

### 14.1 모델변경시의 경고

```
warning: This session was recorded with model `gpt-5.4` but is resuming with `gpt-5.3-codex`. Consider switching back to `gpt-5.4` as it may affect Codex performance.
```

→ 경고는出る이 동작에문제없음.필요에応じて모델변경가능.

### 14.2 `--last` 의 경합リスク

복수에이전트를병렬실행하고 있다경우, `--last` 는 최신의세션를 참조한다때문에, 의도하지 않는다세션를이어받다가능性이 있다.

→ **해결策**: 명시적에세션ID를 관리한다(6.2의방법)

### 14.3 resume 시의 Git 컨텍스트소실

v0.111.0 이전로는 resume 시에 Git 컨텍스트와앱이보유되지 않는다문제가 있った.

→ **해결策**: v0.111.0 이후에업그레이드

### 14.4 인증

```bash
# CI/CD 로 의 인증(추천)
export CODEX_API_KEY=<your-api-key>

# 인터랙티브인증
codex login
```

---

## 15. 비교: 他의 CLI도구

| 기능 | Codex CLI | Gemini CLI | Claude Code |
|------|-----------|------------|-------------|
| 세션인수인계 | `exec resume` | 未확인 | MCP経由 |
| 세션フォーク | `fork` / `/fork` | - | - |
| JSON출력 | `--json` | - | - |
| Web검색 | `--search` / `--enable web_search_request` | 組み込み | `WebSearch` tool |
| 모델지정 | `-m` | `-m` | `/model` |
| MCP 지원 | `codex mcp` + config.toml | 설정파일 | 설정파일 |
| 로컬 LLM | `--oss` / `--local-provider` | - | - |
| クラウド태스크 | `codex cloud` | - | - |
| 코드 리뷰 | `/review` | - | - |
| プロ파일 | `--profile` | - | - |

---

## 16. 참고링크

- [Codex CLI Reference](https://developers.openai.com/codex/cli/reference/)
- [Codex CLI Features](https://developers.openai.com/codex/cli/features/)
- [Codex Non-interactive Mode](https://developers.openai.com/codex/noninteractive/)
- [Codex Models](https://developers.openai.com/codex/models/)
- [Codex Config Reference](https://developers.openai.com/codex/config-reference)
- [Codex Advanced Configuration](https://developers.openai.com/codex/config-advanced/)
- [Codex MCP Integration](https://developers.openai.com/codex/mcp/)
- [Codex Slash Commands](https://developers.openai.com/codex/cli/slash-commands/)
- [Codex Changelog](https://developers.openai.com/codex/changelog/)
- [Codex GitHub Repository](https://github.com/openai/codex)

---

## 17. 一次정보와검증상황

| 정보 | 一次정보源 | 검증방법 | 검증일 |
|------|-----------|---------|--------|
| 명령어옵션 | `codex exec --help` / `codex exec resume --help` (v0.112.0) | 로컬실행 | 2026-03-09 |
| 모델목록 | Web검색(OpenAI공식) | 未実機검증 | 2026-03-09 |
| JSONL출력포맷 | 実機검증(v0.63.0時点) | 로컬실행 | 2025-11-27 |
| 세션설정인수인계 | 実機검증(v0.63.0時点) | 로컬실행 | 2025-12-02 |
| 신명령어(fork/cloud/apply) | Web검색 | 未実機검증 | 2026-03-09 |
| MCP 지원 | Web검색 | 未実機검증 | 2026-03-09 |
| 플러그인시스템 | Web검색 | 未実機검증 | 2026-03-09 |
| スラッシュ명령어 | Web검색 | 未実機검증 | 2026-03-09 |

> **주의**: "未実機검증"의 항목는Web검색결과에 기반한.버전업에 의해사양이변경되어 있다가능性이 있다.
> 実機로 검증하는 경우는 `codex exec --help`, `codex exec resume --help` 등로최신사양를확인한다것.

---

## 변경履歴

| 日付 | 내용 |
|------|------|
| 2025-11-27 | 初版생성(v0.63.0 대상)|
| 2025-12-02 | `--json` 옵션의제약를追記(resume時に引き継がれ없다문제)|
| 2026-03-09 | v0.112.0 대응에전面업데이트.모델목록업데이트(gpt-5.4 추천), 신명령어추가(fork/cloud/apply/mcp/features), スラッシュ명령어목록, MCP 지원, プロ파일·OSS 대응, 플러그인시스템, 샌드박스개선, item.type 의 확장(file_change/mcp_tool_call/web_search/plan_update), CI/CD 패턴추가.`--json` resume 제약의해소를확인·수정(v0.112.0 로 resume 로 도 `--json` 사용가능).一次정보섹션추가 |
