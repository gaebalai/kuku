# [설계] dao → kuku リネーム

Issue: #73

## 개요

패키지名·CLI 명령어·리포지토리명를 `dao` 부터 `kuku`(舵)에전面リネーム한다.DAO(Data Access Object)패턴와의이름충돌를解지우다る.

## 배경·목적

- `dao` は広く知られた Data Access Object 패턴의약칭이며, 본프로젝트의목적(워크플로우オーケストレーション)と無関係な連想を生む
- `kuku`(舵)는"舵取り＝방향제어"のメタファーで, 워크플로우의제어와いう본질를表現한다
- PyPI·GitHub 上로 `kuku` / `apokamo/kuku` が未사용이다것을확인완료

## 인터페이스

### 입력

リネーム대상의전파일(후술의스코프表참조).

### 출력

| 대상 | Before | After |
|------|--------|-------|
| 패키지디렉토리 | `dao_harness/` | `kuku_harness/` |
| CLI 명령어 | `dao` | `kuku` |
| pyproject.toml name | `dev-agent-orchestra` | `kuku` |
| pyproject.toml scripts | `dao = "dao_harness.cli_main:main"` | `kuku = "kuku_harness.cli_main:main"` |
| setuptools packages | `dao_harness*` | `kuku_harness*` |
| GitHub 리포지토리 | `apokamo/dev-agent-orchestra` | `apokamo/kuku` |
| Worktree 명명 규칙 | `dao-[prefix]-[number]` | `kuku-[prefix]-[number]` |

### 사용예

```bash
# Before
dao run workflows/feature-development.yaml 73
dao validate workflows/feature-development.yaml

# After
kuku run workflows/feature-development.yaml 73
kuku validate workflows/feature-development.yaml
```

```python
# Before
from dao_harness.runner import WorkflowRunner
from dao_harness.models import Workflow

# After
from kuku_harness.runner import WorkflowRunner
from kuku_harness.models import Workflow
```

## 제약·전제 조건

- **하위 호환性는 불필요**: `dao` 명령어의에일리어스·호환레이어는設け없다(유저는作者만)
- **legacy/ 는 대상外**: V5/V6 코드는すで에 비지원.참조先も존재하지 않는다
- **draft/design/ の過去설계書**: リネーム대상외.`development_workflow.md` 의 정의通り, Close 시에 Issue 本文へ아카이브され worktree 삭제로自然소멸한다一時산출물이며, 履歴문맥를壊すリスクのほう이 큰
- **workflow YAML 변경완료**: `workflows/feature-development.yaml` 의 agent/model 調整は事前에 완료완료(未커밋).本 Issue 의 스코프에含めて커밋한다
- **테스트期待값의追随이 필요**: workflow 事前調整에 의해 `fix-code` 의 `resume` 를 삭제완료때문, 구사양를전제에한테스트期待값도본 Issue 内로 업데이트한다
- **`.dao/` 디렉토리**: #70 로 신설予定때문본 Issue では扱わ없다(아직존재하지 않는다)

## 방침

### 페이즈1: 패키지リネーム(코드)

1. `git mv dao_harness/ kuku_harness/` 로 디렉토리リネーム
2. `kuku_harness/` 内의 전 `.py` 파일로 `dao_harness` → `kuku_harness` 를 치환
3. `tests/` 内의 전 `.py` 파일로 `dao_harness` → `kuku_harness` 를 치환
4. `pyproject.toml` 를 업데이트:
 - `name = "kuku"`
 - `dao = "dao_harness.cli_main:main"` → `kuku = "kuku_harness.cli_main:main"`
 - `include = ["dao_harness*"]` → `include = ["kuku_harness*"]`
5. `pip install -e ".[dev]"` で再설치

### 페이즈2: 문서·스킬정의

1. `CLAUDE.md`: `dao_harness` → `kuku_harness`, `dao` CLI → `kuku` CLI
2. `README.md`: 프로젝트名·사용예
3. `docs/` 하위: CLI 명령어예, 패키지참조
4. `.claude/skills/`: Worktree 명명 규칙 `dao-` → `kuku-`
5. `uv.lock`: `pyproject.toml` 의 name 변경에 수반하여 `uv lock` で再생성(수동편집하지 않는다)
6. workflow 事前調整に追随한다테스트期待값의수정
 - 예: `tests/test_skill_harness_adaptation.py` 의 `fix-code` resume 필수전제를신사양에合わせる

### 페이즈3: 품질검증

```bash
source .venv/bin/activate
ruff check kuku_harness/ tests/ && ruff format kuku_harness/ tests/ && mypy kuku_harness/ && pytest
```

전체크通過를 확인.

### 페이즈4: 커밋·プッシュ

1. workflow YAML 변경를含めて커밋
2. 패키지リネーム를 커밋
3. 문서업데이트를커밋
4. push

### 페이즈5: 리포지토리リネーム(GitHub)

1. `gh repo rename kuku`
2. 로컬 bare repository の再 clone(Issue 本文의 절차을 따른다)

### 치환대상의망라적리스트

| 카테고리 | 파일수 | 치환패턴 |
|----------|-----------|-------------|
| 패키지소스 (`kuku_harness/`) | 13 | `dao_harness` → `kuku_harness` |
| 테스트 (`tests/`) | 21 | `dao_harness` → `kuku_harness` |
| pyproject.toml | 1 | name, scripts, packages |
| CLAUDE.md | 1 | `dao_harness` → `kuku_harness`, `dao` CLI → `kuku` |
| README.md | 1 | 프로젝트명, CLI 예 |
| docs/ | ~8 | CLI 예, 패키지참조 |
| .claude/skills/ | 3 | Worktree 명명 규칙 `dao-` → `kuku-` |
| uv.lock | 1 | `pyproject.toml` 의 name 변경에 수반하여 `uv lock` で再생성 |

### 주의事項: 부분일치의회피

- `dao` 의 단순치환는 `document` 등에誤매치하지 않는다(`dao` 는 독립토큰로서出現)
- 단 `dao_harness` は先에 치환し, 残った `dao` CLI 참조를개별에처리한다
- 정규表現 `\bdao\b` で境界매치를 사용し, 誤치환를방지한다

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.

본변경는리팩터링(リネーム)이며, 신규로직의추가는 없다.기존테스트スイート이 그ままリグレッション테스트로서기능한다.

### Small 테스트
- **기존테스트의通過확인**: `tests/` 内의 전 Small 테스트(`@pytest.mark.small`)이 `kuku_harness` import 로 정상에동작한다것
- 대상: 밸리데이션, 파서ー, 모델, 프롬프트ビルダー등의単体테스트
- 신규테스트추가: 불필요(로직변경없음)

### Medium 테스트
- **기존테스트의通過확인**: 전 Medium 테스트(`@pytest.mark.medium`)이새로운패키지名·CLI 名로 동작한다것
- 대상: CLI 인수파싱, 워크플로우실행, ロギング통합, 세션상태영속화등
- 特에 주의: CLI エントリーポ인ト이 `kuku` 명령어로서동작한다것
- **workflow 事前調整와 의 정합성확인**: `workflows/feature-development.yaml` 의 mixed-agent / resume 방침에 대해, Medium 테스트의期待값이구사양에고정되어 있지 않다것

### Large 테스트
- **기존테스트의通過확인**: 전 Large 테스트(`@pytest.mark.large`)이 E2E 로 동작한다것
- 대상: `test_e2e_cli.py` — 実際의 CLI 호출이 `kuku` 명령어로동작한다것
- CLI 의 서브프로세스호출경로이正しく해결된다것을검증

### 스킵한다サイズ
- 없음(전サイズとも기존테스트로검증가능)

## 영향문서

이변경에 의해업데이트이필요에된다가능性의 있다문서를列挙한다.

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 있음 | ADR 003 에 `dao_harness` 패키지참조있음 |
| docs/ARCHITECTURE.md | 있음 | `dao` CLI·패키지로의참조있음 |
| docs/dev/ | 있음 | development_workflow.md 의 Worktree 명명 규칙, workflow-authoring.md 의 CLI 예 |
| docs/cli-guides/ | 없음 | 3파일존재한다이 `dao` / `dao_harness` / `dev-agent-orchestra` 로의참조없음(grep 확인완료) |
| README.md | 있음 | 프로젝트명 `dev-agent-orchestra`, `dao_harness` 패키지참조, `dao` CLI 사용예이残存 |
| CLAUDE.md | 있음 | pre-commit 명령어, CLI 사용예 |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| Issue #73 本文 | `gh issue view 73` | リネーム스코프, 작업절차, 주의事項의 정의원 |
| pyproject.toml | `./pyproject.toml` | 현행의 CLI エントリーポ인ト정의: `dao = "dao_harness.cli_main:main"` |
| setuptools find_packages | https://setuptools.pypa.io/en/latest/userguide/package_discovery.html | `[tool.setuptools.packages.find]` 의 `include` 패턴이 `kuku_harness*` へ변경가능이다것의 근거 |
| gh repo rename | https://cli.github.com/manual/gh_repo_rename | `gh repo rename kuku` 로 리포지토리名를 변경한다명령어 |
| GitHub repo rename docs | https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository | リネーム後に旧 URL 부터신 URL 로의자동리다이렉트이설정된다근거."GitHub will automatically redirect links to your repository to the new name." |
| PyPI name availability | https://pypi.org/pypi/kuku/json | JSON API 이 404 를 반환하다함으로써 `kuku` 이 PyPI 上で未사용이다것을확인.`/project/kuku/` 는 브라우저용중간ページ의 영향로 200 를 반환하다경우이 있다때문에, 機械검증로는 JSON API 를 source-of-truth 으로 한다 |
