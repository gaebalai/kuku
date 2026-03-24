# [설계] issue-implement 로 baseline failure 를 Issue 코멘트로 기록한다

Issue: #76

## 개요

`issue-implement` 스킬에 baseline check 스텝를추가し, 구현시작전의 테스트실패를 Issue 코멘트에기록한다구조를組み込む.

## 배경·목적

#73 의 workflow 실행로, implement 모두의 `pytest` 로 기지실패이検出된이, 이하이 AI 세션記憶内로 만관리된위해불안정에되었다:

- baseline failure 와 신규 regression の区별
- 도중재개시의"もとも와 의 실패"의 공유
- 정지이유의一貫한설명

Issue 코멘트를 source of truth 에 한다함으로써, agent 再기동·모델전환·人間介入をまたいでも전제이안정한다.

## 인터페이스

### 입력

기존의 `issue-implement` 와 동일(변경없음):

| 변수 | 타입 | 설명 |
|------|-----|------|
| `issue_number` | int | GitHub Issue 번호 |
| `step_id` | str | 현재의스텝 ID |

### 출력

`issue-implement` 의 실행中에 이하이추가된다:

1. **Issue 코멘트**: baseline failure 이 존재하는 경우, 所定포맷로投稿
2. **regression 판정기준**: 이후의테스트실행로 baseline failure 를 제외한差분로合否판정

### 사용예

#### baseline failure 있음 의 경우

```markdown
## Baseline Check 결과

### 실행환경

- **Commit**: abc1234
- **명령어**: `pytest`

### Baseline Failure 목록

| nodeid | kind | error_type | 개요 |
|--------|------|------------|------|
| tests/test_foo.py::test_bar | FAILED | AssertionError | expected 1, got 2 |
| tests/test_baz.py::test_qux | ERROR | ImportError | No module named 'xxx' |

### Regression 판정키

상기テーブル의 `(nodeid, kind, error_type)` の3튜플를비교키으로 한다.
이후의 pytest 실행로:
- 비교키이일치한다실패 → baseline failure(기지)로서제외
- 비교키이일치하지 않는다신규 FAILED/ERROR → regression

### 판정

- **계속**: 상기는변경전부터존재한다실패이며, 本 Issue 의 대상외
- **정지**: (該当하는 경우만기재)
```

#### baseline failure 없음 의 경우

Issue 코멘트는投稿하지 않는다(clean baseline は暗黙의 전제로서다루다).

## 제약·전제 조건

- 변경대상는스킬정의파일(`.claude/skills/*/SKILL.md`)만.Python 코드의변경는 없다
- baseline check 는 `pytest` 의 실행결과를파싱한다절차(agent 로의指示)이며, 자동화된プ로그ラム이 아니다
- Issue 코멘트의포맷는, 他스킬(review-code, verify-code)이참조할 수 있다よう一意に識별가능에한다(`## Baseline Check 결과` 헤더로識별)
- baseline failure 의 제외대상는 pytest 만.ruff / mypy 는 baseline failure 의 개념를적용하지 않는다(lint/타입에러는구현前에 수정해야 할위해)

## 방침

### 1. `issue-implement` SKILL.md 의 변경

#### 1.1 Step 2.5: Baseline Check 의 삽입

현재의 Step 2(설계書읽기)과 Step 3(Red Phase)사이에삽입한다.

```
Step 1: Worktree 정보의취득(기존)
Step 2: 설계書의 읽기(기존)
Step 2.5: Baseline Check(신규) ← 여기
Step 3: 테스트구현 (Red Phase)(기존, 번호繰り下げ없음)
...
```

절차:

1. 구현전에 `pytest` 를 실행한다
2. 전경로의 경우: baseline 는 clean.코멘트불필요.次스텝へ進む
3. FAILED / ERROR 이 있다경우:
 a. 각실패테스트의 `(nodeid, kind, error_type)` 를 기록한다
 b. Issue 코멘트에所定포맷로投稿한다(commit hash 를 포함하다)
 c. 계속가부를판단한다(정지기준에該当한다인가)
 d. 계속하는 경우: 이후의 regression 판정는 baseline failure 를 제외하여행う

**정지기준**:
- baseline failure が本 Issue 의 구현대상와동일모듈/기능에영향하는 경우
- 실패数が多く, regression の切り분けが困難な경우(目安: 10 건超)

#### 1.2 Step 4 (Green Phase) 의 pytest 合否조건의변경

현행의 Step 4 는 `pytest` 전경로를暗黙に期待하고 있다.baseline failure 이 있다경우의조건를明示한다.

**변경前** (현행):
```
테스트通過확인: pytest
```

**변경後**:
```
테스트通過확인: pytest 를 실행し, 이하의기준로合否판정한다.

- baseline failure 코멘트이 없다경우: 전테스트 PASSED を期待(종래どおり)
- baseline failure 코멘트이 있다경우:
 1. FAILED/ERROR 의 테스트를 baseline failure 목록와대조한다
 2. 비교키 (nodeid, kind, error_type) 이 baseline 와 일치 → 기지(제외)
 3. 비교키이불일치의신규 FAILED/ERROR → regression(수정이필요)
 4. baseline にあったが消えた(PASSED に変わった)→ 문제없음
```

#### 1.3 Step 7 (품질 체크) 의 조건변경

pre-commit 체크를 2 단계에분리한다.`CLAUDE.md` 의 `&&` 체인는 baseline failure 이 남다과 `pytest` 의 exit 비 0 로 체인전체이실패한다때문에, `pytest` 는 개별실행에한다.

**변경後**:
```
품질 체크(2 단계실행):

7a. ruff check / ruff format / mypy: && 체인로 실행.exit 0 필수(baseline failure 의 개념를적용하지 않는다)
7b. pytest: 개별에실행し, 이하의기준로合否판정한다
 - Baseline Check 코멘트없음: exit 0 필수(종래どおり)
 - Baseline Check 코멘트있음: Step 4 와 같은 regression 판정기준를적용
 - baseline failure 만残っ하고 있다 → OK(커밋가능)
 - 신규 FAILED/ERROR 이 있다 → NG(수정이필요)
```

> **중요**: `pytest` 를 `&&` 체인에含め없다이유는, baseline failure 이 존재하면 `pytest` 이 비 0 로 종료し, 체인전체이실패한다위해.개별실행한다함으로써 exit code に関わらず출력를확인し, baseline 대조에 의한合否판정이가능이 된다.

#### 1.4 Step 9 (Issue 코멘트) 의 테스트결과보고의변경

구현완료보고의테스트결과テーブル에 baseline failure 의 정보를 포함하다.

**변경後のテーブル예**:
```
| 항목 | 결과 |
|------|------|
| 테스트총수 | XX |
| passed | XX |
| failed | XX (うち baseline: YY, regression: 0) |
| errors | XX (うち baseline: YY, regression: 0) |
| skipped | XX |
```

### 2. `issue-review-code` SKILL.md 의 변경

#### 2.1 Step 1.5(독립테스트실행)의合否판정조건의변경

현행규칙:
> 상기이 exit 0 でなければ **Changes Requested**

**변경後**:
```
1. Issue 코멘트부터최신의 `## Baseline Check 결과` 를 검색한다
 - gh issue view [issue-number] --comments 로 취득완료의 코멘트부터探す
2. Lint / Format / 타입체크(exit 0 필수):
 - ruff check && ruff format --check && mypy 를 && 체인로 실행
3. 테스트실행(개별):
 - pytest 를 && 체인에含めず개별에실행한다
 - 이유: baseline failure 이 남다과 pytest 이 비 0 로 종료し, 체인전체이실패한다위해
4. 合否판정:
 - baseline failure 코멘트이 없다경우:
 - 전명령어이 exit 0 でなければ Changes Requested(종래どおり)
 - baseline failure 코멘트이 있다경우:
 - ruff check / ruff format / mypy: exit 0 필수(변경없음)
 - pytest: FAILED/ERROR 를 baseline 목록와대조한다
 - 비교키 (nodeid, kind, error_type) 이 baseline 와 완전일치 → 제외
 - 불일치의신규 FAILED/ERROR → Changes Requested
 - baseline failure 만残っ하고 있다 → 테스트合否는 OK 으로 한다
```

### 3. `issue-verify-code` SKILL.md 의 변경

Step 1(컨텍스트취득)에 baseline failure 코멘트의참조를추가한다.판정로직는 `issue-review-code` 와 동일.

```
Issue 코멘트부터최신의 `## Baseline Check 결과` 를 확인し,
테스트실행시의 regression 판정에사용한다.
```

### 4. `kuku-run-verify` SKILL.md 의 변경

본스킬는워크플로우검증용이며, 개별테스트의 baseline 관리는 scope 外.변경불필요.

### 5. Baseline 코멘트의선택규칙

Issue 에 `## Baseline Check 결과` 코멘트이복수존재하는 경우(再실행시 등):

- **최신의코멘트를정으로 한다**: Issue 코멘트는시계열順に並ぶ때문에, 最後に投稿된 `## Baseline Check 결과` 이 현재의 baseline
- **이유**: baseline は"구현시작時点"의 스냅샷이며, 再실행時に는 환경이変わっ하고 있다가능性이 있다.최신의 baseline check が最も정확한 상태를反映한다
- **코멘트에 commit hash 를 포함하다**: 어떤時点의 스냅샷かを明示し, 오래된 baseline 코멘트와의区별를容易에 한다

### 6. Regression 비교키의정의

| 키 | 설명 | 예 |
|------|------|-----|
| `nodeid` | pytest 의 test node ID | `tests/test_foo.py::test_bar` |
| `kind` | 실패種별 | `FAILED` or `ERROR` |
| `error_type` | 예외클래스명 | `AssertionError`, `ImportError` |

**비교규칙**:
- `(nodeid, kind, error_type)` の3튜플이 baseline 와 완전일치 → 기지 failure(제외)
- いずれか이 불일치 → regression(신규문제)

**에러메시지는비교대상에含め없다이유**:
- 메시지는실행환경やデータ에 의해微妙に変화しうる(경로, 타임스탬프등)
- 오검출이多く되어, agent 의 판단負荷が増える
- `error_type` の変화로 원인의質적変화는十분에検出가능

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.
> AI 는 테스트를생략한다傾向이 있다때문에, 설계단계로명확에정의し, 생략의여지를배제한다.
> 상세는 [테스트 규약](../../../docs/dev/testing-convention.md) 참조.

### Small 테스트

- baseline failure 코멘트의포맷검증:
 - 所定헤더 `## Baseline Check 결과` 이 포함된다것
 - 테스트실패목록テーブル이 올바른 Markdown 구문이다것
 - 판정섹션(계속/정지)이포함된다것
- 단, 스킬정의는 Markdown 템플릿이며, 실행시에 agent 이 해석한다.Markdown 템플릿自体의 구문체크는수동리뷰로 대체한다

### Medium 테스트

- 변경후의 SKILL.md 를 사용하여, 이하의시나리오로 `issue-implement` 를 수동실행し, 期待どおり의 Issue 코멘트이投稿된다것을확인:
 - **시나리오 1**: baseline failure 있음 → 코멘트投稿된다
 - **시나리오 2**: baseline clean → 코멘트投稿되지 않는다
- `issue-review-code` 이 baseline failure 코멘트를 참조し, 기지실패를 regression 부터제외할 수 있다것을확인

### Large 테스트

- `kuku run workflows/feature-development.yaml` 로 E2E 실행し, baseline failure 이 있다상태로 implement → review-code 의 플로우를通す
- baseline failure 이 Issue 코멘트에기록され, review-code が그것를 참조하여正しく판정할 수 있다것을확인

### 스킵한다サイズ(該当하는 경우만)

- **Small**: 물리적에생성불가.변경대상는 Python 코드이 아니라 Markdown 의 스킬정의파일만이다때문에, pytest 로 자동검증한다대상코드이존재하지 않는다.Markdown 템플릿의구문정확性는 설계 리뷰및수동확인로담보한다.

## 영향문서

이변경에 의해업데이트이필요에된다가능性의 있다문서를列挙한다.

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 없음 | 새로운技術選定는 없다 |
| docs/ARCHITECTURE.md | 없음 | 아키텍처변경는 없다 |
| docs/dev/development_workflow.md | 있음 | implement 페이즈의절차에 baseline check 이 추가된다때문에, 페이즈개요에言及이 필요 |
| docs/dev/testing-convention.md | 없음 | 테스트 규약自体는 변경하지 않는다 |
| docs/cli-guides/ | 없음 | CLI 사양변경는 없다 |
| CLAUDE.md | 없음 | 규약변경는 없다 |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| Issue #76 本文 | `gh issue view 76` | "AI 의 내부記憶만로는再실행·별 agent·별모델를またい로 전제이안정하지 않는다때문에, Issue 코멘트를 source of truth 에 한い" |
| Issue #73 (배경事예) | `gh issue view 73` | #76 の動機와 되었다事예.implement 모두의 baseline pytest 로 기지실패이観測され, 이후의판단이흔들림た |
| 현행 issue-implement SKILL.md | `.claude/skills/issue-implement/SKILL.md` | 현재의 Step 3 로 pytest 를 실행한다이, baseline failure 의 기록·판정규칙는未정의 |
| 현행 issue-review-code SKILL.md | `.claude/skills/issue-review-code/SKILL.md` | Step 1.5 로 독립테스트실행한다이, baseline failure 의 제외규칙는未정의 |
| 현행 issue-verify-code SKILL.md | `.claude/skills/issue-verify-code/SKILL.md` | 수정확인時에 테스트실행한다이, baseline failure 의 참조규칙는未정의 |
| 테스트 규약 | `docs/dev/testing-convention.md` | 테스트サイズ정의(S/M/L)와스킵판정기준 |
