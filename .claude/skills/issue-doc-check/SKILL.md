---
description: PR 전 품질 게이트로서, 코드 변경에 따른 문서 영향을 망라 체크한다
name: issue-doc-check
---

# Issue Doc Check

코드 리뷰 Approve 후, PR 생성 전에 실행하는 품질 게이트.
코드 변경에 따른 문서의 영향을 망라적으로 체크하고, 필요에 따라 업데이트합니다.

## 언제 사용하는가

| 타이밍 | 이 스킬을 사용 |
|-----------|-----------------|
| `/issue-review-code` 또는 `/issue-verify-code` 에서 Approve 후 | ✅ 필수 |
| PR 생성 전의 최종 확인으로서 | ✅ 추천 |

**워크플로우 내의 위치**: implement → review-code → **doc-check** → pr → close

## 입력

### 하네스 경유(컨텍스트 변수)

**항상 주입되는 변수:**

| 변수 | 타입 | 설명 |
|------|-----|------|
| `issue_number` | int | GitHub Issue 번호 |
| `step_id` | str | 현재의 스텝 ID |

### 수동 실행(슬래시 커맨드)

```
$ARGUMENTS = <issue-number>
```

### 해결 규칙

컨텍스트 변수 `issue_number` 가 존재하면 그쪽을 사용.
없으면 `$ARGUMENTS` 의 제1인수를 `issue_number` 로서 사용.

## 전제 지식의 읽기

이하의 문서를 Read 도구로 읽어들인 후 작업을 시작할 것.

1. **개발 워크플로우**: `docs/dev/workflow_feature_development.md`

## 공통 규칙

- [_shared/report-unrelated-issues.md](../_shared/report-unrelated-issues.md) — 작업 중에 발견한 무관한 문제의 보고 규칙

## 실행절차

### Step 1: Worktree 정보의 취득

[_shared/worktree-resolve.md](../_shared/worktree-resolve.md) 의 절차에 따라,
Worktree 의 절대 경로를 취득할 것.

### Step 2: 영향 문서의 확인

1. **설계서의 「영향 문서」 섹션을 확인**:
   ```bash
   cat [worktree-absolute-path]/draft/design/issue-[number]-*.md
   ```

2. **변경 파일의 확인**:
   ```bash
   cd [worktree-absolute-path] && git diff main...HEAD --name-only
   ```

### Step 3: 체크리스트의 실행

| 확인 항목 | 판정 기준 |
|----------|---------|
| ADR 이 필요한가 | 새로운 기술 선정・아키텍처 변경의 유무 |
| ARCHITECTURE.md 의 업데이트 | 시스템 구성・컴포넌트 구조의 변경 |
| docs/dev/ 의 업데이트 | 워크플로우・개발 절차・테스트 규약의 변경 |
| docs/cli-guides/ 의 업데이트 | CLI 사양・커맨드의 변경 |
| CLAUDE.md 의 업데이트 | 새로운 커맨드・규약・금지 사항의 추가 |

### Step 4: 문서 업데이트의 실시

업데이트가 필요한 문서가 있으면 수정・커밋：

```bash
cd [worktree-absolute-path] && git add docs/ CLAUDE.md && git commit -m "docs: update documentation for #[issue-number]"
```

### Step 5: 스킵 조건

이하의 경우, 문서 업데이트는 불필요：

- **버그 수정**: 기존의 동작을 수정하는 것만으로 설계 변경 없음
- **경미한 리팩터**: 내부 구현의 개선으로 외부 사양・구조에 영향 없음
- **테스트 추가**: 테스트 코드만의 변경

### Step 6: Issue 에 코멘트

**업데이트를 행한 경우:**

```bash
gh issue comment [issue-number] --body "$(cat <<'EOF'
## 문서 체크 완료

체크리스트에 기반하여, 이하의 문서를 업데이트했습니다.

### 업데이트 내용

- `docs/xxx`: (업데이트 내용의 개요)

### 다음 스텝

`/issue-pr [issue-number]` 로 PR을 생성해주세요.
EOF
)"
```

**업데이트 불필요의 경우:**

```bash
gh issue comment [issue-number] --body "$(cat <<'EOF'
## 문서 체크 완료

체크리스트를 확인한 결과, 관련 문서의 업데이트는 불필요했습니다.

**이유**: (버그 수정만 / 내부 구현의 개선만 / 등)

### 다음 스텝

`/issue-pr [issue-number]` 로 PR을 생성해주세요.
EOF
)"
```

### Step 7: 완료 보고

```
## 문서 체크 완료

| 항목 | 값 |
|------|-----|
| Issue | #[issue-number] |
| 업데이트 | 있음 / 없음 |
| 대상 | (업데이트한 문서 / -) |

### 다음 스텝

`/issue-pr [issue-number]` 로 PR을 생성해주세요.
```

## Verdict 출력

실행 완료 후, 이하의 형식으로 verdict 를 출력할 것:

---VERDICT---
status: PASS
reason: |
  문서 체크 완료
evidence: |
  영향 문서의 확인・업데이트 완료
suggestion: |
---END_VERDICT---

### status 의 선택 기준

| status | 조건 |
|--------|------|
| PASS | 체크 완료 |
