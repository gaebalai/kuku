---
description: Issue요건에 기반하여, draft/design/에 설계서를 생성한다. worktree내에서의 작업이 전제.
name: issue-design
---

# Issue Design

지정된 Issue에 기반하여, 설계서(Markdown)를 생성합니다.
설계서는 `draft/design/` 에 생성되며, Issue Close 시에 Issue 본문에 아카이브됩니다.

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| Issue착수 후, 구현 전 | ✅ 필수 |
| worktree가 존재하지 않는다 | ❌ 먼저 `/issue-start` 를 실행 |

**워크플로우 내의 위치**: create → start → **design** → review-design → implement → review-code → doc-check → pr → close

## 입력

### 하네스경유(컨텍스트변수)

**항상 주입되는 변수:**

| 변수 | 타입 | 설명 |
|------|-----|------|
| `issue_number` | int | GitHub Issue 번호 |
| `step_id` | str | 현재 스텝 ID |

### 수동실행(슬래시 명령)

```
$ARGUMENTS = <issue-number>
```

### 해결 규칙

컨텍스트변수 `issue_number` 가 존재하면 그쪽을 사용.
없으면 `$ARGUMENTS` 의 제1인수를 `issue_number` 로 하여 사용.

## 전제지식의 읽기

이하의 문서를 Read 도구로 읽어들인 후 작업을 시작할 것.

1. **개발워크플로우**: `docs/dev/workflow_feature_development.md`
2. **테스트 규약**: `docs/dev/testing-convention.md`

## 전제 조건

- `/issue-start` 가 실행완료되어 있을 것
- Issue본문에 Worktree정보가 기재되어 있을 것

## 설계서 규칙

| 규칙 | 설명 |
|--------|------|
| **What & Constraint** | 입력/출력과 제약만 |
| **Minimal How** | 구현상세는 방침만. 의사코드는 OK |
| **Primary Sources** | 일차정보(공식문서 등)의 URL/경로를 반드시 기재 |
| **API사양** | 공식링크 참조(복사붙여넣기 금지) |
| **Test Strategy** | ID나열이 아니라 검증관점을 언어화 |

### 일차정보의 접근가능성 규칙

> **중요**: 리뷰어(agent)가 접근할 수 없는 일차정보는 사용할 수 없습니다.

| 정보의 종류 | 대응방법 |
|------------|----------|
| 공개URL | 그대로 기재(추천) |
| 로그인필수/유상 | 로컬에 다운로드하여 리포지토리에 배치, 또는 해당부분을 인용 |
| 사내한정/NDA | 사용불가. 공개판 문서를 찾거나, 해당부분의 스크린샷・인용으로 대체 |

설계 리뷰 시에 접근불가의 일차정보가 있으면, 리뷰가 중단됩니다.

## 공통 규칙

- [_shared/report-unrelated-issues.md](../_shared/report-unrelated-issues.md) — 작업중에 발견한 무관계한 문제의 보고 규칙

## 실행절차

### Step 1: Worktree 정보의 취득

[_shared/worktree-resolve.md](../_shared/worktree-resolve.md) 의 절차에 따라,
Worktree 의 절대 경로를 취득할 것. 이후의 스텝에서는 이 경로를 사용한다.

### Step 2: 설계서의 생성

1. **디렉토리생성**(절대 경로를 사용):
   ```bash
   mkdir -p [worktree-absolute-path]/draft/design
   ```

2. **파일이름 결정**:
   - `draft/design/issue-[number]-[short-name].md`
   - 예: `draft/design/issue-42-workflow.md`

3. **설계서 템플릿**:

```markdown
# [설계] 타이틀

Issue: #[issue-number]

## 개요

(무엇을 실현하는가, 1-2문으로)

## 배경・목적

(왜 이 변경이 필요한가)

## 인터페이스

### 입력

(인수, 파라미터, 설정 등)

### 출력

(반환값, 부작용, 생성물 등)

### 사용예

\`\`\`python
# 사용자 코드예
\`\`\`

## 제약・전제 조건

- (기술적 제약)
- (비즈니스 제약)
- (의존관계)

## 방침

(구현의 대략적인 방침. 의사코드 OK)

## 테스트전략

> **CRITICAL**: S/M/L 모두의 사이즈의 테스트방침을 정의할 것.
> AI 는 테스트를 생략하는 경향이 있기 때문에, 설계단계에서 명확히 정의하고, 생략의 여지를 배제한다.
> 상세는 [테스트 규약](../../../docs/dev/testing-convention.md) 참조.

### Small 테스트
- (검증대상을 열거: 단체로직, 밸리데이션, 매핑 등)

### Medium 테스트
- (검증대상을 열거: DB연계, 내부서비스 결합 등)

### Large 테스트
- (검증대상을 열거: 실API소통, E2E데이터 흐름 등)

### 스킵하는 사이즈(해당하는 경우만)
- 사이즈: (물리적으로 생성불가한 이유를 명기. 「실행시간」「환경의존」은 부당한 이유)

## 영향문서

이 변경으로 업데이트가 필요하게 될 가능성이 있는 문서를 열거한다.

| 문서 | 영향의 유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 있음/없음 | (새로운 기술선정이 있는 경우) |
| docs/ARCHITECTURE.md | 있음/없음 | (아키텍처변경이 있는 경우) |
| docs/dev/ | 있음/없음 | (워크플로우・개발절차변경이 있는 경우) |
| docs/cli-guides/ | 있음/없음 | (CLI사양변경이 있는 경우) |
| CLAUDE.md | 있음/없음 | (규약변경이 있는 경우) |

## 참조정보(Primary Sources)

| 정보원 | URL/경로 | 근거(인용/요약) |
|--------|----------|-------------------|
| (공식문서명) | (URL) | (설계판단의 뒷받침이 되는 인용 또는 요약) |

> **중요**: 설계판단의 근거가 되는 일차정보를 반드시 기재해주세요.
> - URL뿐만 아니라, **근거(인용/요약)** 도 기재필수
> - 리뷰 시에 일차정보의 기재가 없는 경우, 설계 리뷰는 중단됩니다
```

### Step 3: 커밋

```bash
cd [worktree-absolute-path] && git add draft/design/ && git commit -m "docs: add design for #[issue-number]"
```

### Step 4: Issue에 코멘트

설계완료를 Issue에 코멘트합니다.

```bash
gh issue comment [issue-number] --body-file - <<'EOF'
## 설계서생성완료

설계서를 생성했습니다.

### 산출물

- **파일**: `draft/design/issue-[number]-xxx.md`

### 설계의 요점

1. **What**: (무엇을 실현하는가)
2. **Why**: (왜 이 설계인가)
3. **Constraints**: (주요 제약)

### 테스트전략

- (주요한 검증포인트)

### 다음스텝

`/issue-review-design [issue-number]` 로 리뷰를 부탁합니다.
EOF
```

### Step 5: 완료보고

이하의 형식으로 보고해주세요:

```
## 설계서생성완료

| 항목 | 값 |
|------|-----|
| Issue | #[issue-number] |
| 설계서 | draft/design/issue-[number]-xxx.md |
| 커밋 | [commit-hash] |

### 다음스텝

`/issue-review-design [issue-number]` 로 리뷰를 실시해주세요.
```

## Verdict 출력

실행완료 후, 이하의 형식으로 verdict 를 출력할 것:

---VERDICT---
status: PASS
reason: |
  설계서생성・커밋완료
evidence: |
  draft/design/issue-XX-*.md 를 생성
suggestion: |
---END_VERDICT---

### status 의 선택기준

| status | 조건 |
|--------|------|
| PASS | 설계서생성・커밋완료 |
| ABORT | 설계불가능한 요건 |
