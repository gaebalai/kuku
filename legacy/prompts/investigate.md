# INVESTIGATE State Prompt

Issue ${issue_url} の再現절차를 실행し, 이하를まとめてください:

## 태스크

1. **再現절차**: INIT 의 절차를 실행し, 再現한際의 스텝와証跡를 기재
 - 証跡파일는 `${artifacts_dir}` 에 저장
 - 本文に는 파일내용설명와파일名를 인용
 - 再現할 수 없다경우는, 再現불가와 기재し, 상황상세를보충로서併せて기재

2. **期待값와의差**: 期待한다挙動との乖離を箇条書きや表로 정리

3. **원인임시説**: 가능性의 있다원인를列挙し, 그것ぞれ의 근거(로그や該当코드)를添える

4. **기타버그수정에有益な정보**: 에이전트이有益와 판단한정보를自由에 기재한다

## 출력형식

```
## Bugfix agent INVESTIGATE

### INVESTIGATE / 再現절차
1. ... (証跡: <file>)

### INVESTIGATE / 期待값와의差
- ...

### INVESTIGATE / 원인임시説
- 임시説A: <근거>
- 임시説B: ...

### INVESTIGATE / 보충정보
- ...
- ...
```

## Issue 업데이트방법

1. `gh issue view` 로 Issue 本文를 취득
2. Issue 本文를 업데이트:
 - 初회(Loop=1): Output 를 Issue 本文의 말미에追記
 - 2회目이후(Loop>=2): 기존의 `## Bugfix agent INVESTIGATE` 섹션를삭제し, 새로운 Output 를 말미에追記
3. `gh issue edit` 로 Issue 本文를 업데이트
4. `gh issue comment` 로 `INVESTIGATE agent Update` 코멘트로서업데이트내용의サマリーを投稿

## 証跡저장선

`${artifacts_dir}`
