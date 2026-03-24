# [설계] dao validate 서브명령어의추가

Issue: #65

## 개요

워크플로우 YAML 의 스키마밸리데이션를 CLI 부터실행할 수 있다 `dao validate <file>...` 서브명령어를추가한다.

## 배경·목적

워크플로우 YAML 를 `dao run` 로 실행한다前に, 정의의정당性를 사전 검증한다수단이 없다.`load_workflow()` + `validate_workflow()` は既에 구현완료だが, CLI 에서의직접호출수단이존재하지 않는다.워크플로우생성者が素早くフィードバックを得られる하도록한다때문에, 薄い CLI 래퍼로서 `dao validate` 를 제공한다.

## 인터페이스

### 입력

| 인수 | 타입 | 필수 | 설명 |
|------|-----|------|------|
| `<file>...` | 1つ이상의파일경로 | Yes | 밸리데이션대상의워크플로우 YAML |

### 출력

**stdout** — 각파일의검증결과:

```
✓ workflows/feature-development.yaml
```

**stderr** — 에러상세:

```
✗ bad.yaml
 - Step 'review' transitions to unknown step 'fix' on RETRY
 - Cycle 'review-cycle' entry step 'review' not found
```

**복수파일시의サマリー** (1つ이상실패시, stderr):

```
Validation failed: 1 of 2 files had errors.
```

### 종료코드

| 코드 | 의미 |
|--------|------|
| 0 | 전파일밸리데이션성공 |
| 1 | 1つ이상의밸리데이션에러 |
| 2 | argparse 에러(인수부족 등, argparse 기본값동작) |

### 사용예

```python
# 테스트에서의호출(cli_main.main() 를 직접사용)
from dao_harness.cli_main import main

exit_code = main(["validate", "workflows/feature-development.yaml"])
assert exit_code == 0

exit_code = main(["validate", "bad.yaml"])
assert exit_code == 1

exit_code = main(["validate", "good.yaml", "bad.yaml"])
assert exit_code == 1
```

## 제약·전제 조건

- **신규의존없음**: argparse 만사용(기존의 `cli_main.py` 와 마찬가지)
- **기존함수의재이용**: `load_workflow()` 과 `validate_workflow()` 를 그まま사용
- **기존의 `cli_main.py` 로의추가**: 신파일는作らず, `cli_main.py` 의 `create_parser()` 에 서브명령어를추가한다形
- **カラー출력는대상外**: Issue 스코프외(의존추가이필요)
- **JSON 출력모드는대상外**: Issue 스코프외
- **종료코드체계**: 기존의 `EXIT_OK = 0`, `EXIT_DEFINITION_ERROR = 2` を再이용.밸리데이션실패용에 `EXIT_VALIDATION_ERROR = 1` 를 추가

## 방침

### 1. `cli_main.py` 로의 `validate` 서브명령어등록

`create_parser()` 内의 `subparsers` 에 `validate` 를 추가.`nargs="+"` で1つ이상의파일경로를받다.

### 2. `cmd_validate()` 의 구현

```python
# 疑似코드
def cmd_validate(args) -> int:
 failed = 0
 total = len(args.files)
 for path in args.files:
 if not path.exists():
 print_error(path, "File not found")
 failed += 1
 continue
 try:
 wf = load_workflow(path)
 validate_workflow(wf)
 print_success(path)
 except WorkflowValidationError as e:
 print_error(path, e.errors)
 failed += 1
 if failed > 0 and total > 1:
 print_summary(failed, total)
 return EXIT_VALIDATION_ERROR
 return EXIT_OK if failed == 0 else EXIT_VALIDATION_ERROR
```

### 3. `main()` 로의ディス패치추가

기존의 `if args.command == "run"` 에 `elif args.command == "validate"` 를 추가.

### 4. 출력헬퍼

`_print_success(path)` 과 `_print_errors(path, errors)` 를 `cli_main.py` 内에 정의.stdout/stderr の使い분け는 Issue 사양을 따른다(성공→stdout, 실패→stderr).

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.

### Small 테스트

`cmd_validate()` 의 로직를직접테스트한다.`capsys` 로 캡처.

- **유효한 YAML → exit 0 + `✓` 메시지이 stdout 에 출력된다**
- **스키마위반 YAML → exit 1 + 에러메시지이 stderr 에 출력된다**
- **YAML 구문에러 → exit 1 + 에러메시지이 stderr 에 출력된다**
- **존재하지 않는다파일 → exit 1 + 에러메시지이 stderr 에 출력된다**
- **복수파일전성공 → exit 0**
- **복수파일일부실패 → exit 1 + サマリー이 stderr 에 출력된다**
- **인수없음 → argparse 이 exit 2 를 반환하다**(argparse 의 기본값동작확인)

### Medium 테스트

実際의 파일시스템上의 워크플로우 YAML を使った결합테스트.`tmp_path` fixture 를 사용.

- **実파일의 읽기·파싱·밸리데이션의파이프라인검증**: `tmp_path` 에 YAML 를 쓰기, `cmd_validate()` 에 경로를渡하여 end-to-end 의 동작확인
- **복수파일혼재시의 파일 I/O 挙動**: 유효/무효파일를혼재させ, 전파일이처리된다것(도중로打ち切られ없다것)를확인
- **퍼미션에러시의挙動**: 읽기권한의없다파일를渡한 경우의에러ハンドリング

### Large 테스트

実際에 설치된 `dao` 명령어를 `subprocess` 経由로 실행한다 E2E 테스트.

- **`dao validate <valid.yaml>` 의 실행 → exit 0 + stdout 에 `✓` 출력**
- **`dao validate <invalid.yaml>` 의 실행 → exit 1 + stderr 에 에러출력**
- **`dao validate` 인수없음 → exit 2**
- **`dao validate <valid.yaml> <invalid.yaml>` 의 실행 → exit 1 + サマリー출력**

## 영향문서

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 없음 | 새로운技術選定는 없다 |
| docs/ARCHITECTURE.md | 없음 | 아키텍처변경는 없다 |
| docs/dev/ | 없음 | 개발워크플로우自体로의변경는 없다 |
| docs/cli-guides/ | 있음 | `dao validate` の使い方を追記한다필요이 있다 |
| CLAUDE.md | 있음 | Essential Commands 섹션에 `dao validate` を追記 |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| 기존 `load_workflow()` | `dao_harness/workflow.py:14-30` | YAML 파싱 + `_parse_workflow()` 로 Workflow 오브젝트를 반환하다.`yaml.YAMLError` 는 `WorkflowValidationError` にラップ완료 |
| 기존 `validate_workflow()` | `dao_harness/workflow.py:168-301` | Workflow 오브젝트의 정적검증.에러는 `WorkflowValidationError(errors: list[str])` で一括 raise |
| `WorkflowValidationError` | `dao_harness/errors.py:9-19` | `errors: list[str]` 속성로복수에러를보유.`str` 인수의 경우는요소1의리스트로 변환 |
| 기존 `cli_main.py` | `dao_harness/cli_main.py` | `create_parser()` + 서브명령어패턴이確立완료.`_register_run()` と同패턴로 `_register_validate()` 를 추가가능 |
| argparse `nargs="+"` | https://docs.python.org/3/library/argparse.html#nargs | 1つ이상의인수를받다.0개의 경우 argparse 이 에러(exit 2)를出す |
| Issue #65 사양 | GitHub Issue #65 本文 | CLI 출력포맷, 종료코드, 스코프정의 |
