# [설계] test_legacy_cleanup.py 를 삭제

Issue: #97

## 개요

V5/V6→V7移행時에 생성된일시적한 회帰테스트파일 `tests/test_legacy_cleanup.py` 를 삭제한다.

## 배경·목적

`tests/test_legacy_cleanup.py` 는 Issue #59 로 V5/V6 코드를 `legacy/` へ이동한際에 생성된회帰테스트이다.移행는완료하고 있으며, 테스트의 역할는終え하고 있다.

더욱, `TestPackageInstallation.test_bugfix_agent_not_importable_after_install` 이 subprocess 로 `pip install -e` 를 실행한다때문에, worktree 환경로 shared `.venv` 의 editable install 경로를덮어쓰기한다副作用가 있り, #87 의 직접원인와なっ하고 있다.

삭제이유를まとめると:

1. **역할의완료**: 移행검증는완료완료.파일/디렉토리의존재확인나 문서내용의검증는, 리포지토리의상태이変われば自然に壊れる성질의테스트이며, 계속적인 価값이 없다
2. **副作用의 제거**: Large 테스트이 shared `.venv` を破壊한다문제(#87)의 근본원인를제거

## 인터페이스

### 입력

없음(파일삭제만)

### 출력

- `tests/test_legacy_cleanup.py` 이 존재し없이된다
- 테스트スイート부터 22 테스트케이스(Small 17 + Medium 3 + Large 2)이제거된다

### 사용예

```bash
# 삭제후의 확인
pytest # test_legacy_cleanup.py 의 테스트이含まれ없다것
```

## 제약·전제 조건

- 他의 테스트파일부터 `test_legacy_cleanup.py` 로의참조·의존이 없다것(확인완료: `grep` 로 참조없음)
- `conftest.py` や픽스처에영향이 없다것(이파일는독립하고 있으며외부픽스처를정의하지 않고 있다)
- 삭제대상의테스트이검증하여いた내용(legacy 배치, pyproject.toml, 문서내용)는, 리포지토리의상태그도의이一次정보이며, 테스트로보호한다필요이 없다

## 방침

1. `tests/test_legacy_cleanup.py` 를 `git rm` 로 삭제
2. `ruff check`, `ruff format`, `mypy`, `pytest` 로 품질 체크
3. 커밋

단순한 파일삭제이며, 코드 수정나 리팩터링는불필요.

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.
> AI 는 테스트를생략한다傾向이 있다때문에, 설계단계로명확에정의し, 생략의여지를배제한다.
> 상세는 [테스트 규약](../../../docs/dev/testing-convention.md) 참조.

### 스킵한다サイズ

- **Small**: 물리적에생성불가.이변경는파일삭제만이며, 신규로직·밸리데이션·매핑등의테스트대상코드이존재하지 않는다.
- **Medium**: 물리적에생성불가.DB연계·내부서비스결합등의검증대상이존재하지 않는다.
- **Large**: 물리적에생성불가.実API疎通·E2E데이터 흐름등의검증대상이존재하지 않는다.

### 검증방법

테스트코드의신규생성는불필요だが, 이하로正しく삭제된것을검증한다:

- `pytest` 의 전테스트경로(기존테스트에영향이 없다것)
- `pytest --collect-only -q` 로 테스트목록부터 `test_legacy_cleanup` が消え하고 있다것
- `ruff check` / `mypy` 이 경로한다것(他파일에서의참조이 없다것)

## 영향문서

이변경에 의해업데이트이필요에된다가능性의 있다문서를列挙한다.

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 없음 | 技術選定의 변경없음 |
| docs/ARCHITECTURE.md | 없음 | 아키텍처변경없음 |
| docs/dev/ | 없음 | 워크플로우·개발절차의변경없음 |
| docs/cli-guides/ | 없음 | CLI사양변경없음 |
| CLAUDE.md | 없음 | 규약변경없음 |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| 삭제대상파일 | `tests/test_legacy_cleanup.py` | 22테스트전건의내용를확인.모두 V5/V6→V7 移행검증용이며, 移행완료後는 불필요.모두 docstring: `"""Tests for #59: V5/V6 legacy file cleanup and V7 base clarification."""` |
| Issue #87 (副作用보고) | https://github.com/apokamo/kuku/issues/87 | `TestPackageInstallation` 이 shared `.venv` 의 editable install 경로를덮어쓰기한다副作用이 보고되어 있다 |
| Issue #59 (移행元Issue) | https://github.com/apokamo/kuku/issues/59 | 이테스트파일이생성된移행작업의원 Issue.移행완료에 의해역할종료 |
