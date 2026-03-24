# 워크플로우 정의 매뉴얼

kuku_harness가 읽어들이는 YAML 워크플로우 정의의 작성법.

## 전제 조건

워크플로우를 실행하는 프로젝트에는 `.kuku/config.toml`이 필요합니다. 이것이 프로젝트 루트의 마커가 됩니다.

```toml
# .kuku/config.toml (최소 구성)
[paths]
artifacts_dir = "~/.kuku/artifacts"   # 생략 시 기본값

[execution]
default_timeout = 1800               # 필수: 타임아웃 기본값 (초)
```

## 파일 배치

```
workflows/
  feature-development.yaml
  bugfix.yaml
```

## 전체 구조

```yaml
name: feature-development          # 필수: 워크플로우명
description: "설계→구현→PR 플로우"  # 필수: 설명
execution_policy: auto             # 필수: auto / sandbox / interactive
default_timeout: 600               # 생략 가능: 워크플로우 전체의 기본 타임아웃(초)

cycles:                            # 생략 가능: 루프 사이클 정의
  <cycle-name>:
    entry: <step-id>
    loop: [<step-id>, ...]
    max_iterations: 3
    on_exhaust: ABORT

steps:                             # 필수: 스텝 목록 (위부터 순서대로 실행)
  - id: <step-id>
    skill: <skill-name>
    agent: claude                  # claude / codex / gemini
    on:
      PASS: <next-step-id>
      RETRY: <step-id>
```

## 스텝 필드

| 필드 | 타입 | 필수 | 설명 |
|-----------|-----|------|------|
| `id` | str | ✅ | 스텝 ID. 영숫자와 하이픈 |
| `skill` | str | ✅ | 스킬명 (`<agent>.skills/<name>`의 룩업 키) |
| `agent` | str | ✅ | `claude` / `codex` / `gemini` |
| `on` | mapping | ✅ | verdict → next step ID의 매핑. 비어있지 않을 것 |
| `model` | str | — | 모델명 (생략 시 agent 기본값) |
| `effort` | str | — | `low` / `medium` / `high` (agent가 지원하는 경우) |
| `max_budget_usd` | float | — | 코스트 상한 (USD) |
| `max_turns` | int | — | 턴 수 상한 |
| `timeout` | int | — | 타임아웃(초). 폴백: step.timeout → workflow.default_timeout → config.execution.default_timeout |
| `resume` | str | — | resume할 스텝 ID (동일 agent의 세션 계속) |

### `on` 매핑

값은 **스텝 ID** 또는 **`end`**를 지정한다.

| verdict | 의미 |
|---------|------|
| `PASS` | 성공. 다음 스텝으로 진행 |
| `RETRY` | 재시행. 동일 스텝을 재실행 |
| `BACK` | 차등. 전단 스텝을 재실행 |
| `ABORT` | 중단. 워크플로우 전체를 정지 |

`end`를 값으로 지정하면 워크플로우 종료.

## 사이클 정의

review → fix → verify와 같은 루프를 선언한다.

```yaml
cycles:
  code-review:
    entry: review-code      # 사이클로의 입구 스텝
    loop:                   # RETRY 시 루프 스텝 군
      - fix-code
      - verify-code
    max_iterations: 3       # fix→verify를 1 이터레이션으로 카운트
    on_exhaust: ABORT       # max_iterations 도달 시 발행하는 verdict
```

**제약**: `loop` 말미 스텝의 `on.RETRY`는 `loop` 선두 스텝을 가리킬 것.

## execution_policy

| 값 | 동작 |
|----|------|
| `auto` | 전 agent에서 승인·sandbox를 바이패스 (완전 자동) |
| `sandbox` | sandbox 내에서 자동 실행 (파일 쓰기를 제한) |
| `interactive` | 승인 플로우 유효 (수동 확인 있음) |

## resume (세션 계속)

동일 agent 내에서 컨텍스트를 이어받는 경우에 지정한다.

```yaml
steps:
  - id: design
    skill: design
    agent: claude
    on:
      PASS: implement

  - id: implement
    skill: implement
    agent: claude
    resume: design          # design 스텝의 세션을 계속
    on:
      PASS: end
```

`resume` 대상 스텝과 `agent`가 다른 경우 밸리데이션 에러.

## 완전 샘플

```yaml
name: feature-development
description: "설계→구현→코드 리뷰의 표준 플로우"
execution_policy: auto

cycles:
  code-review:
    entry: review-code
    loop:
      - fix-code
      - verify-code
    max_iterations: 3
    on_exhaust: ABORT

steps:
  - id: design
    skill: issue-design
    agent: claude
    model: claude-sonnet-4-6
    effort: high
    on:
      PASS: implement
      ABORT: end

  - id: implement
    skill: issue-implement
    agent: claude
    resume: design
    on:
      PASS: review-code
      ABORT: end

  - id: review-code
    skill: issue-review-code
    agent: codex
    on:
      PASS: end
      RETRY: fix-code
      ABORT: end

  - id: fix-code
    skill: issue-fix-code
    agent: claude
    on:
      PASS: verify-code
      ABORT: end

  - id: verify-code
    skill: issue-verify-code
    agent: codex
    resume: review-code
    on:
      PASS: end
      RETRY: fix-code
      ABORT: end
```

## 실행 명령어

```bash
# 통상 실행 (첫 번째 스텝부터)
kuku run workflows/feature-development.yaml 57

# 도중부터 재개 (--from으로 시작 스텝 지정)
kuku run workflows/feature-development.yaml 57 --from fix-code

# 단발 실행 (1스텝만 실행하고 종료)
kuku run workflows/feature-development.yaml 57 --step review-code

# config 탐색의 기점 디렉토리를 지정
kuku run workflows/feature-development.yaml 57 --workdir ../kuku-feat-57

# 에이전트 출력의 스트리밍 표시를 억제
kuku run workflows/feature-development.yaml 57 --quiet
```

**주의**: `--from`과 `--step`은 배타 옵션입니다 (동시 지정 불가).

### 밸리데이션

워크플로우 YAML을 실행 전에 검증할 수 있습니다:

```bash
# 단일 파일 밸리데이션
kuku validate workflows/feature-development.yaml

# 복수 파일 일괄 밸리데이션
kuku validate workflows/*.yaml
```

**출력 예**:

```
✓ workflows/feature-development.yaml
✗ workflows/bad.yaml
  - Step 'review' transitions to unknown step 'fix' on RETRY

Validation failed: 1 of 2 files had errors.
```

- 성공: `✓ <filename>`이 stdout에 출력, exit 0
- 실패: `✗ <filename>` + 에러 상세가 stderr에 출력, exit 1
- 인수 없음: argparse 에러, exit 2

### 종료 코드

| 종료 코드 | 의미 |
|-----------|------|
| 0 | 정상 종료 |
| 1 | 워크플로우 ABORT 또는 예기치 않은 에러 |
| 2 | 정의 에러 (YAML 부정, 스킬 미검출, 인수 에러, `.kuku/config.toml` 미검출 등) |
| 3 | 실행 시 에러 (CLI 실행 실패, 타임아웃, verdict 해석 실패 등) |

## 관련 문서

- [스킬 작성 매뉴얼](skill-authoring.md)
- [Architecture](../ARCHITECTURE.md)
