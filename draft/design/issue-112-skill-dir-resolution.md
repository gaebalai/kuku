# [설계] 스킬디렉토리해결의에이전트비의존화

Issue: #112

## 개요

`skill.py` 의 `SKILL_DIRS` ハード코드를폐지し, `.kuku/config.toml` 로 설정가능한 단일캐노니컬디렉토리에 의한스킬해결에移행한다.

## 배경·목적

현재의 `SKILL_DIRS` 는 agent 名와 디렉토리의매핑를ハード코드하고 있다:

```python
SKILL_DIRS = {
 "claude": ".claude/skills",
 "codex": ".agents/skills",
 "gemini": ".agents/skills",
}
```

이설계에는이하의문제이 있다:

1. **暗黙의 claude 의존**: `.agents/skills/` 는 `.claude/skills/` 로의심볼릭 링크를전제로서おり, claude 이 존재하지 않는다구성(codex 만, gemini 만)로파탄한다
2. **하네스이알다필요의없다関心事의 혼입**: 각 CLI 이 어떤디렉토리부터스킬를 로드한다か는 파일시스템(심볼릭 링크)의 책무이며, 하네스의검증로직이 agent → directory 매핑를 가진다필요이 없다
3. **新에이전트추가시의 코드변경**: 새로운 agent 이 추가된다たび에 `SKILL_DIRS` にエントリ를 추가한다필요이 있다

## 인터페이스

### 입력

#### config.toml 의 변경

```toml
[paths]
artifacts_dir = ".kuku-artifacts"
skill_dir = ".claude/skills" # 추가.기본값값: ".claude/skills"
```

- `skill_dir`: 스킬의실체이저장된다캐노니컬디렉토리(workdir 에서의상대경로)
- 생략시는 `".claude/skills"` 를 기본값으로 한다(하위 호환)
- **상대경로限定**(`..` 금지, 絶対경로불가).`artifacts_dir` 와 는 규칙이 다르다
 - 이유: `validate_skill_exists` 의 `is_relative_to(workdir)` 체크에 의해, repo 外の絶対경로는必ず `SecurityError` 이 된다.config で受理하여도 pre-flight で弾かれる모순를防ぐ
 - `artifacts_dir` 는 repo 外(`~/.kuku/artifacts`)에 둔다정당한 유스케이스이 있다위해絶対경로를허용한다이, 스킬는 repo 内에 존재한다전제때문상대경로만

#### validate_skill_exists 의 변경

**현재**:
```python
def validate_skill_exists(skill_name: str, agent: str, workdir: Path) -> None:
```

**변경後**:
```python
def validate_skill_exists(skill_name: str, workdir: Path, skill_dir: str) -> None:
```

- `agent` 파라미터를삭제
- `skill_dir` 파라미터를추가(config 부터취득한값를전달하다)

### 출력

- 변경없음(`None` 를 반환하다인가, `SkillNotFound` / `SecurityError` 를 raise)

### 사용예

```python
# runner.py 로 의 호출(변경후)
for step in self.workflow.steps:
 validate_skill_exists(step.skill, self.project_root, self.config.paths.skill_dir)
```

```toml
# claude + codex 구성(기본값)
[paths]
skill_dir = ".claude/skills"
# → .agents/skills/ 는 .claude/skills/ 로의심볼릭 링크

# codex 만구성
[paths]
skill_dir = ".agents/skills"
# → .claude/skills/ 는 불필요.스킬실체를 .agents/skills/ 에 배치
```

## 제약·전제 조건

- **하위 호환와기본값값의근거**: `skill_dir` 생략시는 `".claude/skills"` 를 기본값으로 한다.Issue 本文の"설정없음=에러.暗黙의 기본값는持た없다"는 agent→directory 매핑의문제(미지의 agent 에 대해暗黙로 경로를추측하지 않는다)를指하고 있으며, 본설계는그매핑自体를 폐지한다함으로써해결한다.`skill_dir` 의 기본값값는 agent 매핑와는 별次元의 설정이며, `execution.default_timeout`(필수·기본값없음)とは異되어, 기존프로젝트의破壊적변경를避ける위해기본값값를持たせる
- **config.toml 필수**: `kukuConfig.discover()` が既에 필수이다때문에, 新たな의존는추가하지 않는다
- **CLI 마다의스킬로드경로는변경하지 않는다**: 하네스는캐노니컬디렉토리로존재확인한다만.각 CLI がど의 경로부터스킬를 로드한다か는 파일시스템(심볼릭 링크)로해결한다
- **경로트래버설방어를유지**: 현행의 `..` 체크과 `resolve()` + `is_relative_to()` 체크를그まま남기다

## 방침

### 1. config.py 로의 skill_dir 추가

`PathsConfig` 에 `skill_dir: str` 필드를추가.기본값값 `".claude/skills"`.
`_load()` 로 의 밸리데이션는 `_validate_skill_dir` 로서신설(`..` 금지, 絶対경로불가, 타입체크).`artifacts_dir` は絶対경로를허용한다때문에, 동일밸리데이터는使わ없다.

### 2. skill.py の簡素화

`SKILL_DIRS` dict 를 삭제し, `validate_skill_exists` のシグネチャ를 변경:

```python
def validate_skill_exists(skill_name: str, workdir: Path, skill_dir: str) -> None:
 if ".." in skill_name.split("/"):
 raise SecurityError(...)
 base = workdir / skill_dir / skill_name / "SKILL.md"
 resolved = base.resolve()
 if not resolved.is_relative_to(workdir.resolve()):
 raise SecurityError(...)
 if not resolved.exists():
 raise SkillNotFound(...)
```

- `agent` 파라미터가 없く된다때문에, `Unknown agent` 에러경로도삭제된다

### 3. runner.py 의 호출변경

```python
# 변경전
validate_skill_exists(step.skill, step.agent, self.project_root)

# 변경후
validate_skill_exists(step.skill, self.project_root, self.config.paths.skill_dir)
```

### 4. 문서정리

이하의문서로 `.agents/skills/` 과 `.claude/skills/` の二重관리전제의기술를정리:

- `docs/dev/skill-authoring.md`: "파일배치"섹션 — 캐노니컬디렉토리와설정방법의설명에개정
- `docs/ARCHITECTURE.md`: Layer 3 의 설명 — 단일캐노니컬디렉토리 + symlink 구성에개정
- `docs/adr/003-skill-harness-architecture.md`: Layer 3 의 `.claude/skills/, .agents/skills/` 併記を, 캐노니컬디렉토리(`paths.skill_dir` 로 설정)+ symlink 구성에개정.Issue #112 완료조건로업데이트이明記되어 있다위해대상에포함하다

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.
> 상세는 [테스트 규약](../../../docs/dev/testing-convention.md) 참조.

### Small 테스트

- **skill_dir 파라미터로의스킬해결**: `validate_skill_exists(skill_name, workdir, skill_dir)` 이 지정디렉토리로正しく SKILL.md を検出한다것
- **커스텀 skill_dir**: `".agents/skills"` 와 `"custom/skills"` 등비기본값의디렉토리로도동작한다것
- **경로트래버설방어의유지**: `..` 를 포함 skill_name 이 `SecurityError` 를 raise 한다것(기존테스트의移행)
- **SkillNotFound**: 존재하지 않는다스킬로 `SkillNotFound` 이 raise 된다것(기존테스트의移행)
- **config 파싱**: `PathsConfig` 의 `skill_dir` 기본값값, 명시적지정, `..` 금지밸리데이션의검증

### Medium 테스트

- **심볼릭 링크経由의 해결**: `skill_dir` 이 심볼릭 링크先を指す경우로도 `resolve()` で正しく検出할 수 있다것(`tmp_path` 에 심볼릭 링크를 생성하여테스트)
- **Runner 통합**: `WorkflowRunner` 이 `config.paths.skill_dir` 를 `validate_skill_exists` に渡し, 워크플로우내전스텝의스킬를사전 검증할 수 있다것(CLI 실행는목)

### Large 테스트

- **E2E 스킬로드검증**: 実際의 `.kuku/config.toml` + `.claude/skills/` + `.agents/skills/` 심볼릭 링크구성로 `kuku run <workflow> <issue> --step <step-id>` 를 실행し, CLI 이 스킬를네이티브로로드하여실행시작하면무렵까지검증한다(pre-flight 검증만로없이, CLI 의 스킬로드경로経由의 실행를 포함 E2E)
- **커스텀 skill_dir 로 의 E2E**: `config.toml` 의 `skill_dir` 를 비기본값값에변경한상태로 `kuku run --step` 이 정상에동작한다것

## 영향문서

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 있음 | ADR 003 의 Layer 3 テーブル를 업데이트(`.claude/skills/, .agents/skills/` 併記 → `paths.skill_dir` 로 설정한다캐노니컬디렉토리) |
| docs/ARCHITECTURE.md | 있음 | Layer 3 와 패키지구성의 skill.py 설명를업데이트 |
| docs/dev/ | 있음 | skill-authoring.md 의 파일배치섹션를업데이트 |
| docs/cli-guides/ | 없음 | CLI 側의 스킬로드機構는 변경하지 않는다 |
| CLAUDE.md | 없음 | 규약변경없음 |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| 현행 skill.py | `kuku_harness/skill.py` | `SKILL_DIRS` dict 이 에이전트→디렉토리의ハード코드매핑를 가진다(L7-11).본설계의직접적인 변경대상 |
| 현행 config.py | `kuku_harness/config.py` | `PathsConfig` 에 `artifacts_dir` 의 패턴이존재し, `skill_dir` を同패턴로추가할 수 있다.`_validate_artifacts_dir` 의 밸리데이션로직를 `skill_dir` にも적용한다근거 |
| runner.py 의 호출 | `kuku_harness/runner.py:58` | `validate_skill_exists(step.skill, step.agent, self.project_root)` — 현재의호출箇所.`agent` → `config.paths.skill_dir` 로의변경이필요 |
| 현행 .agents/skills/ | `.agents/skills/` | 既에 모두의エントリ이 `../../.claude/skills/*` 로의심볼릭 링크로서구성완료.캐노니컬디렉토리방식로의移행는현행의파일시스템구성와整合한다 |
| skill-authoring.md | `docs/dev/skill-authoring.md:11-23` | "스킬의실체는 `.claude/skills/` に置き, `.agents/skills/` は그것를 참조한다 symlink 로서다루다"と明記완료.본설계는이방침를코드側로 정식에反映한다 |
| ARCHITECTURE.md | `docs/ARCHITECTURE.md:48-49` | Layer 3 이 `.claude/skills/` 과 `.agents/skills/` 를 병렬에기술하고 있다이, 본설계로캐노니컬 + symlink の関係에 개정한다 |
