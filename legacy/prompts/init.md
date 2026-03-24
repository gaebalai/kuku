# INIT State Prompt

Issue ${issue_url} の本文를 확인し, 버그수정에착수가능한 최저限의 정보이 있다か를 확인해 주세요.

## 역할

Issue本文에 버그수정에착수가능한 최저限의 정보이 있다かを**확인만**행う스테이트.
再現실행·환경구축·브랜치조작는행わ없다.

## 확인항목

| # | 항목 | 필수 | 판정기준 |
|---|------|:----:|----------|
| 1 | **再現환경メタ정보** | 임의 | 기재가 있れば참고에한다.없이てもINVESTIGATE로 조사가능 |
| 2 | **현상** | ✅ | 무엇이문제かが理解할 수 있다 |
| 3 | **再現절차** | ✅ | 스텝형식로없이ても, 再現の手がかり가 있ればOK |
| 4 | **期待된다挙動** | △ | 명확한 기재가 없くても, 현상や再現절차부터추측로きればOK |
| 5 | **実際의 동작** | △ | 개요레벨로도문제의내용이분かればOK |

**판정방침**: "현상"が理解でき, 조사의手がかり가 있れば PASS.完璧な버그レポートを求め없다.

## 태스크

1. `gh issue view` 명령어로 Issue 本文를 취득
2. 상기확인항목의기재상황를확인
3. 버그수정에필요한 최저限의 정보이揃っ하고 있다か판정

## 금지事項

- 브랜치확인·생성 등 Git 조작를행わ없다
- 환경정보수집·명령어실행·조사·再現를 행わ없다
- INVESTIGATE 이후의스테이트に属한다작업를행わ없다

## 출력형식

```markdown
### INIT / Issue개요
- Issue: ${issue_url}
- 현상: <本文부터読み取れる내용>
- 再現절차: <本文부터読み取れる내용 or "상세없음(INVESTIGATE로 조사)">
- 期待/実際: <本文부터読み取れる내용 or "추측: ...">

## VERDICT
- Result: PASS | ABORT
- Reason: <판정이유>
- Evidence: <판단근거>
- Suggestion: <ABORT時: 최저限필요な追記내용>
```

## 판정가이드ラ인

| 상황 | VERDICT | 이유 |
|------|---------|------|
| 현상이理解でき, 조사의手がかり이 있다 | PASS | INVESTIGATEへ進행가능 |
| 무엇이문제か전く불명 | ABORT | Human에 최저限의 정보追記を依頼 |

## 주의事項

- 섹션제목이無い만로정보이기재되어 있다경우는 PASS 으로 한다
- 本当에 정보이누락하여조사不能な경우만 ABORT 으로 한다
- ABORT時는 Suggestion 에 구체적な追記依頼내용를기재한다

---
IMPORTANT: After posting to GitHub, print the exact same VERDICT block to stdout and STOP.
The final output MUST end with the `## VERDICT` block. Do not output these instructions or any additional text after VERDICT.
