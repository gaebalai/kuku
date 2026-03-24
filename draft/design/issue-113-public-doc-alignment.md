# [설계] 공개용에 README 과 docs 의 전제를현행설계에揃える

Issue: #113

## 개요

공개전체크로判明한 README 과 docs 의 전제ズレ를 해소し, 初見유저이현행의 `kuku` 설계를誤解하지 않는다상태에한다.

## 배경·목적

現状, README 와 일부문서에는다음ズレ이 있다.

- skill 배치이 `.claude/skills/` 실체 / `.agents/skills/` symlink 라는현행방침에揃っ하지 않고 있다
- `resume` を中心에 한見せ方が, 現状の記事や상정운용와ずれ하고 있다
- README 에 최소도입예가 없く, 初見유저이最初の一歩で詰まりやすい

공개상태로이ズレ를 남기다와, 記事·README·docs 이 별々의 것을言っ하고 있다하도록見え, 도입판단やフィードバックの質を下げる.

## 인터페이스

### 입력

- Issue #113 의 요건
- 현행의 README
- `docs/dev/skill-authoring.md`
- `docs/dev/workflow-authoring.md`
- 공개予定の記事로 설명하고 있다도입·운용방침

### 출력

- README 의 기술업데이트
- `docs/dev/skill-authoring.md` 의 기술업데이트
- `docs/dev/workflow-authoring.md` 의 기술업데이트
- 初見유저용의 최소도입예

### 사용예

```bash
# README 에 기재한다상정의도입예
kuku run workflows/minimal-code-review.yaml 57
```

## 제약·전제 조건

- `kuku` 본체의구현변경는필수이 아니라, 今회의主대상는 README / docs の整合
- skill 배치에 대해는 `.claude/skills/` 를 실체, `.agents/skills/` 를 symlink 으로 한다설계방침를전제에한다
- 워크플로우의설명는 `resume` を主軸にし, 공개용 docs は現행운용에合わせて정리한다
- 記事로 설명하고 있다내용와모순하지 않는다것

## 방침

1. README 를 공개용의入口로서재정리한다
 - 최소도입예를載せる
 - skill 배치의전제를明示한다
 - 상세는 docs へ보내다
2. `skill-authoring.md` を現행설계에合わせる
 - skill 배치의설명를 `.claude/skills/` 실체 / `.agents/skills/` symlink 에 업데이트한다
 - "하네스는 skill 의 내용를읽지 않는다"と"VERDICT 계약에 의존한다"の関係を誤解없이설명한다
3. `workflow-authoring.md` 를 공개용에 정리한다
 - `resume` を主軸에 설명한다
 - 샘플 workflow を現행의 review / verify 운용에合わせる

## 테스트전략

> **CRITICAL**: S/M/L 모두의サイズ의 테스트방침를정의한다것.

今회의변경는문서中心때문, 코드테스트는원칙대상외으로 한다.また, 문서整合때문의회帰자동테스트는추가하지 않는다.README 와 docs の文言변경에 대해테스트를作り시작하다와, 保守대상만이増えて負債에 되어やすい때문에, 今회는수동확인를정으로 한다.

### Small 테스트
- README / docs 의 링크切れ이 없다것을확인한다
- 샘플 YAML / skill 명의 기술이서로일치하고 있다것을확인한다
- 문서의설명順や用語の使い方이 공개記事と大きく모순하지 않는다것을확인한다

### Medium 테스트
- 없음
 이유: 今회는문서변경이主이며, 파일I/O や내부서비스결합를伴う신규기능추가는 없다

### Large 테스트
- README 의 최소도입예를見た初見유저시점로, `kuku run` の最初の一歩が理解할 수 있다か를 수동확인한다

### 스킵한다サイズ(該当하는 경우만)
- サイズ: Medium
 이유: 대상이 docs の整合이며, Medium 에 해당한다결합관점이존재하지 않는다

## 영향문서

이변경에 의해업데이트이필요에된다가능性의 있다문서를列挙한다.

| 문서 | 영향의유무 | 이유 |
|-------------|-----------|------|
| docs/adr/ | 없음 | 설계방침의追認이며, 신규 ADR 는 불필요 |
| docs/ARCHITECTURE.md | 없음 | 본건는主에 공개용 docs の整合 |
| docs/dev/ | 있음 | `skill-authoring.md` 과 `workflow-authoring.md` 를 업데이트한다 |
| docs/cli-guides/ | 없음 | CLI 사양自体는 변경하지 않는다 |
| CLAUDE.md | 없음 | 개발규약自体는 변경하지 않는다 |
| README.md | 있음 | 공개용入口로서정비한다 |

## 참조정보(Primary Sources)

| 정보源 | URL/경로 | 근거(인용/要約) |
|--------|----------|-------------------|
| Issue #113 | https://github.com/apokamo/kuku/issues/113 | README / docs 의 전제ズレ와 대응범위이정리되어 있다 |
| README | `README.md` | 공개용入口だが, 최소도입예와현행 skill 배치전제이부족하고 있다 |
| Workflow 정의매뉴얼 | `docs/dev/workflow-authoring.md` | `resume` の現状설명와샘플의見直し대상 |
| 스킬 작성 매뉴얼 | `docs/dev/skill-authoring.md` | skill 배치설명이현행의 symlink 방침와ズレ하고 있다 |
