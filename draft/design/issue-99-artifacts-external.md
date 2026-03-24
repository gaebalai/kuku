# [설계] artifacts 의 출력선를 worktree 外에 이동한다

Issue: #99

## 개요

`kuku run` 의 artifacts(실행로그·세션상태)의 기본값출력선를 `~/.kuku/artifacts/` 에 변경し, worktree 삭제時에 로그이失われ없다구성에한다.

## 배경·목적

현재 artifacts 는 worktree 内(`{repo_root}/.kuku-artifacts/`)에출력된다때문에, 이하의문제이 있다:

1. **事後검증不能**: `issue-close` 로 worktree 를 삭제하면過去의 run 로그이소실한다
2. **後처리의경합**: worktree 삭제後에 하네스이 `run.log` 를 참조し ENOENT 로 이상종료한다(旧 #96)
3. **worktree の使い捨て性が損なわれる**: artifacts が残っ하고 있다위해삭제타이밍에제약이生じる

## 인터페이스

### 입력

#### `config.toml` 의 `[paths]` 섹션

```toml
[paths]
# 絶対경로지정(추천)
artifacts_dir = "/home/user/.kuku/artifacts"

# 또는 ~ 전개
artifacts_dir = "~/.kuku/artifacts"

# 상대경로(종래호환: repo_root 에서의상대)
artifacts_dir = ".kuku-artifacts"
```

- 未지정시의 기본값: `~/.kuku/artifacts`
- `~` 는 런타임로 `Path.expanduser()` 에 의해전개

#### 경로해결규칙

| 지정형식 | 해결방법 |
|---------|---------|
| `~/.kuku/artifacts` | `Path.expanduser()` → 絶対경로 |
| `/abs/path` | 그まま사용 |
| `relative/path` | `repo_root / relative/path` |

### 출력

변경없음.디렉토리구조는현행와동일:

```
{artifacts_dir}/
└── {issue_number}/
 ├── session-state.json
 ├── progress.md
 └── runs/
 └── {YYMMDDhhmm}/
 ├── run.log
 └── {step_id}/
 ├── stdout.log
 ├── console.log
 └── stderr.log
```

### 사용예

```python
# config.toml 없음(기본값)
# → ~/.kuku/artifacts/99/session-state.json

# config.toml: artifacts_dir = "~/.kuku/artifacts"
# → /home/user/.kuku/artifacts/99/session-state.json

# config.toml: artifacts_dir = ".kuku-artifacts"(종래호환)
# → {repo_root}/.kuku-artifacts/99/session-state.json
```

## 제약·전제 조건

- 기존의 `.kuku-artifacts/` 디렉토리의마이그레이션는행わ없다(수동移행)
- `~` 전개는 Python 의 `Path.expanduser()` に依拠한다.전개실패시(`RuntimeError`)는 `ConfigLoadError` 로 변환하여보고한다
- `..` 를 포함상대경로는引き続き거부한다(repo_root 이스케이프방지)
- artifacts_dir 하위의디렉토리구조(issue 번호 / runs / etc.)는변경하지 않는다

## 방침

### 1. `PathsConfig` 의 기본값값변경

```python
@dataclass(frozen=True)
class PathsConfig:
 artifacts_dir: str = "~/.kuku/artifacts" # 변경: ".kuku-artifacts" → "~/.kuku/artifacts"
```

### 2. 경로해결로직(`kukuConfig.artifacts_dir` プロパティ)

```python
@property
def artifacts_dir(self) -> Path:
 expanded = Path(self.paths.artifacts_dir).expanduser()
 if expanded.is_absolute():
 return expanded
 return self.repo_root / self.paths.artifacts_dir
```

- `~` 付き → `expanduser()` で絶対경로에 → 그まま반환
- 絶対경로 → 그まま반환
- 상대경로 → `repo_root / path`(종래동작)

### 3. 밸리데이션변경(`_validate_artifacts_dir`)

현재의밸리데이션:
- 絶対경로 → **거부** ← 이것를 철폐
- `..` 를 포함 → 거부

변경後:
- `~` 전개시의 `RuntimeError` 를 `ConfigLoadError` 로 변환
- `~` 전개後に絶対경로인지 아닌지를판정
- 絶対경로 → **허가**
- 상대경로로 `..` 를 포함 → 거부(종래通り)

```python
@staticmethod
def _validate_artifacts_dir(config_path: Path, artifacts_dir: str) -> None:
 try:
 expanded = Path(artifacts_dir).expanduser()
 except RuntimeError as e:
 raise ConfigLoadError(
 config_path,
 f"paths.artifacts_dir: failed to expand '~': {e}",
 ) from e
 if expanded.is_absolute():
 return # 絶対경로는무조건로허가
 # 상대경로의 경우만 .. 체크
 p = PurePosixPath(artifacts_dir)
 if ".." in p.parts:
 raise ConfigLoadError(...)
```

`expanduser()` 실패시는 `ConfigLoadError` 로 변환한다함으로써, `cli_main.py` 의 기존에러ハンドリング(`EXIT_CONFIG_NOT_FOUND`)에乗せる.`EXIT_ABORT`(상정외예외)이 아니라, 설정에러로서명확에보고된다.

### 4. 테스트수정

기존테스트의期待값를신기본값에合わせて업데이트한다.絶対경로거부테스트는"허가"테스트에변경.

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.

### Small 테스트

- `PathsConfig` 의 기본값값이 `~/.kuku/artifacts` 이다것
- `kukuConfig.artifacts_dir` プロパティ의 경로해결로직:
 - `~` 付き문자열 → `expanduser()` 로 전개된絶対경로
 - 絶対경로문자열 → 그まま반환
 - 상대경로문자열 → `repo_root / path`
- `_validate_artifacts_dir`:
 - 絶対경로 → 에러에라면없다
 - `~` 付き경로 → 에러에라면없다
 - 상대경로로 `..` → `ConfigLoadError`
 - 통상의상대경로 → 에러에라면없다
 - `expanduser()` 이 `RuntimeError` を送出 → `ConfigLoadError` 로 변환된다

### Medium 테스트

- `config.toml` に絶対경로를지정 → `kukuConfig._load` が正しく파싱し `artifacts_dir` プロパティが絶対경로를 반환하다
- `config.toml` 에 `~` 付き경로를지정 → `expanduser()` 후의 경로이返る
- `config.toml` 에 상대경로를지정 → 종래호환로 `repo_root / path` が返る
- `config.toml` 未지정(기본값) → `~/.kuku/artifacts` 이 전개된絶対경로이返る
- `SessionState.load_or_create` + `_persist` 이 worktree 외의 디렉토리에正しく써넣다
- `WorkflowRunner` 이 worktree 외의 artifacts_dir 에 로그를출력한다
- CLI `cmd_run` 이 기본값 config 로 `~/.kuku/artifacts` 상당의 경로를 `WorkflowRunner` 에 전달하다

### Large 테스트

- `kuku run` 를 서브프로세스로 실행し, artifacts 이 지정한絶対경로하위에생성된다것을확인(테스트로는 `tmp_path` ベースの絶対경로를 config 에 지정し, 実유저의 `~/.kuku/` を汚さ없다)
- `kuku run --workdir` 지정시에 config discovery + artifacts 경로해결이正しく동작한다것을확인
- **worktree 삭제後の残存확인(완료조건 (3))**: `kuku run` 실행후에 workdir(worktree 상당)를 `shutil.rmtree` 로 삭제し, artifacts_dir 하위의 `run.log` / `session-state.json` が残存하고 있다것을검증한다
- **後처리의비의존性확인(완료조건 (4))**: `kuku run` 의 실행후(`WorkflowRunner.run()` が返った後)에 workdir 를 삭제하여も, 하네스이 artifacts_dir 内의 파일를정상에참조할 수 있다것(＝ ENOENT 이 발생하지 않는다것)를 검증한다

## 영향문서

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| README.md | 있음 | L34-40: `artifacts_dir = ".kuku-artifacts"` 를 기본값값의예로서기재.신기본값 `~/.kuku/artifacts` 에 업데이트이필요 |
| docs/ARCHITECTURE.md | 있음 | L201-204: `artifacts_dir` 의 기본값값를 `.kuku-artifacts` と明記.신기본값에업데이트이필요 |
| docs/dev/workflow-authoring.md | 있음 | L9-13: `artifacts_dir = ".kuku-artifacts"` 를 최소구성예로서기재.신기본값에업데이트이필요 |
| docs/adr/ | 없음 | 새로운技術選定는 없다 |
| docs/cli-guides/ | 없음 | CLI 인터페이스의변경는 없다 |
| CLAUDE.md | 없음 | 규약변경는 없다 |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| 현행 config 구현 | `kuku_harness/config.py` | `PathsConfig.artifacts_dir` 의 기본값값, `_validate_artifacts_dir` 의 밸리데이션로직, `kukuConfig.artifacts_dir` プロパティ의 경로해결를확인 |
| 현행 state 구현 | `kuku_harness/state.py` | `SessionState` 이 `artifacts_dir` 를 인수로수신, 그하위에 `session-state.json` / `progress.md` 를 써넣다구조를확인 |
| 현행 runner 구현 | `kuku_harness/runner.py:62-72` | `WorkflowRunner` 이 `artifacts_dir` 를 수신, `runs/{timestamp}` 디렉토리를 생성하여로그를출력한다구조를확인 |
| 현행 CLI 구현 | `kuku_harness/cli_main.py:208` | `config.artifacts_dir` 를 `WorkflowRunner` 에 전달하다箇所를 확인 |
| 기존테스트 | `tests/test_config.py` | 絶対경로거부테스트(L100-107), 기본값값테스트(L33-35, L156-164)이변경대상이다것을확인 |
| Python Path.expanduser | `pathlib` 표준라이브러리 (`/usr/lib/python3.12/pathlib.py:1400-1412`, `/usr/lib/python3.12/posixpath.py:247-285`) | `~` 를 `$HOME` 에 전개한다.`HOME` 환경변수이미설정의 경우는 `pwd` 모듈에폴백.해결不能時는 `RuntimeError` を送出한다 |
| Issue #99 | GitHub Issue | 완료조건: (1) 기본값출력선이 `~/.kuku/artifacts/`, (2) 絶対경로지정가능, (3) worktree 삭제로로그이남다, (4) 후처리이壊れ없다 |
