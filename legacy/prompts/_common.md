# Common Prompt Elements

이파일는전스테이트로 공유된다공통요소를정의합니다.
각프롬프트파일의선두에자동적으로 삽입され합니다.

---

## VERDICT 출력형식

REVIEW스테이트(INIT포함하다)는, 必ず이하의형식로VERDICT를 출력해 주세요.

```markdown
## VERDICT
- Result: PASS | RETRY | BACK_DESIGN | ABORT
- Reason: <판정이유>
- Evidence: <판정근거>
- Suggestion: <다음アクション提案>(ABORT時는 필수)
```

### VERDICT 키ワード정의

| VERDICT | 의미 | 사용가능스테이트 |
|---------|------|-----------------|
| `PASS` | 성공·次스테이트へ進행 | 전REVIEW스테이트 |
| `RETRY` | 同스테이트再실행(軽微な문제) | INVESTIGATE_REVIEW, DETAIL_DESIGN_REVIEW, IMPLEMENT_REVIEW |
| `BACK_DESIGN` | 설계見直し이 필요 | IMPLEMENT_REVIEW 만 |
| `ABORT` | 속행不能·即座에 종료 | 전스테이트(緊急時) |

### 주의事項

1. **必ず `## VERDICT` 섹션를 포함하다것**
2. **Result 행는1행로, 키ワード만를기재**
3. **ABORT時는 Suggestion 에 구체적한 대처法를 기재**
4. **작업스테이트(INVESTIGATE, DETAIL_DESIGN, IMPLEMENT, PR_CREATE)는VERDICT를 출력하지 않는다**
5. **【중요】최종응답는必ず VERDICT 블록로종료한다것**
 - GitHub 로의投稿내용와동일의 VERDICT 를 stdout にも출력한다
 - VERDICT 블록의後에 추가의文章·サマリーを付け없다
 - "태스크완료보고"만의응답는금지

---

## Issue 업데이트규칙

Issue本文로의追記규칙：

1. **初회(Loop=1)**: 섹션를 Issue 本文의 말미에追記
2. **2회目이후(Loop>=2)**: 기존의該当섹션를삭제し, 새로운내용를말미에追記

예:

- 初회: Output 를 Issue 本文의 말미에追記
- 2회目이후: 기존섹션를삭제し, 새로운내용를말미에追記

명령어예: `gh issue edit <issue_number> --body "<updated_body>"`

---

## 証跡저장규칙

- 証跡파일는 artifacts_dir 에 저장
- 파일名는 내용이わかる命名에 한다
- 本文には証跡파일로의참조를 포함하다

예:
```markdown
### INVESTIGATE / 再現절차
1. pytest실행 (証跡: pytest_output.txt)
2. 에러로그확인 (証跡: error_log.txt)
```
