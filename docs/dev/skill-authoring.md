# 스킬 작성 매뉴얼

kuku_harness에서 호출되는 스킬의 작성법.

## 스킬의 역할

스킬은 "1스텝의 실제 작업"을 담당하는 프롬프트 자산. 하네스는 무엇을 어떤 순서로 실행하는지를 제어하고, 스킬 본체는 agent(Claude Code / Codex / Gemini)가 네이티브로 로드하여 실행한다.

**하네스는 스킬의 내용을 읽지 않는다**. 스킬의 로드는 CLI에 완전히 위임한다. 단, 실행 결과로서 나오는 `VERDICT`의 출력 계약에는 의존한다.

## 파일 배치

스킬의 실체는 `.kuku/config.toml`의 `paths.skill_dir`로 지정된 캐노니컬 디렉토리에 둔다. 다른 에이전트용 디렉토리(예: `.agents/skills/`)는 캐노니컬 디렉토리로의 심볼릭 링크로서 구성한다. 하네스는 `skill_dir`과 `skill` 필드에서 경로를 해결한다(`agent` 필드는 경로 해결에 사용하지 않는다).

```toml
# .kuku/config.toml
[paths]
skill_dir = ".claude/skills"   # 필수. 캐노니컬 디렉토리
```

```
.claude/skills/           # 캐노니컬 디렉토리(skill_dir로 지정)
  issue-design
  issue-implement
  issue-review-code

.agents/skills/           # 다른 에이전트용 symlink
  issue-review-code -> ../../.claude/skills/issue-review-code
```

각 스킬은 디렉토리이며, `SKILL.md`를 포함.

## SKILL.md 포맷

```markdown
---
name: issue-review-code
description: "코드 리뷰를 실시하고 verdict를 반환한다"
---

# Issue Review Code

(스킬의 설명과 프롬프트 본문)

## 출력 포맷

반드시 이하의 형식으로 verdict를 출력할 것:

---VERDICT---
status: PASS
reason: |
  리뷰 대상의 코드는 설계서와의 정합성·품질 기준을 충족하고 있다.
evidence: |
  - 테스트 커버리지: 87% (목표 80% 이상)
  - ruff / mypy: 에러 없음
  - 설계서의 전 요건이 구현되어 있다
suggestion: ""
---END_VERDICT---
```

## verdict 출력 규약

모든 스킬은 최종 출력으로서 이하의 형식의 verdict 블록을 포함해야 한다.

```
---VERDICT---
status: <PASS | RETRY | BACK | ABORT>
reason: |
  (1-2문으로 판단 이유를 요약)
evidence: |
  (판단의 근거가 되는 구체적 정보. 테스트 결과, 리뷰 지적, 차분 등)
suggestion: |
  (ABORT/BACK 시 필수: 다음 액션의 제안)
---END_VERDICT---
```

verdict 블록은 **stdout에 그대로 출력**할 것. 하네스는 CLI의 표준 출력에서 verdict를 추출하기 때문에, `gh issue comment --body`의 인수나 별도 명령어의 입력에만 verdict를 넣어도 판정되지 않는다.

Issue 코멘트와 Issue 본문 업데이트는 별도로 해도 되지만, 그것은 verdict 출력의 대체가 아니다. 코멘트 투고를 수행하는 경우에도, 최종적인 verdict 블록은 stdout에 남길 것.

### verdict의 선택 기준

| verdict | 사용 조건 |
|---------|---------|
| `PASS` | 목표를 달성하여 다음 스텝으로 진행해도 됨 |
| `RETRY` | 동일 스텝을 재실행함으로써 해결할 수 있는 문제가 있다 |
| `BACK` | 전단의 스텝을 수정하지 않으면 해결할 수 없는 문제가 있다 |
| `ABORT` | 워크플로우 전체를 정지해야 할 중대한 문제가 있다 |

**제약**:
- `ABORT` / `BACK`의 경우, `suggestion`은 필수 (빈 문자 불가)
- `evidence`는 필수 (빈 문자 불가)
- `reason`은 필수 (빈 문자 불가)
- `status`는 상기 4값만 유효

### YAML block scalar의 이용

`evidence` / `suggestion`에 복수 행을 쓰는 경우는 YAML block scalar (`|`)를 사용한다.

```
---VERDICT---
status: RETRY
reason: 테스트가 3건 실패하고 있다
evidence: |
  FAILED tests/test_workflow_parser.py::TestValidationErrors::test_empty_steps
  FAILED tests/test_cli_args.py::TestBuildClaudeArgs::test_basic_args
  FAILED tests/test_state_persistence.py::TestSessionState::test_load_or_create
suggestion: |
  실패하고 있는 테스트를 수정한 후 재시행할 것.
  특히 workflow_parser의 에러는 타입 체크 문제로 보인다.
---END_VERDICT---
```

## 하네스가 주입하는 컨텍스트 변수

스킬의 프롬프트에는 이하의 변수가 자동 주입된다.

| 변수 | 타입 | 설명 |
|------|-----|------|
| `issue_number` | int | GitHub Issue 번호 |
| `step_id` | str | 현재 스텝 ID |
| `previous_verdict` | str | 이전 스텝의 verdict 요약 (resume 스텝 등) |
| `cycle_count` | int | 현재 사이클 이터레이션 (사이클 내 스텝만) |
| `max_iterations` | int | 사이클의 상한 횟수 (사이클 내 스텝만) |

`previous_verdict`는 `resume` 지정 스텝에 주입된다. `review-code`처럼 독립 평가가 필요한 스텝에는 주입되지 않는다. 수정계 스킬에서는, 상세한 리뷰 내용은 Issue 코멘트를 정본으로 하고, `previous_verdict`는 보조적 요약으로서 취급한다.

## GitHub Issue의 활용

스킬은 GitHub Issue를 장기 기억으로서 사용한다.

```bash
# 작업 결과를 Issue에 코멘트
gh issue comment <issue_number> --body "..."

# Issue 본문을 업데이트 (상태의 기록)
gh issue edit <issue_number> --body "..."
```

**규칙**: 리뷰계 스킬(review-\*, verify-\*)은 Issue에 코멘트로 결과를 기록한다. 구현계 스킬은 완료 보고를 코멘트한다.

## 추천 패턴

### Devil's Advocate 프리앰블 (리뷰계)

리뷰 스킬에는 "비판적 시점"을 강제하는 프리앰블을 넣는다.

```markdown
> **CRITICAL**: 이 리뷰는 개선 제안이 아니라, 구현상의 결함을 발견하는 것이 목적.
> "문제 없어 보인다"고 생각한 경우에도, 경계 조건·타입 불일치·에러 전파 누락을 반드시 확인할 것.
```

### 인크리멘탈 커밋 (구현계)

구현 스킬은 논리적인 단위로 커밋을 분할한다.

```bash
git add <files> && git commit -m "feat: implement X component"
git add <files> && git commit -m "test: add tests for X"
```

## 수동·하네스 양립 스킬의 작성법

워크플로우 대상 스킬은, 하네스 구동과 수동 슬래시 명령어의 **양쪽에서 동작**하도록 설계한다.

### 입력 섹션

`## 인수` 대신 `## 입력` 섹션을 사용하여 양쪽의 입력 소스를 기재한다.

```markdown
## 입력

### 하네스 경유 (컨텍스트 변수)

| 변수 | 타입 | 설명 |
|------|-----|------|
| `issue_number` | int | GitHub Issue 번호 |
| `step_id` | str | 현재 스텝 ID |

### 수동 실행 (슬래시 명령어)

$ARGUMENTS = <issue-number>

### 해결 규칙

컨텍스트 변수 `issue_number`가 존재하면 그쪽을 사용.
없으면 `$ARGUMENTS`의 제1인수를 `issue_number`로서 사용.
```

**우선 순위**: 컨텍스트 변수 > `$ARGUMENTS`. 하네스가 변수를 주입하고 있는 경우는 그쪽을 사용하고, 수동 실행 시에는 종래대로 `$ARGUMENTS`에서 취득한다.

### 수동 전용 스킬

`issue-create`, `issue-start`처럼 워크플로우 시작 전의 페이즈를 담당하는 스킬은, 하네스 구동의 대상 외. verdict 출력은 추가하지만, 입력은 기존의 `$ARGUMENTS`를 유지한다.

### fix 스킬의 리뷰 결과 취득

`issue-fix-code`, `issue-fix-design`에서는, 하네스 경유에서도 수동 실행에서도, Issue 코멘트를 리뷰 결과의 정본으로서 취득한다. `previous_verdict`가 존재하는 경우는 보조 정보로서 사용해도 된다.

```markdown
### 리뷰 결과의 취득

1. Issue 코멘트에서 최신의 리뷰 결과를 취득한다
2. 컨텍스트 변수 `previous_verdict`가 존재하는 경우는 보조 정보로서 확인한다
```

### 품질 체크 명령어의 범용화

스킬 내에서 품질 체크 명령어를 기술하는 경우, 프로젝트 고유의 경로(예: `bugfix_agent/`)를 하드코딩하지 않는다. 대신 CLAUDE.md를 참조하는 형태로 한다.

```markdown
**품질 체크 (커밋 전 필수)**:

CLAUDE.md의 "Pre-Commit (REQUIRED)" 섹션에 기재된 명령어를 실행할 것.
```

## 관련 문서

- [워크플로우 정의 매뉴얼](workflow-authoring.md)
- [테스트 규약](testing-convention.md)
- [Architecture](../ARCHITECTURE.md)
