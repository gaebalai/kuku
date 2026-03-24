---
description: 워크플로우를 수동 실행하여 검증하고, 실패 시는 계속하지 않고 원인을 조사하여 Issue 에 기록한다. 성공 시도 발견 사항이나 막힌 점을 Issue 에 기록한다.
name: kuku-run-verify
---

# kuku Run Verify

`kuku run` 에 의한 워크플로우의 수동 검증을 표준화합니다.
검증 목적의 실행이며, 에러 발생 시는 그 시점에서 정지하고, 원인 조사와 Issue 코멘트를 우선합니다.

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| 워크플로우 변경 후의 실기 검증 | ✅ 필수 |
| 「`kuku run workflows/... <issue>` 를 실행하고, 결과를 Issue 에 남겨줘」라고 의뢰되었을 때 | ✅ 추천 |
| 통상의 feature 개발을 그대로 진행하고 싶을 때만 | ⚠️ 임의 |
| 단순히 YAML 의 정적 검증만 하고 싶을 때 | ❌ `kuku validate` 만으로 충분 |

## 입력

### 수동 실행(슬래시 커맨드)

```
$ARGUMENTS = <workflow-path> <issue-number> [kuku run options...]
```

- `workflow-path` (필수): 예 `workflows/feature-development.yaml`
- `issue-number` (필수): GitHub Issue 번호
- `kuku run options...` (임의): `--from` / `--step` / `--workdir` / `--quiet` 등을 그대로 후속에 전달

### 예

```bash
/kuku-run-verify workflows/feature-development.yaml 73
/kuku-run-verify workflows/feature-development.yaml 73 --from fix-code
/kuku-run-verify workflows/feature-development.yaml 73 --workdir ../kuku-feat-73
```

## 전제 지식의 읽기

이하를 필요에 따라 참조할 것.

1. **워크플로우 정의**: `docs/dev/workflow-authoring.md`
2. **스킬 생성 규약**: `docs/dev/skill-authoring.md`
3. **공통 Worktree 해결**: `../_shared/worktree-resolve.md`

## 공통 규칙

- 에러가 발생하면, 추가의 `kuku run` 재실행으로 앞으로 진행하지 않는다. 먼저 원인 조사와 Issue 코멘트를 완료시킨다.
- 장시간 실행 중의 상태 확인은, 매번 세밀하게 폴링하지 않고 **2 분 정도의 간격** 을 기준으로 해도 좋다. 신규 출력이 없어도 `kuku run` 프로세스 자체가 계속하고 있는 한, 즉시 정지 취급하지 않는다.
- review / fix / verify 사이클 중의 반려나, agent 가 자력으로 수정 가능한 일시적 실패는, workflow 전체의 실패로 보지 않고 과잉으로 정지하지 않는다. `kuku run` 자체의 종료, 명확한 행, 수작업 개입 필수의 이상이 확인된 시점에서 정지 판단을 행한다.
- 성공 시도 `신경 쓰인 점` 과 `막힌 점` 을 기록한다. 없으면 `특히 없음` 이라고 명기한다.
- Issue 코멘트에는 원본 로그 전문을 붙이지 않고, 요점과 필요한 발췌만을 기재한다.
- 원인을 단정할 수 없는 경우는, **확정 사항** 과 **가설** 을 나눠서 쓴다.

## 실행절차

### Step 1: 인수의 해석

`$ARGUMENTS` 에서 이하를 취득한다.

1. `workflow_path`
2. `issue_number`
3. `extra_args` (`kuku run` 에 그대로 전달하는 나머지 인수)

`workflow_path` 는 메인 리포지토리 기준의 상대 경로로서 해결하고, 파일이 존재하는 것을 확인한다.

### Step 2: Worktree 의 해결(`--workdir` 미지정 시에만)

`extra_args` 에 `--workdir` 가 포함되어 있지 않은 경우에만,
[_shared/worktree-resolve.md](../_shared/worktree-resolve.md) 의 절차로 Issue 본문에서 Worktree 를 해결한다.

- 해결할 수 있는 경우: `kuku run` 에 `--workdir [resolved-path]` 를 추가한다
- 해결할 수 없는 경우: `--workdir` 없이 속행해도 좋다. 단, Issue 코멘트에 그 취지를 명기한다

### Step 3: 사전 검증

먼저 `kuku validate` 를 실행한다.

```bash
cd [main-repo-absolute-path] && source .venv/bin/activate && kuku validate [workflow-path]
```

- exit 0: 다음으로 진행
- exit 1 이상: **여기서 정지**
  - YAML 정의 에러 또는 인수 에러로서 취급
  - `kuku run` 은 실행하지 않는다
  - 표준 출력 / 표준 에러의 요점을 기록

### Step 4: 워크플로우 실행

로그를 보존하면서 `kuku run` 을 실행한다.

```bash
LOG_FILE=$(mktemp)
cd [main-repo-absolute-path] && source .venv/bin/activate && \
  kuku run [workflow-path] [issue-number] [extra_args...] 2>&1 | tee "$LOG_FILE"
RUN_EXIT=${PIPESTATUS[0]}
```

### Step 5: 판정과 조사

#### 5.1 성공 시(exit 0)

- 실행 커맨드
- 사용한 `workdir`
- 실행한 옵션
- 로그의 요점
- 신경 쓰인 점 / 막힌 점
- 다음 회용 노하우

를 정리하여 Issue 에 코멘트한다.

#### 5.2 실패 시(exit 비 0)

**그 자리에서 정지하고, 계속 실행하지 않을 것.**

최소한, 이하를 조사한다.

1. **어디서 멈췄는가**
   - 마지막으로 시작한 step / 성공한 step / 실패한 step
2. **종료 코드의 종별**
   - `1`: 워크플로우 ABORT 또는 예기하지 못한 에러
   - `2`: 정의 에러(YAML 부정, 스킬 미검출, 인수 에러 등)
   - `3`: 실행 시 에러(CLI 실행 실패, 타임아웃, verdict 해석 실패 등)
3. **관련 파일**
   - 해당 workflow YAML
   - 실패 step 이 가리키고 있는 SKILL.md
   - 필요하면 Issue 본문, worktree 상태, 대상 로그
4. **원인의 정리**
   - 확정 사항
   - 유력한 원인 가설
   - 추가로 필요한 액션

필요에 따라 이하의 조사를 행한다.

```bash
sed -n '1,220p' [workflow-path]
gh issue view [issue-number] --comments
git worktree list
```

### Step 6: Issue 코멘트

성공・실패 어느 쪽이든, Issue 에 반드시 코멘트한다.
`gh issue comment --body-file - <<'EOF'` 를 사용하여, 이하의 템플릿을 베이스로 기록할 것.

#### 성공 템플릿

````bash
gh issue comment [issue-number] --body-file - <<'EOF'
# 워크플로우 실행 검증 결과

## 실행 커맨드

```bash
kuku validate [workflow-path]
kuku run [workflow-path] [issue-number] [extra_args...]
```

## 결과

| 항목 | 값 |
|------|-----|
| Workflow | `[workflow-path]` |
| Issue | #[issue-number] |
| Exit Code | 0 |
| Workdir | `[resolved-or-explicit-workdir]` |
| Validation | PASS |

## 로그 요점

```text
(주요한 출력을 10-30 행 정도로 발췌)
```

## 신경 쓰인 점 / 막힌 점

- (없으면 `특히 없음`)

## 다음 회용 노하우

- (없으면 `특히 없음`)
EOF
````

#### 실패 템플릿

````bash
gh issue comment [issue-number] --body-file - <<'EOF'
# 워크플로우 실행 검증 결과

## 실행 커맨드

```bash
kuku validate [workflow-path]
kuku run [workflow-path] [issue-number] [extra_args...]
```

## 실패 개요

| 항목 | 값 |
|------|-----|
| Workflow | `[workflow-path]` |
| Issue | #[issue-number] |
| Exit Code | `[exit-code]` |
| 정지 위치 | `[step-or-phase]` |
| Workdir | `[resolved-or-explicit-workdir]` |
| Validation | PASS / FAIL |

## 원인 조사

### 확정 사항

- ...

### 원인 가설

- ...

### 추가로 확인한 커맨드

- `...`

## 로그 발췌

```text
(실패 원인을 알 수 있는 범위의 발췌)
```

## 신경 쓰인 점 / 막힌 점

- ...

## 다음 회용 노하우

- ...

## 제안 액션

- ...
EOF
````

## 완료 보고

성공 시:

```
## 워크플로우 실행 검증 완료

| 항목 | 값 |
|------|-----|
| Workflow | [workflow-path] |
| Issue | #[issue-number] |
| 판정 | PASS |

Issue 에 검증 결과와 노하우를 코멘트 완료.
```

실패 시:

```
## 워크플로우 실행 검증 중단

| 항목 | 값 |
|------|-----|
| Workflow | [workflow-path] |
| Issue | #[issue-number] |
| 판정 | ABORT |

Issue 에 실패 원인의 조사 결과를 코멘트 완료.
```

## Verdict 출력

실행 완료 후, 이하의 형식으로 verdict 를 출력할 것:

---VERDICT---
status: PASS
reason: |
  워크플로우의 수동 검증이 완료되고, Issue 에 결과를 기록했다
evidence: |
  kuku validate 와 kuku run 이 완료되고, 로그 요점・발견 사항・노하우를 Issue 에 코멘트했다
suggestion: |
---END_VERDICT---

### status 의 선택 기준

| status | 조건 |
|--------|------|
| PASS | `kuku validate` 와 `kuku run` 이 성공하고, Issue 코멘트까지 완료 |
| ABORT | 밸리데이션 실패, 실행 실패, 전제 부족, 또는 원인 조사가 필요 |
