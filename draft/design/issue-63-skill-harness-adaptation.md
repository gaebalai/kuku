# [설계] 스킬를dao하네스적용프로젝트용에 수정 + 워크플로우YAML생성

Issue: #63

## 개요

기존의 `.claude/skills/` 内스킬(전13개)를, dao-harness 워크플로우エンジン와 수동スラッシュ명령어의**両方로 동작**한다하도록수정한다.併せて `workflows/feature-development.yaml` 를 생성한다.

**스코프**:
- 워크플로우 YAML 는 **claude-only**(전스텝의 agent 이 `claude`)로생성한다.codex / gemini 용스킬(`.agents/skills/`)의 정비는별 Issue 으로 한다
- **워크플로우대상스킬(11개)**: issue-design, issue-review-design, issue-fix-design, issue-verify-design, issue-implement, issue-review-code, issue-fix-code, issue-verify-code, issue-doc-check, issue-pr, issue-close
- **수동전용스킬(2개)**: issue-create, issue-start — 워크플로우시작전의 준비페이즈이며, 하네스구동의대상외.verdict 출력만추가し, 입력는기존의 `$ARGUMENTS` 를 유지한다

## 배경·목적

현재의스킬는수동실행(`/issue-implement 63`)전용에설계되어 있다.dao-harness 부터구동하려면 verdict 블록출력와컨텍스트변수대응이필요だが, 수동실행기능도유지한い.수정는"추가·확장"를 기본와し, 기존기능를삭제하지 않는다.

## 인터페이스

### 입력

스킬는이하의2つ의 입력소스를**両立지원**한다.

| 소스 | 제공원 | 이용가능한 변수 |
|--------|--------|---------------|
| 컨텍스트변수 | dao-harness 이 자동주입 | `issue_number`, `step_id`, `previous_verdict`, `cycle_count`, `max_iterations` |
| `$ARGUMENTS` | Claude Code スラッシュ명령어 | 유저이 전달하다인수문자열 |

**우선順位**: 컨텍스트변수이존재すればそちら를 사용.なければ `$ARGUMENTS` 부터취득.

### 출력

각스킬는기존의완료보고에加え, 말미에 verdict 블록를출력한다.

```
---VERDICT---
status: <PASS | RETRY | BACK | ABORT>
reason: |
 (1-2文로 판정이유)
evidence: |
 (구체적근거)
suggestion: |
 (ABORT/BACK時는 필수)
---END_VERDICT---
```

### 사용예

**수동실행(종래通り):**
```bash
# Claude Code のスラッシュ명령어로서
/issue-implement 63
```

**하네스구동:**
```bash
# dao CLI 부터워크플로우로서
dao run workflows/feature-development.yaml 63
```

## 제약·전제 조건

- 스킬의작업내용(절차·리뷰기준·커밋규약·품질 체크등)는一切변경하지 않는다
- 기존의"다음스텝"섹션는남기다(수동時に有用, 하네스는 verdict 만참조)
- `$ARGUMENTS` 섹션는남기다(수동실행의입력수단)
- 품질 체크명령어의ハード코드경로 `bugfix_agent/` 는 범용화한다

## 방침

### 1. 워크플로우대상스킬(11개)：입력섹션의확장

기존의 `## 인수` 섹션를 `## 입력` 섹션에改名し, 両方의 입력소스를기재.

**주의**: 수동전용스킬(issue-create, issue-start)는대상외.기존의 `## 인수` 섹션를그まま유지한다.

```markdown
## 입력

### 하네스経由(컨텍스트변수)

**常에 주입된다변수:**

| 변수 | 타입 | 설명 |
|------|-----|------|
| `issue_number` | int | GitHub Issue 번호 |
| `step_id` | str | 현재의스텝 ID |

**조건付き로 주입된다변수(該当스킬만기재):**

| 변수 | 타입 | 조건 | 설명 |
|------|-----|------|------|
| `previous_verdict` | str | resume 지정스텝만 | 전스텝의 verdict(reason/evidence/suggestion) |
| `cycle_count` | int | 사이클내스텝만 | 현재의イテレーション번호 |
| `max_iterations` | int | 사이클내스텝만 | 사이클의상한회수 |

### 수동실행(スラッシュ명령어)

$ARGUMENTS = <issue-number>

### 해결규칙

컨텍스트변수 `issue_number` 이 존재すればそちら를 사용.
なければ `$ARGUMENTS` の第1인수를 `issue_number` 로서사용.
```

**스킬마다의입력변수목록:**

입력섹션에는, 그스킬로実際에 이용한다변수만를기재한다.

| 스킬 | 분류 | 常에 주입 | 조건付き |
|--------|------|---------|---------|
| issue-create | 수동전용 | N/A(`$ARGUMENTS = <title> [type] [description]`) | - |
| issue-start | 수동전용 | N/A(`$ARGUMENTS = <issue-number> [prefix]`) | - |
| issue-design | 워크플로우대상 | `issue_number`, `step_id` | - |
| issue-review-design | 워크플로우대상 | `issue_number`, `step_id` | `cycle_count`, `max_iterations` |
| issue-fix-design | 워크플로우대상 | `issue_number`, `step_id` | `previous_verdict`, `cycle_count`, `max_iterations` |
| issue-verify-design | 워크플로우대상 | `issue_number`, `step_id` | `cycle_count`, `max_iterations` |
| issue-implement | 워크플로우대상 | `issue_number`, `step_id` | - |
| issue-review-code | 워크플로우대상 | `issue_number`, `step_id` | `cycle_count`, `max_iterations` |
| issue-fix-code | 워크플로우대상 | `issue_number`, `step_id` | `previous_verdict`, `cycle_count`, `max_iterations` |
| issue-verify-code | 워크플로우대상 | `issue_number`, `step_id` | `cycle_count`, `max_iterations` |
| issue-doc-check | 워크플로우대상 | `issue_number`, `step_id` | - |
| issue-pr | 워크플로우대상 | `issue_number`, `step_id` | - |
| issue-close | 워크플로우대상 | `issue_number`, `step_id` | - |

### 2. 전스킬：verdict 블록의추가

전13스킬(워크플로우대상11개 + 수동전용2개)에 verdict 출력를추가.
기존의"완료보고"섹션의**後に** verdict 출력섹션를추가.

수동전용스킬(issue-create, issue-start)는 verdict 를 출력한다이, 워크플로우 YAML には含め없다.수동실행시의 verdict 는 표시된다만로, 전이제어에는使われ없다.

스킬마다의 verdict status 매핑:

| 스킬 | PASS | RETRY | BACK | ABORT |
|--------|------|-------|------|-------|
| issue-create | Issue 생성성공 | - | - | 생성실패 |
| issue-start | Worktree 구축성공 | - | - | 구축실패 |
| issue-design | 설계書생성·커밋완료 | - | - | 설계불가능한 요건 |
| issue-review-design | Approve | RETRY(Changes Requested) | - | ABORT 레벨의문제 |
| issue-fix-design | 수정완료 | - | - | 수정불가능 |
| issue-verify-design | Approve | RETRY(수정不十분) | - | ABORT 레벨의문제 |
| issue-implement | 구현·테스트·품질 체크전경로 | RETRY(테스트실패등) | BACK(설계에문제) | ABORT 레벨의문제 |
| issue-review-code | Approve | RETRY(Changes Requested) | BACK(설계에문제) | ABORT 레벨의문제 |
| issue-fix-code | 수정완료 | - | - | 수정불가능 |
| issue-verify-code | Approve | RETRY(수정不十분) | - | ABORT 레벨의문제 |
| issue-doc-check | 체크완료(업데이트유무問わず) | - | - | - |
| issue-pr | PR 생성성공 | RETRY(push 실패등) | - | ABORT 레벨의문제 |
| issue-close | クローズ완료 | RETRY(머지실패등) | - | ABORT 레벨의문제 |

**주의**: `on` 매핑로사용하지 않는다 status は, 스킬内で"출력요건"로서列挙하지 않는다.워크플로우 YAML 의 `on` と整合させる.

### 3. review/verify 스킬：verdict status 와 판정의一貫한대응

리뷰系스킬(review-design, review-code, verify-design, verify-code)의 기존판정를 verdict status 에 대응付ける.**전리뷰系스킬로統一**한다.

| 기존판정 | verdict status | 전이선(cycle 内) | 설명 |
|---------|---------------|-------------------|------|
| Approve | PASS | cycle 外の次스텝로 | 리뷰/검증合格 |
| Changes Requested | RETRY | fix 스텝へ(cycle loop head) | 수정이필요 |

**사이클内의 전이플로우:**

```
design-review 사이클:
 review-design → RETRY → fix-design → verify-design → RETRY → fix-design(loop)
 → PASS → implement → PASS → implement

code-review 사이클:
 review-code → RETRY → fix-code → verify-code → RETRY → fix-code(loop)
 → PASS → doc-check → PASS → doc-check
```

review 스텝는 cycle 의 entry 이며, RETRY 시에 fix(loop head)へ전이한다.
verify 스텝는 cycle 의 loop tail 이며, RETRY 시에 fix(loop head)へ戻る.
いずれ도 PASS 로 cycle を抜けて次스텝へ進む.

### 4. fix 스킬：`previous_verdict` 의 폴백대응

issue-fix-code, issue-fix-design 의 Step 1(컨텍스트취득)에이하를추가:

```markdown
### 리뷰결과의취득

1. 컨텍스트변수 `previous_verdict` 이 존재하는 경우는그것를 확인(하네스経由)
2. 존재하지 않는다경우는 Issue 코멘트부터최신의리뷰결과를취득(수동실행시)
```

### 5. 경로범용화

`bugfix_agent/` のハード코드를이하에변경:

```markdown
**품질 체크(커밋전필수)**:

CLAUDE.md の"Pre-Commit (REQUIRED)"섹션에기재된명령어를 실행한다것.
```

이것에 의해 프로젝트 마다의 CLAUDE.md 에 정의된품질 체크이자동적으로 적용된다.

### 6. 워크플로우 YAML 생성

`workflows/feature-development.yaml` 를 생성.

- **agent**: 전스텝 `claude`(claude-only 워크플로우)
- create / start 는 워크플로우외(수동로事前실행)
- design 부터 close 까지
- design-review 사이클(max 3), code-review 사이클(max 3)
- review 의 RETRY → fix へ, verify 의 RETRY → fix へ(cycle loop)
- verify 의 PASS → cycle 外の次스텝へ

**`resume` 지정과 `previous_verdict` 의 대응関係:**

fix 스텝는직전의 review/verify 스텝의컨텍스트를이어받다때문에, `resume` 를 지정한다.이것에 의해 `previous_verdict` 이 자동주입된다.

| fix 스텝 | `resume` 값 | resume 대상의설명 | previous_verdict 의 내용 |
|-------------|------------|------------------|----------------------|
| fix-design | `review-design` | 初회는 review-design 의 세션를계속.2회目이후도같은값(verify-design 의 verdict 는 `state.last_transition_verdict` 経由で渡る) | 리뷰/검증의指摘事項 |
| fix-code | `review-code` | 初회는 review-code 의 세션를계속.2회目이후도마찬가지 | 리뷰/검증의指摘事項 |

**YAML での表現:**

`resume` 는 step ID(문자열)를지정한다(`docs/dev/workflow-authoring.md` 準拠, `models.py: Step.resume: str | None`).

```yaml
steps:
 # ... 前略 ...
 - id: fix-design
 skill: issue-fix-design
 agent: claude
 resume: review-design # review-design 스텝의세션를계속
 on:
 PASS: verify-design
 ABORT: end
 - id: fix-code
 skill: issue-fix-code
 agent: claude
 resume: review-code # review-code 스텝의세션를계속
 on:
 PASS: verify-code
 ABORT: end
```

`resume: <step-id>` 지정에 의해, 하네스는이하를 수행한다:
1. 지정 step ID 의 세션 ID 를 `state.sessions` 부터취득し, CLI 의 `--resume` 옵션에전달하다(세션계속)
2. `state.last_transition_verdict` 를 `previous_verdict` 로서프롬프트에주입한다(`dao_harness/prompt.py` 準拠)

**mixed-agent 대응(codex / gemini)**: 本 Issue 의 스코프외.별 Issue 로 `.agents/skills/` 에 스킬를배치し, 워크플로우 YAML 의 agent 필드를변경한다形로 대응한다.

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.

### Small 테스트
- 수정후의 각 SKILL.md 에 verdict 출력섹션이존재한다か(문자열패턴매치)
- 입력섹션에컨텍스트변수과 $ARGUMENTS の両方이 기재되어 있다인가
- `bugfix_agent/` がハード코드되어 있지 않다인가
- fix 스킬에 `previous_verdict` 폴백기술이 있다인가
- 워크플로우 YAML 의 구문타당성(`dao_harness.workflow.load_workflow` 로 파싱가능인가)

### Medium 테스트
- 워크플로우 YAML 의 밸리데이션(`dao_harness.workflow.validate_workflow` を通過한다인가)
- 사이클정의의정합성(entry / loop 스텝이正しく참조되어 있다인가)
- 전스텝의 `skill` 이 파일시스템上에 존재한다か(`dao_harness.skill.validate_skill_exists`)
- fix 스텝에 `resume` 이 설정되어 있다か(`previous_verdict` 주입의전제 조건)
- 각스킬의 SKILL.md verdict example 이 파일읽기 → `parse_verdict()` 로 정상에파싱할 수 있다か(파일 I/O + verdict 파서ー결합)
- 워크플로우전스텝의전이先이 도달가능か(step 존재확인 + transition 정합성)

### Large 테스트
- 워크플로우 YAML + 수정완료스킬로 `dao run --step <step-id>` 를 단일스텝실행し, verdict 이 정상에 parse 된다인가

### 스킵한다サイズ
- **Large**: 물리적에생성불가.이유는이하의2点:
 1. `dao` CLI 엔트리 포인트이미구현(`pyproject.toml` 의 `[project.scripts]` 이 코멘트아웃상태)
 2. 단일스텝실행는 `WorkflowRunner` → `execute_cli()` → `subprocess.Popen(["claude", ...])` の経路を辿り, 実際의 AI 에이전트프로세스의기동이필수.CI 환경로에이전트바이너리 + API 키를전제으로 한다테스트는구성할 수 없다

## 영향문서

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 없음 | 새로운技術選定없음 |
| docs/ARCHITECTURE.md | 없음 | 아키텍처변경없음 |
| docs/dev/skill-authoring.md | 있음 | 수동·하네스両立스킬의 작성법가이드를추가(Phase 5) |
| docs/dev/development_workflow.md | 없음 | 워크플로우自体는 변경없음 |
| docs/cli-guides/ | 없음 | CLI 사양변경없음 |
| CLAUDE.md | 없음 | 규약변경없음 |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| skill-authoring.md | `docs/dev/skill-authoring.md` | verdict 출력규약, 컨텍스트변수사양, SKILL.md 포맷를정의.전스킬는 verdict 블록필수 |
| workflow-authoring.md | `docs/dev/workflow-authoring.md` | 워크플로우 YAML 의 구조, step 필드(`on` 매핑), cycle 정의의사양 |
| ARCHITECTURE.md | `docs/ARCHITECTURE.md` | V7 의 3계층아키텍처(Workflow YAML → Skill 계약 → Skill 구현)를정의.스킬는 Layer 3 |
| ADR 001 | `docs/adr/001-review-cycle-pattern.md` | review 과 verify の区별, 수렴보증(verify 는 신규指摘금지), max 3 iterations |
| ADR 003 | `docs/adr/003-skill-harness-architecture.md` | V6→V7 移행결정.CLI skill harness + 프로젝트 skills 의 구성 |
| prompt.py | `dao_harness/prompt.py` | 컨텍스트변수의주입로직.`issue_number`, `step_id`, `previous_verdict`, `cycle_count`, `max_iterations` |
| testing-convention.md | `docs/dev/testing-convention.md` | S/M/L 테스트サイズ정의, 스킵판정기준 |
