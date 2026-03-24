# kuku 「쿠쿠」

AI-driven software development harness workflow orchestrator. Claude Code / Codex / Gemini CLI의 스킬을 워크플로우 YAML에 따라 실행한다.
참고로 쿠쿠란 말은 제주도 방언으로 '호호'라고 하는 말로 웃으며 작업하자는 의미로 쿠쿠라고 정했습니다.

> **V7 (kuku_harness)이 현재 정규 엔트리 포인트입니다.** `legacy/`는 V5/V6의 참조용 아카이브이며, 지원 대상 외입니다.

## 아키텍처 개요

3계층 아키텍처로 AI 에이전트를 제어:

```
┌─────────────────────────────────────────────┐
│  하네스 (kuku_harness/)                       │
│  워크플로우 YAML을 해석하여 CLI를 순차 호출 │
├─────────────────────────────────────────────┤
│  스킬 (.claude/skills/, .agents/skills/)     │
│  실체는 .claude, .agents는 symlink          │
├─────────────────────────────────────────────┤
│  CLI (Claude Code / Codex / Gemini)          │
│  스킬을 로드하여 프로젝트 컨텍스트에서 실행      │
└─────────────────────────────────────────────┘
```

상세: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 셋업 (개발자용)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 개발 워크플로우

Issue 기반 TDD 개발 플로우:

```
/issue-create → /issue-start → /issue-design → /issue-implement → /issue-pr → /issue-close
```

워크플로우 가이드: [docs/dev/workflow_guide.md](docs/dev/workflow_guide.md)

## 최소 도입

대상 프로젝트에 `.kuku/config.toml`을 배치한다 (코로케이티드 모델):

```toml
# .kuku/config.toml
[paths]
artifacts_dir = "~/.kuku/artifacts"

[execution]
default_timeout = 1800  # 필수: 타임아웃 기본값 (초)
```

skill의 실체는 `.claude/skills/`에 두고, `.agents/skills/`는 이를 참조하는 symlink로 취급한다.

```text
.claude/skills/
  implement/
    SKILL.md
  review-code/
    SKILL.md
  fix-code/
    SKILL.md
  verify-code/
    SKILL.md

.agents/skills/
  review-code -> ../../.claude/skills/review-code
  verify-code -> ../../.claude/skills/verify-code
```

최소 workflow는 다음과 같다.

```yaml
name: minimal-code-review
description: "최소 코드 리뷰 포함 플로우"
execution_policy: auto

steps:
  - id: implement
    skill: implement
    agent: claude
    on:
      PASS: review-code
      ABORT: end

  - id: review-code
    skill: review-code
    agent: codex
    on:
      PASS: end
      RETRY: fix-code
      ABORT: end

  - id: fix-code
    skill: fix-code
    agent: claude
    on:
      PASS: verify-code
      ABORT: end

  - id: verify-code
    skill: verify-code
    agent: codex
    resume: review-code
    on:
      PASS: end
      RETRY: fix-code
      ABORT: end
```

`resume`은 동일 agent의 이전 단계 컨텍스트를 이어받아 계속 실행하기 위한 지정.

## 워크플로우 실행

```bash
# 최소 workflow 실행
kuku run workflows/minimal-code-review.yaml 57

# 도중에 재개
kuku run workflows/minimal-code-review.yaml 57 --from fix-code

# 단일 스텝 실행
kuku run workflows/minimal-code-review.yaml 57 --step review-code
```

상세:
- [docs/dev/workflow-authoring.md](docs/dev/workflow-authoring.md)
- [docs/dev/skill-authoring.md](docs/dev/skill-authoring.md)

## 품질 체크

커밋 전에 반드시 실행:

```bash
source .venv/bin/activate
ruff check kuku_harness/ tests/       # Lint
ruff format kuku_harness/ tests/      # Format
mypy kuku_harness/                    # Type check
pytest                               # Test
```

## 문서

| 문서 | 내용 |
|-------------|------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | V7 아키텍처 상세 |
| [docs/adr/](docs/adr/) | 아키텍처 결정 기록 |
| [docs/dev/workflow_guide.md](docs/dev/workflow_guide.md) | 워크플로우 가이드 |
| [docs/dev/testing-convention.md](docs/dev/testing-convention.md) | 테스트 규약 (S/M/L) |
| [docs/dev/workflow-authoring.md](docs/dev/workflow-authoring.md) | 워크플로우 YAML 정의 |
| [docs/dev/skill-authoring.md](docs/dev/skill-authoring.md) | 스킬 작성 가이드 |
| [docs/cli-guides/](docs/cli-guides/) | CLI 도구 가이드 (Claude/Codex/Gemini) |

## `legacy/` 디렉토리

V5/V6의 구 코드·테스트·문서를 참조용으로 보관.

```
legacy/
├── bugfix_agent/                  # V5/V6 패키지
├── bugfix_agent_orchestrator.py   # V5 엔트리 포인트
├── prompts/                       # V6 프롬프트
├── tests/                         # V5 테스트
├── docs/                          # V5 문서
├── config.toml                    # V5 설정
└── AGENT.md                       # V5 에이전트 지시서
```

## License

Apache-2.0
