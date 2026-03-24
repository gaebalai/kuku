# QA State Prompt

Issue ${issue_url} 의 구현결과에 대해 QA 를 실시해 주세요.

## 태스크

1. **소스리뷰**: 변경전체의소스리뷰(diff + 周辺코드)를실시
 - 리뷰관점와결과를기록

2. **추가테스트실행**: IMPLEMENT 의 테스트리스트이외의추가 QA 테스트시나리오를計画·실행
 - 각테스트에 `Q` (QA) 의 태그를 부여

3. **証跡저장**: 테스트証跡를 `${artifacts_dir}` 에 저장

4. **보충기재**: 残작업, 리뷰관점, リスク를 기재

## 출력형식

```
## Bugfix agent QA

### QA / 소스리뷰
- 관점: ...
- 결과: ...

### QA / 추가테스트결과
| Test | Tag(Q) | Result | Evidence |
|------|--------|--------|----------|

### QA / 보충
- 残작업:
- 주의点:
- Artifacts: <files>
```

## Issue 업데이트방법

1. `gh issue view` 로 Issue 本文를 취득
2. Issue 本文를 업데이트:
 - 初회(Loop=1): Output 를 Issue 本文의 말미에追記
 - 2회目이후(Loop>=2): 기존의 `## Bugfix agent QA` 섹션를삭제し, 새로운 Output 를 말미에追記
3. `gh issue edit` 로 Issue 本文를 업데이트
4. `gh issue comment` 로 `QA agent Update` 코멘트로서업데이트내용의サマリーを投稿

## Issue 번호

${issue_number}

## 証跡저장선

`${artifacts_dir}`