# [설계] 기본값워크플로우를PR생성까지에축소

Issue: #93

## 개요

`feature-development.yaml` 의 자동실행범위를 PR 생성까지에축소し, `close` 스텝를삭제한다.

## 배경·목적

- PR 생성후의 머지판단는人間이 행う해야 할(리뷰확인, CI 결과확인, 머지타이밍)
- 자동머지·close 는 의도하지 않는다머지事故のリスク이 있다
- `issue-close` 는 worktree 삭제와 `git pull origin main` を伴い, Codex 실행시의 CWD / 세션계속挙動에 의존한다불안정요소이 있다([#70 kuku-run-verify 실행결과](https://github.com/apokamo/kuku/issues/70#issuecomment-4047582273) で観測)
- PR 생성를自然な"一時정지ポ인ト"으로 한다함으로써, 워크플로우의안전性を高める

## 인터페이스

### 입력

변경대상파일: `workflows/feature-development.yaml`

### 출력

워크플로우실행시의 동작변경:
- **Before**: `pr` → PASS → `close` → PASS → `end`
- **After**: `pr` → PASS → `end`

### 사용예

```bash
# 변경後も워크플로우실행명령어는같은
kuku run workflows/feature-development.yaml 99

# PR생성로자동실행이종료한다
# close 는 수동로 실행한다
/issue-close 99
```

## 제약·전제 조건

- `kuku validate` 이 변경後も通る것(`on` ターゲット의 참조선존재체크)
- 기존테스트이通る것
- `close` 스텝를 참조하고 있다他의 스텝이존재하지 않는다것(`pr` 의 `PASS` 만)

## 방침

YAML 변경 3 箇所 + 문서업데이트 1 箇所:

1. **`pr` 스텝의 `PASS` 전이선를 `close` → `end` 에 변경**
 ```yaml
 # Before
 on:
 PASS: close
 # After
 on:
 PASS: end
 ```

2. **`close` 스텝정의를삭제**(L114-L121 의 8 행)

3. **`description` 를 업데이트**
 ```yaml
 # Before
 description: |
 Issue 의 설계부터 PR クローズ까지의개발워크플로우.
 # After
 description: |
 Issue 의 설계부터 PR 생성까지의개발워크플로우.
 ```

4. **`docs/dev/development_workflow.md` 를 업데이트**
 - 플로우図(mermaid)부터 `close` 의 자동전이를삭제し, `pr` → `end` 에 변경
 - 페이즈개요テーブルの"6. 완료"행의설명를"수동실행(`/issue-close`)"에 변경
 - 상세플로우(ASCII)의 Phase 6 に"※워크플로우외.수동로 실행"の注記를 추가

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.

### Small 테스트
- 변경후의 YAML 를 `load_workflow_from_str()` 로 파싱し, `validate_workflow()` 이 에러없음로通る것을검증
- `pr` 스텝의 `on.PASS` 이 `"end"` 이다것을검증
- `close` 스텝이존재하지 않는다것을검증
- description 이 업데이트되어 있다것을검증

### Medium 테스트
- `kuku validate workflows/feature-development.yaml` CLI 명령어이정상종료한다것을검증(파일I/O + 밸리데이션결합)

### Large 테스트
- 구현완료후, `/kuku-run-verify workflows/feature-development.yaml <issue>` で実機검증를 수행하고, 워크플로우이 `pr` 스텝완료後에 정상종료한다것을확인한다
- 검증결과는 Issue 코멘트로서기록한다(#70 로 의 실제績: [kuku-run-verify 실행결과](https://github.com/apokamo/kuku/issues/70#issuecomment-4047582273))

## 영향문서

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 없음 | 새로운技術選定없음 |
| docs/ARCHITECTURE.md | 없음 | 아키텍처변경없음 |
| docs/dev/development_workflow.md | 있음 | 워크플로우플로우図·페이즈개요에 `close` 의 자동실행이含まれ하고 있다 |
| docs/cli-guides/ | 없음 | CLI 사양변경없음 |
| CLAUDE.md | 없음 | 규약변경없음 |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| 변경대상파일 | `workflows/feature-development.yaml` | `pr` 스텝의 `on.PASS: close` 과 `close` 스텝정의(L105-L121) |
| 워크플로우밸리데이션 | `kuku_harness/workflow.py` L231-235 | `on` ターゲット이 존재한다스텝ID or `"end"` 이다것을검증.`close` 삭제시에 `pr.on.PASS` 를 `end` 에 변경하지 않는다와밸리데이션에러 |
| #70 の観測 | [#70 kuku-run-verify 실행결과](https://github.com/apokamo/kuku/issues/70#issuecomment-4047582273) | close verdict 에 수동 `cd` + `git pull` 이 필요だった事実.SKILL 의 전제와실행환경의ずれ이 원인 |
| 개발워크플로우 | `docs/dev/development_workflow.md` | 플로우図에 `close` 이 자동스텝로서含まれ하고 있으며, 문서업데이트이필요 |
