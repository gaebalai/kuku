# [설계] 콘솔출력에타임스탬프를추가한다

Issue: #101

## 개요

`kuku run` 의 콘솔출력(`stream_and_log` 의 `print` 호출)에타임스탬프를추가し, 각이벤트의발생時刻を把握할 수 있다하도록한다.

## 배경·목적

kuku 의 콘솔출력는 `stream-json` 의 이벤트단위로표시된다때문에, リアルタイム感が薄い(#100 참조).타임스탬프를 부여한다함으로써, 각스텝의所要時間や진척의時間感覚を低코스트로補える.

## 인터페이스

### 입력

변경없음.기존의 `stream_and_log` 함수의シグネチャ는 유지한다.

### 출력

터미널출력(`print`)의 포맷이변경된다.

**변경前:**

```
[step_id] 텍스트
```

**변경後:**

```
[2026-03-13T15:04:23] [step_id] 텍스트
```

### 사용예

```python
# 변경는내부구현만.유저코드로의영향없음.
# kuku run workflow.yaml 42 실행시의터미널출력이바뀌다.
```

## 제약·전제 조건

- 타임스탬프포맷: `YYYY-MM-DDTHH:MM:SS`(ISO 8601, 로컬タイム, タイムゾーン表記없음)
- 타임스탬프과 step_id 는 별ブラケット로 분리(파싱容易性·기존출력와의호환性)
- `CLIResult.full_output` に는 타임스탬프를含め없다(下流의 파서ー, 特에 verdict 파서ー에 영향를与え없기 때문에)
- `console.log` 파일에도타임스탬프를含め없다(Issue 의 대상는 `print` 호출만)
- `stdout.log` は生의 JSONL 를 그まま기록한다위해변경하지 않는다

## 방침

`stream_and_log` 함수내의 2 箇所의 `print` 호출(L110, L123)에타임스탬프를추가한다.

```python
from datetime import datetime

# 타임스탬프생성(헬퍼함수)
def _now_stamp() -> str:
 """현재時刻를 ISO 8601 형식(초정밀도, タイムゾーン없음)로반환하다."""
 return datetime.now().isoformat(timespec="seconds")

# print 호출의변경(2箇所)
# 변경前: print(f"[{step_id}] {text}")
# 변경後: print(f"[{_now_stamp()}] [{step_id}] {text}")
```

변경대상:
- `kuku_harness/cli.py` 의 `_now_stamp` 헬퍼추가(모듈프라이빗)
- `stream_and_log` 内의 `print` 2 箇所의 포맷변경

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.

### Small 테스트

- `_now_stamp()` 의 반환값포맷검증: ISO 8601 형식(`YYYY-MM-DDTHH:MM:SS`)이다것
- `_now_stamp()` 이 `datetime.now()` 를 사용하고 있다것(`freezegun` 또는 `unittest.mock.patch` 로 고정時刻를 주입し, 期待값와일치한다것을검증)

### Medium 테스트

- `stream_and_log` 의 `verbose=True` 時, `print` 출력에타임스탬프이포함된다것(`capsys` 로 캡처し, `[YYYY-MM-DDTHH:MM:SS]` 패턴를정규表現로 검증)
- `stream_and_log` 의 `verbose=True` 時, 비JSON행의 `print` 출력에도타임스탬프이포함된다것
- `CLIResult.full_output` 에 타임스탬프이含まれ**없다**것(기존테스트의암묵적보증だが, 명시적에검증)
- `console.log` 에 타임스탬프이含まれ**없다**것

### Large 테스트

- `kuku run` を実서브프로세스로서실행し, stdout 에 `[YYYY-MM-DDTHH:MM:SS] [step_id]` 형식의타임스탬프이출력된다것을검증
- 방식: `tests/test_cli_main.py::TestCLILarge` 와 마찬가지의패턴로, 유효한 JSONL 를 출력한다목 CLI 스크립트를 `tmp_path` 에 생성し PATH 선두에배치한다.`kuku run` 를 `subprocess.run` 로 실행し, stdout 를 정규表現로 검증한다
- `--quiet` 플래그사용時に는 타임스탬프이출력되지 않는다것도검증

## 영향문서

이변경에 의해업데이트이필요에된다가능性의 있다문서를列挙한다.

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 없음 | 새로운技術選定없음 |
| docs/ARCHITECTURE.md | 없음 | 아키텍처변경없음 |
| docs/dev/ | 없음 | 워크플로우·개발절차변경없음 |
| docs/cli-guides/ | 없음 | CLI 의 인수·서브명령어사양에변경없음(출력포맷만) |
| CLAUDE.md | 없음 | 규약변경없음 |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| Python datetime.isoformat | https://docs.python.org/3/library/datetime.html#datetime.datetime.isoformat | `timespec="seconds"` 로 `YYYY-MM-DDTHH:MM:SS` 형식를得る.Issue 요건의"ISO 8601, タイムゾーン表記없음"에 합치 |
| 대상코드 | `kuku_harness/cli.py` L78-140 (`stream_and_log`) | `print(f"[{step_id}] {text}")` 이 L110, L123 의 2 箇所에 존재.이것들이 타임스탬프추가의대상 |
| Issue #101 | GitHub Issue #101 | 포맷사양: `[YYYY-MM-DDTHH:MM:SS] [step_id] 텍스트` |
| 기존 Large 테스트패턴 | `tests/test_cli_main.py` L459-527 (`TestCLILarge`) | `kuku run` 를 `subprocess.run` 로 실행し, mock workflow + 제어된 PATH 로 E2E 검증한다수법.今회의 Large 테스트로도동패턴를踏襲し, JSONL 를 출력한다 mock CLI 스크립트를 PATH 에 배치한다 |
