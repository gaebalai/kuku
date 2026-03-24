---
description: Issue생성과 라벨부여를 수행한다. 개발워크플로우의 기점.
name: issue-create
---

# Issue Create

GitHub Issue를 생성하고, 적절한 라벨을 부여합니다.

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| 새 기능・버그수정・리팩터의 착수 전 | ✅ 필수 |
| 기존 Issue가 있는 경우 | ❌ 불필요 |

## 인수

```
$ARGUMENTS = <title> [type] [description]
```

- `title` (필수): Issue 타이틀
- `type` (임의): `feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `perf` (기본값: feat)
- `description` (임의): 상세설명. 생략 시는 대화로 수집.

## type → 라벨 매핑

| type | 라벨 | 용도 |
|------|--------|------|
| `feat` | `enhancement` | 새 기능추가 |
| `fix` | `bug` | 버그수정 |
| `refactor` | `refactoring` | 리팩터링 |
| `docs` | `documentation` | 문서 |

## 실행절차

### Step 1: 인수의 해석

`$ARGUMENTS` 에서 `title`, `type`, `description` 을 취득합니다.

- `type` 이 미지정인 경우는 `feat` 를 기본값으로 한다
- `description` 이 미지정인 경우는, 사용자에게 상세를 확인한다

### Step 2: Issue본문의 생성

이하의 구성으로 Issue본문을 생성합니다:

```markdown
## 개요

(description 의 내용)

## 목적

(왜 이 변경이 필요한가)

## 완료조건

- [ ] (달성해야 할 조건)
```

### Step 3: Issue생성과 라벨부여

```bash
gh issue create --title "[title]" --body "[body]" --label "[label]"
```

### Step 4: 완료보고

이하의 형식으로 보고해주세요:

```
## Issue생성완료

| 항목 | 값 |
|------|-----|
| Issue | #[issue-number] |
| 타이틀 | [title] |
| Type | [type] |
| 라벨 | [label] |
| URL | [issue-url] |

### 다음스텝

작업을 시작하려면 `/issue-start [issue-number]` 를 실행해주세요.
```

## Verdict 출력

실행완료 후, 이하의 형식으로 verdict 를 출력할 것:

---VERDICT---
status: PASS
reason: |
  Issue 생성성공
evidence: |
  Issue #XX 를 생성
suggestion: |
---END_VERDICT---

### status 의 선택기준

| status | 조건 |
|--------|------|
| PASS | Issue 생성성공 |
| ABORT | 생성실패 |
