# [설계] ライセンス選定과 SPDX 移행

Issue: #105

## 개요

Apache License 2.0 를 정식채용し, `pyproject.toml` 의 `project.license` 를 PEP 639 準拠의 SPDX 형식에移행한다.合わせて `LICENSE` 파일의신규추가과 `README.md` のライセンス表記를 업데이트한다.

## 배경·목적

- オープン소스화에 용たライセンス정식選定が未了
- 現状 `license = {text = "MIT"}` のテーブル형식는 PEP 639 로 비추천(setuptools 이 2027-02-18 에 경고기한를설정)
- 리포지토리에 `LICENSE` 파일이존재せず, 배포物にライセンス문서이含まれ없다
- Apache 2.0 は特許条項(Patent Grant / Patent Retaliation)에 의한コントリビューター보호를제공し, kuku 의 도구계층로서의성질와합치한다

## 인터페이스

### 입력

변경대상파일:

| 파일 | 現状 | 변경내용 |
|---------|------|---------|
| `pyproject.toml` | `license = {text = "MIT"}` + MIT classifier + `setuptools>=68.0` | SPDX 문자열 + `license-files` 추가 + classifier 삭제 + `setuptools>=77.0.0` に引き上げ |
| `LICENSE` | 존재하지 않는다 | Apache License 2.0 전文를 신규생성 |
| `README.md` | `## License` 섹션에 `MIT` | `Apache-2.0` 에 업데이트 |

### 출력

변경후의 상태:

```toml
# pyproject.toml
[project]
license = "Apache-2.0"
license-files = ["LICENSE"]
# classifiers 부터 "License :: OSI Approved :: MIT License" 를 삭제(대체추가없음)

[build-system]
requires = ["setuptools>=77.0.0", "wheel"]
```

```
# LICENSE(리포지토리루트)
Apache License Version 2.0 전문(https://www.apache.org/licenses/LICENSE-2.0.txt 부터취득)
```

```markdown
# README.md
## License

Apache-2.0
```

## 제약·전제 조건

- PEP 639 / Core Metadata 2.4 に準拠한다것
- `License ::` classifier 는 PEP 639 로 deprecated 때문삭제한다
- `LICENSE` 파일는 Apache Software Foundation 의 공식텍스트를그まま사용한다(改変불가)
- setuptools >= 77.0.0 이 필요(PEP 639 지원는 v77.0.0 로 도입).현재의 `build-system.requires = ["setuptools>=68.0"]` 를 `["setuptools>=77.0.0"]` に引き上げる
- `license-files` を明示지정し, 배포물로의 LICENSE 同梱를 보증한다

## 방침

코드변경는발생하지 않는다.프로젝트메타데이터와문서파일만의변경.

1. **LICENSE 파일생성**: Apache 공식サイト부터취득한전文를 배치
2. **pyproject.toml 업데이트**:
 - `license = {text = "MIT"}` → `license = "Apache-2.0"`
 - `license-files = ["LICENSE"]` 를 추가
 - `classifiers` 부터 `"License :: OSI Approved :: MIT License"` 를 삭제
 - `build-system.requires` 의 `setuptools>=68.0` → `setuptools>=77.0.0` に引き上げ
3. **README.md 업데이트**: License 섹션를 `Apache-2.0` 에 변경

변경順序는 상기의通り.LICENSE 파일이先에 존재한다함으로써, `license-files` 의 참조先이 확정한다.

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.
> AI 는 테스트를생략한다傾向이 있다때문에, 설계단계로명확에정의し, 생략의여지를배제한다.
> 상세는 [테스트 규약](../../../docs/dev/testing-convention.md) 참조.

### 스킵한다サイズ

- **Small / Medium / Large 모두스킵**: 이변경는프로젝트메타데이터와문서파일만의수정이며, 테스트대상와된다코드로직이물리적에존재하지 않는다.pyproject.toml 의 필드값와 LICENSE 파일의존재는, 자동테스트이 아니라 PR 리뷰와 이하의수동확인로검증한다.

### 수동확인절차

구현완료후, 이하를수동로확인한다:

```bash
# 1. pip install 이 경고없음에 성공한다것
pip install -e .

# 2. 메타데이터의확인
python -c "
from importlib.metadata import metadata
m = metadata('kuku')
print(m['License-Expression']) # Apache-2.0
"

# 3. LICENSE 파일의존재와내용
head -3 LICENSE
# Apache License / Version 2.0 이 포함된다것
```

## 영향문서

이변경에 의해업데이트이필요에된다가능性의 있다문서를列挙한다.

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 없음 | 技術選定이 아니라ライセンス選定.Issue 本文에 결정근거이아카이브된다 |
| docs/ARCHITECTURE.md | 없음 | 아키텍처변경없음 |
| docs/dev/ | 없음 | 개발절차·워크플로우변경없음 |
| docs/cli-guides/ | 없음 | CLI 사양변경없음 |
| CLAUDE.md | 없음 | 규약변경없음 |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| PEP 639 | https://peps.python.org/pep-0639/ | `license` 필드는 SPDX 문자열를 사용.`License ::` classifier 는 deprecated.`license-files` でライセンス문서의배포物同梱を明示지정 |
| Apache License 2.0 전문 | https://www.apache.org/licenses/LICENSE-2.0.txt | LICENSE 파일에배치한다정식텍스트 |
| SPDX License List | https://spdx.org/licenses/ | `Apache-2.0` 이 정식한 SPDX 識별子이다것의 근거 |
| setuptools 문서 | https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html | `project.license` 의 SPDX 형식지원와移행ガイダンス |
| setuptools v77.0.0 릴리스노트 | https://setuptools.pypa.io/en/latest/history.html | PEP 639 초기지원도입.SPDX license expression, `license-files`, `licenses/` 서브폴더저장, Core Metadata 2.4 대응 |

> **중요**: 설계판단의근거와된다一次정보를必ず기재해 주세요.
> - URL만로없이, **근거(인용/要約)** も기재필수
> - 리뷰時に一次정보의기재이 없다경우, 설계 리뷰는중단され합니다
