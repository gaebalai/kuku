# ADR-002: V5 베이스 개발로의 이전

## Status

Accepted

## Context

### 문제

신규 아키텍처(src/core)로의 V5 기능 이식을 진행하고 있었지만, 1개월 이상 경과해도 완료 전망이 서지 않고, 그 사이에 에이전트가 사용 불능인 상태가 계속되고 있었다.

### 이식 진척 상황

| 항목 | 상태 |
|------|------|
| prompts | 5/14 이전 완료 |
| CLI 가이드 | 1/3 이전 완료 |
| 오케스트레이터 본체 | 미이전 |
| bugfix 워크플로우 | **동작하지 않음** |

### V5(bugfix-v5)의 상태

- 9 스테이트의 상태 머신이 완전히 동작
- 테스트, 문서, 설계서가 갖추어져 있다
- Claude/Codex/Gemini의 3 에이전트 대응 완료

### src/core의 리팩터링 성과

- RunLogger: JSONL 실행 로그 (#29/#44에서 이식 완료)
- config.py: pydantic-settings 통합
- state.py: SessionState API 확장

이것들은 부분적인 개선이며, V5를 동작시키기에는 불충분했다.

## Decision

**V5 오리지널을 dao 리포지토리에 직접 복사하고, 메인 개발 대상으로 한다.**

- src/core/, src/bugfix_agent/, src/workflows/, docs/를 삭제
- V5(bugfix_agent/, prompts/, docs/, tests/)를 통째로 복사
- 개선(RunLogger 통합 등)은 V5가 동작하는 상태를 유지하면서 후속 PR에서 실시

### 채용 이유

1. **동작 우선**: 사용할 수 없는 도구를 개선을 계속하는 것에 가치는 없다
2. **완성품의 활용**: V5는 동작하는 완성품이며, 이식 코스트에 상응하지 않는다
3. **단계적 개선**: git history에 src/core의 성과는 남아 있으며, 필요 시 꺼낼 수 있다

### 기각한 선택지

| 선택지 | 기각 이유 |
|--------|---------|
| 이식을 계속 | 1개월 이상 진척 없음, 완료 전망 불명 |
| src/core와 공존 | 이중 관리에 의한 혼란 리스크 |

## Consequences

### Positive

- 에이전트가 즉시 사용 가능하게 된다
- 단일 코드 베이스로 관리가 간결
- V5의 문서·테스트가 그대로 이용 가능

### Negative

- src/core의 리팩터링 성과(pydantic-settings 등)를 일단 잃는다
- RunLogger 통합을 재차 수행할 필요가 있다

### Risks

- V5의 디렉토리 구조 전제 경로(config.py 등)의 수정이 필요 → 대응 완료
