# ADR-001: Review-Fix-Verify 사이클 패턴

## Status

Accepted

## Context

dev-agent-orchestra의 워크플로우에서, 리뷰 사이클이 수렴하지 않는 문제가 발생하고 있었다.

### 문제

`review → fix → review` 루프에서는:

1. 매회 풀 리뷰를 실행하기 때문에, 신규 지적이 발생하여 계속된다
2. 사소한 지적의 반복으로 사이클이 수렴하지 않는다
3. 워크플로우가 파탄하는 리스크가 있다

### 배경

Issue #6에서 Claude Code 스킬을 도입한 때, jquants 워크플로우의 `review → fix → verify` 패턴을 채용하여 효과가 확인되었다.

## Decision

리뷰 사이클에 `verify` 스테이트를 도입한다.

### review vs verify의 차이

| 관점 | review | verify |
|------|--------|--------|
| 목적 | 풀 리뷰 | 수정 확인만 |
| 신규 지적 | 있음 | 없음 |
| 수렴 보증 | 없음 | 있음 |

### 스테이트 전이

```
REVIEW ──(PASS)──> COMPLETE
   │
   └──(RETRY)──> FIX ──(always)──> VERIFY
                                      │
                        ┌─────────────┴─────────────┐
                        │                           │
                      PASS                        RETRY
                        │                           │
                        v                           v
                    COMPLETE                       FIX
```

### 수렴 보증의 메커니즘

1. `verify`는 "지적 사항이 수정되었는지"만을 확인
2. 신규 지적을 추가하지 않음으로써 루프를 수렴시킨다
3. 이 규칙은 프롬프트 설계로 담보 (AI로의 명시적 지시)

### VERDICT 프로토콜과의 관계

**결론: VERDICT 프로토콜은 확장하지 않는다**

```
PASS / RETRY / BACK_DESIGN / ABORT
```

**이유:**

1. **하위 호환성**: 기존 VERDICT 파서나 테스트에 영향을 주지 않는다
2. **스테이트 전이로 구별 가능**: `review`와 `verify`의 차이는 VERDICT 값이 아니라, 어떤 스테이트에서 발행되었는지로 판단할 수 있다
3. **심플함**: 새로운 VERDICT 값을 추가하면, 모든 워크플로우에서 대응이 필요해져 복잡해진다

같은 `RETRY`라도, 어떤 스테이트에서 발행되었는지로 전이처가 바뀐다.

### 수렴 보증의 제약

- verify → fix → verify 루프는 **최대 3회**까지로 한다
- 3회를 초과한 경우, 루프 카운터에 의해 강제적으로 ABORT로 전이
- 이 제약은 `SessionState.loop_counters`로 관리

## Consequences

### Positive

- 리뷰 사이클의 수렴이 보증된다
- 워크플로우의 예측 가능성이 향상
- 기존 VERDICT 프로토콜과의 호환성 유지

### Negative

- 스테이트 수의 증가 (각 워크플로우에 FIX / VERIFY를 추가)
- 프롬프트 설계로의 의존 (코드로의 강제는 곤란)

### Risks

- AI가 `verify`에서 신규 지적을 추가해 버릴 가능성
  - 대책: 프롬프트로 명시적으로 금지, 루프 카운터에 의한 강제 종료

## References

- Issue #6: Issue 기반 개발 워크플로우의 도입
- docs/DEVELOPMENT_WORKFLOW.md
