# ADR 003: Python 상태 머신에서 CLI 스킬 하네스로의 전환

**Status**: Accepted
**Date**: 2026-03-09
**Issue**: #57

## 컨텍스트

현행의 `bugfix_agent/`(V6)는 Python 상태 머신 오케스트레이터로, 약 2000 LOC. Claude / Codex / Gemini의 CLI를 외부에서 호출하고, 스텝 실행·verdict 해석·상태 전이를 제어하고 있었다.

**과제**:

1. **프로젝트 컨텍스트의 단절**: 외부 오케스트레이터에서는 각 프로젝트의 문서(코딩 규약, 테스트 규약, 설계 템플릿)를 참조할 수 없다.
2. **CLI 네이티브 기능의 재구현**: Claude Code가 네이티브로 가지고 있는 기능(스킬 실행, 컨텍스트 관리, 도구 호출)을 Python으로 재구현하고 있으며, 보수 코스트가 높다.
3. **CLI 버전 추종 코스트**: Claude v2.0→v2.1, Codex v0.63→v0.112, Gemini v0.18→v0.31로의 추종이 곤란.

## 결정

V6를 폐지하고, **CLI 스킬 하네스(V7 = `dao_harness/`)**로 이전한다.

### 설계 방침

**3계층 아키텍처**:

| 계층 | 책무 | 실체 |
|---|------|------|
| Layer 1: 워크플로우 정의 | 무엇을 어떤 순서로 실행하는가 | `workflows/*.yaml` |
| Layer 2: 스킬 입출력 계약 | verdict 형식·컨텍스트 변수 | `docs/dev/skill-authoring.md` |
| Layer 3: 스킬 본체 | 실제 작업의 프롬프트 | `paths.skill_dir`로 설정한 캐노니컬 디렉토리 + symlink |

**하네스의 역할**: 워크플로우 YAML을 해석하여 CLI를 외부 호출하고 스킬을 순차 실행한다. 스킬의 로드는 CLI에 위임. 하네스는 스킬의 내용을 읽지 않는다.

**기억 구조**:

| 계층 | 매체 | 수명 |
|---|------|------|
| 단기 | CLI resume 세션 | 세션 내 |
| 중기 | `session-state.json`, run 로그 | 워크플로우 실행 중 |
| 장기 | GitHub Issue(본문·코멘트) | 영속 |

**이전 전략**:

- `git tag v6.0`으로 V6 현상을 저장. V7 구현 중에는 `git show v6.0:<path>`로 필요한 노하우를 참조 가능
- `bugfix_agent/`는 이전 기간 중의 **참조용 아카이브**이며, 보수·기능 추가의 대상 외
- V7 구현 완료 후에 `bugfix_agent/`를 삭제

## 근거

- **CLI 네이티브 기능의 활용**: 스킬이 `cwd=workdir`로 실행됨으로써, 프로젝트 문서로의 접근이 가능해진다. 이것은 외부 오케스트레이터에서는 실현 불가능.
- **경량 설계**: "하네스는 전이 제어만, 스킬이 실제 작업"이라는 책무 분리에 의해, 보수 대상이 대폭 축소된다 (~2000 LOC → ~1300 LOC의 하네스 본체 + 프로젝트마다의 스킬).
- **Anthropic 베스트 프랙티스 준수**: [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)의 "Initializer + Coding Agent 패턴"과 같은 설계 사상.

## 영향

- `dao_harness/` 패키지를 신설 (`pyproject.toml`에 등록)
- `CLAUDE.md`의 품질 체크 명령어를 `dao_harness/`에 업데이트
- `docs/dev/workflow-authoring.md`, `docs/dev/skill-authoring.md`를 신설
- `docs/ARCHITECTURE.md`를 V7 하네스 아키텍처에 개정

## 대체안과 기각 이유

**LangChain / LangGraph 등의 프레임워크 채용**: 외부 의존이 늘어나고, CLI 버전 추종 문제가 해소되지 않는다. 프로젝트 컨텍스트 단절 문제도 남는다.

**V6의 단계적 개수**: 프로젝트 컨텍스트 단절이라는 근본 과제는, 외부 오케스트레이터의 아키텍처를 유지하는 한 해결할 수 없다.
