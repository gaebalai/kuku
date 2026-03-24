# Bugfix Agent v5 - 테스트상세설계書 (リバースエンジニアリング)

**생성日**: 2025-12-09
**버전**: 1.0
**목적**: 현재의테스트방식를문서화し, 본번환경와의차이를특정한다

---

## 1. 테스트구성개요

### 1.1 테스트파일목록

| 파일 | サイズ | 테스트수 | 목적 |
|---------|--------|---------|------|
| `test_bugfix_agent_orchestrator.py` | ~100KB | 160+ | 오케스트레이터ー본체의ユニット테스트 |
| `tests/test_issue_provider.py` | ~5KB | 11 | IssueProvider 単体테스트 |
| `test_prompts.py` | ~6KB | 少数 | 프롬프트파일의검증 |
| `tests/conftest.py` | ~2KB | - | pytest fixtures (mock_issue_provider 등) |

### 1.2 테스트카테고리

```
test_bugfix_agent_orchestrator.py
├── Tool Wrapper Tests (Phase 0)
│ ├── MockTool Tests (4건)
│ ├── GeminiTool Tests (12건)
│ ├── CodexTool Tests (10건)
│ └── ClaudeTool Tests (12건)
├── State/Context Tests
│ ├── AgentContext Tests (4건)
│ ├── SessionState Tests (2건)
│ └── Factory Function Tests (6건)
├── IssueProvider Tests (tests/test_issue_provider.py)
│ ├── MockIssueProvider Tests (8건)
│ └── Handler Integration Tests (3건)
├── CLI Parsing Tests (Phase 2)
│ ├── parse_args Tests (12건)
│ ├── ExecutionMode Tests
│ └── ExecutionConfig Tests
├── State Handler Tests (Phase 3)
│ ├── handle_init (3건)
│ ├── handle_investigate (2건)
│ ├── handle_investigate_review (2건)
│ ├── handle_detail_design (2건)
│ ├── handle_detail_design_review (2건)
│ ├── handle_implement (2건)
│ ├── handle_implement_review (3건)
│ ├── handle_qa (2건)
│ ├── handle_qa_review (4건)
│ └── handle_pr_create (1건)
├── Edge Case Tests
│ ├── Loop Counter Tests (3건)
│ ├── Session Management Tests (2건)
│ └── State Transition Tests (2건)
├── Error Handling Tests
│ ├── ToolError Tests (6건)
│ ├── check_tool_result Tests (2건)
│ └── LoopLimitExceeded Tests (1건)
├── Logging Tests
│ ├── RunLogger Tests (3건)
│ └── Log Format Tests (4건)
├── Integration Tests
│ ├── run() SINGLE mode (1건)
│ └── run() FROM_END mode (1건)
└── Smoke Tests (CI skip) - 4건
 ├── test_smoke_gemini_tool_real_cli
 ├── test_smoke_codex_tool_real_cli
 ├── test_smoke_claude_tool_real_cli
 └── test_smoke_full_orchestrator_run
```

---

## 2. 테스트방식

### 2.1 목ベース테스트

大부분의테스트는 `MockTool` 과 `monkeypatch` 를 사용하여CLI호출를목화:

```python
# 패턴1: MockTool 에 의한완전목
ctx = create_test_context(
 analyzer_responses=["analyzer response"],
 reviewer_responses=["reviewer response"],
 implementer_responses=["implementer response"],
 issue_url=config.issue_url,
)

# 패턴2: monkeypatch 에 의한부분목
def fake_streaming(args, **kwargs):
 return (stdout, stderr, returncode)
monkeypatch.setattr(mod, "_run_cli_streaming", fake_streaming)
```

### 2.2 테스트컨텍스트팩토리

`create_test_context()` 함수로統一적인 테스트컨텍스트를 생성:
- `analyzer_responses`: Gemini用리스폰스 (INIT, INVESTIGATE, DETAIL_DESIGN)
- `reviewer_responses`: Codex用리스폰스 (*_REVIEW)
- `implementer_responses`: Claude用리스폰스 (IMPLEMENT, PR_CREATE)
- `issue_provider`: IssueProvider 인스턴스(생략시는 `_SimpleTestIssueProvider` 를 자동생성)

### 2.3 IssueProvider 추상화에 의한로컬테스트

GitHub API 의존를배제한다때문에, `IssueProvider` 추상화를도입:

```python
# tests/utils/providers.py
class MockIssueProvider(IssueProvider):
 """테스트용 IssueProvider"""

 def __init__(self, initial_body: str = "", issue_number: int = 999):
 self._comments: list[str] = []
 ...

 # 어서션용헬퍼
 @property
 def comments(self) -> list[str]: ...
 @property
 def last_comment(self) -> str | None: ...
 @property
 def comment_count(self) -> int: ...
 def has_comment_containing(self, text: str) -> bool: ...
 def clear(self) -> None: ...
```

#### 사용예

```python
# tests/conftest.py 에 픽스처로서정의완료
@pytest.fixture
def mock_issue_provider():
 return MockIssueProvider(initial_body="# Test Issue")

def test_handler_posts_comment(mock_issue_provider):
 ctx = AgentContext(
 reviewer=MockTool(["## VERDICT\n- Result: PASS"]),
 issue_provider=mock_issue_provider,
 ...
 )
 handle_init(ctx, state)

 assert mock_issue_provider.comment_count == 1
 assert "PASS" in mock_issue_provider.last_comment
```

#### 테스트범위

| 테스트種별 | GitHub API | 대상 |
|-----------|------------|------|
| Unit/Handler Tests | ❌ 불필요(MockIssueProvider사용) | MockTool + MockIssueProvider |
| E2E Tests (Real AI) | ✅ 필요(GitHubIssueProvider사용) | 実際의 CLI도구 + GitHub Issue |

### 2.4 Smoke테스트

実際의 CLI도구를 호출하다테스트 (CIで는 스킵):

```python
@pytest.mark.skip(reason="Requires actual CLI tools")
def test_smoke_gemini_tool_real_cli():
 tool = mod.GeminiTool(model="auto")
 response, session_id = tool.run("What is 2+2?")
 assert response != "ERROR"
```

### 2.5 CodexTool JSON 파싱사양

#### 설계의도

CodexTool 는 Codex CLI 의 출력를파싱할 때, JSON파싱에실패한행도수집한다.
이것는 `mcp_tool_call` 모드로 VERDICT 이 플레인텍스트로서출력된다케이스에대응한다위해.

#### 동작사양

| 시나리오 | 期待동작 | 근거 |
|---------|---------|------|
| 유효なJSON행 | 파싱하여 `agent_message.text` 를 추출 | 통상플로우 |
| 무효なJSON행 | **스킵せず수집** | E2E Test 7-10 로 확정한사양 |
| 混合출력 | 유효메시지 + 비JSON행를 `\n\n` 로 결합하여반환 | mcp_tool_call 모드대응 |

#### 下流처리와의関係

수집된출력는 `parse_verdict()` に渡され, VERDICT Result 를 추출합니다:

1. **Step 1 (Strict Parse)**: `re.search(r"Result:\s*(\w+)", text)` 로 매치 → Enum변환로검증
 - 유효값 (PASS/RETRY/BACK_DESIGN/ABORT): 성공
 - 부정값 (PENDING/WAITING등): `InvalidVerdictValueError` を即座에 발생(**폴백대상外**)
 - 매치없음: Step 2へ

2. **Step 2 (Relaxed Parse)**: 복수패턴로탐색(Status:, **Status**:, 스테이터스: 등)

3. **Step 3 (AI Formatter)**: AI 로 정형하여리트라이(최대2회)

**중요**: `Result:` 행이違う場所(예: `gh comment` 인수)에출력된다와Step 1/2로 실패し, Step 3의AI Formatter이 필요에되어합니다.노이즈(비JSON행)의 혼입自体はVERDICT추출에영향しません.상세는 ARCHITECTURE.md Section 10 를 참조.

#### 테스트방침

테스트로는완전일치로검증し, "의도한노이즈"と"의도하지 않는다노이즈"を区별한다：

- ✅ `assert response == "INVALID JSON LINE\n\nok"` (엄밀)
- ❌ `assert "ok" in response` (リグレッション見逃しリスク)

> **참조**: `E2E_TEST_FINDINGS.md` 섹션 3.1, 4.1

---

## 3. 테스트픽스처구조

### 3.1 E2E테스트픽스처

```
test-fixtures/
└── bugfix-agent-e2e/
 ├── L1-simple/
 │ └── 001-type-error/
 │ ├── src/
 │ │ └── calculator.py
 │ ├── tests/
 │ │ └── test_calculator.py
 │ ├── test-artifacts/
 │ │ ├── logs/pytest/test.log
 │ │ ├── coverage/{html,xml,json}/
 │ │ └── bugfix-agent/
 │ └── pytest_output.txt
 ├── L2-medium/ (未구현)
 └── L3-complex/ (未구현)
```

### 3.2 L1-001 픽스처상세

**목적**: シンプルな타입에러를수정한다기본테스트케이스

**테스트내용**:
- 6건의테스트케이스 (모두PASS)
- Python 3.13.7 + pytest-8.4.2
- 커버리지계측대상: `apps/` 모듈

---

## 4. 본번환경와의차이분석

### 4.1 특정된차이

| 항목 | 테스트환경 | 본번환경 | 영향 |
|------|-----------|---------|------|
| CLI호출 | MockTool 로 목화 | 実際의 gemini/codex/claude CLI | 출력포맷의차이 |
| GitHub Issue | MockIssueProvider 로 목화 | GitHubIssueProvider (実API) | ✅ 해결완료 (Issue #284) |
| 작업디렉토리 | tmp_path사용 | 리포지토리루트 | 경로해결의차이 |
| 커버리지계측 | 무효 (`No data was collected`) | 유효 | 커버리지閾값판정 |
| 타임아웃 | 없음/짧은 | config.toml설정값 | 長時間태스크의挙動 |

### 4.2 커버리지문제의상세

L1-001픽스처로발생하고 있다문제:

```
CoverageWarning: Module apps was never imported. (module-not-imported)
CoverageWarning: No data was collected. (no-data-collected)
ERROR: Coverage failure: total of 0 is less than fail-under=40
```

**원인**:
- `pyproject.toml`의 커버리지설정이 `apps/` をターゲット에 하고 있다
- 픽스처의 `src/` 디렉토리는커버리지대상외

### 4.3 E2E테스트ランナー의 상태

**주의**: `e2e_test_runner.py` 는 현재리포지토리에존재하지 않는다

- 이전의E2E테스트로사용されていたが, 삭제또는커밋되어 있지 않다
- `test-artifacts/e2e/` 에 로그이残存 (Dec 6-8의테스트실행결과)

---

## 5. 테스트실행방법

### 5.1 ユニット테스트실행

```bash
# 전테스트실행
cd .claude/agents/bugfix-v5
source /home/aki/claude/kamo2/.venv/bin/activate
pytest test_bugfix_agent_orchestrator.py -v

# 특정카테고리만
pytest test_bugfix_agent_orchestrator.py -v -k "gemini"
pytest test_bugfix_agent_orchestrator.py -v -k "handler"

# Smoke테스트포함하다 (実CLI필요)
pytest test_bugfix_agent_orchestrator.py -v --run-slow
```

### 5.2 커버리지付き실행

```bash
pytest test_bugfix_agent_orchestrator.py --cov=bugfix_agent_orchestrator --cov-report=html
```

---

## 6. 개선提案

### 6.1 短期개선 (곧에 대응가능)

1. **커버리지설정의분리**
 - 픽스처전용의 `pytest.ini` 또는 `pyproject.toml` 를 생성
 - `--no-cov` 옵션의기본값화

2. **E2E테스트ランナー의 복원또는재구현**
 - 현재의워크플로우에合わせた설계
 - GitHub Issue생성/クローズ의 자동화

3. **목리스폰스의充実**
 - 実際의 CLI출력에 기반한목データ
 - エッジ케이스(타임아웃, レート제한)의 테스트

### 6.2 中期개선 (설계변경를伴う)

1. **통합테스트환경의구축**
 - Docker컨테이너로의 격리테스트
 - API키불필요의로컬LLM목

2. **테스트픽스처의拡充**
 - L2-medium: 복수파일수정
 - L3-complex: 리팩터링·설계변경

3. **CI/CD통합**
 - GitHub Actions로 의 테스트자동실행
 - Smoke테스트의조건付き실행

---

## 7. 関連문서

- `ARCHITECTURE.md`: 시스템설계
- `config.toml`: 설정파일
- `prompts/`: 각스테이트의 프롬프트정의

---

## 8. 변경履歴

| 日付 | 버전 | 변경내용 |
|------|-----------|---------|
| 2025-12-09 | 1.0 | 初版생성 (リバースエンジニアリング) |
| 2025-12-15 | 1.1 | IssueProvider 추상화추가 (Issue #284) |
