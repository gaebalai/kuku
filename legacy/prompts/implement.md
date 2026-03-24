# IMPLEMENT State Prompt

Issue ${issue_url} 의 DETAIL_DESIGN 에 따라구현해 주세요.

> **CRITICAL: 테스트생략금지**
> Size M(연계/이상系)및 Size L(통합/E2E)의 테스트를생략해서는 안 된다.
> "時間이 없다""難しい" 등의이유로테스트를스킵한다것은금지.
> 테스트없음구현는 IMPLEMENT_REVIEW で必ず RETRY 된다.

## 태스크

1. **브랜치생성**: 전용브랜치를 생성し, 브랜치명과 HEAD 커밋 ID 를 기록

2. **Red 페이즈**: DETAIL_DESIGN 의 테스트케이스를 모두先에 구현し, 실패한다것을확인

3. **Green 페이즈**: 테스트이 PASS 한다よう구현를 수행한다

4. **리팩터링**: 코드의정리·重複배제(테스트는引き続き PASS 이다것)

5. **품질 체크**: 이하를모두경로한다것
 ```
 ruff check bugfix_agent/ tests/ && ruff format bugfix_agent/ tests/ && mypy bugfix_agent/ && pytest
 ```

6. **証跡저장**: 테스트証跡를 `${artifacts_dir}` 에 저장

7. **보충기재**: 残작업, 리뷰관점, リスク를 기재

## 출력형식

```
## Bugfix agent IMPLEMENT

### IMPLEMENT / 작업브랜치
- Branch: <name>
- Commit: <sha>

### IMPLEMENT / 테스트결과
| Test | Tag(E/A) | Size(S/M/L) | Result | Evidence |
|------|----------|-------------|--------|----------|

### IMPLEMENT / 품질 체크
- ruff check: PASS/FAIL
- ruff format: PASS/FAIL
- mypy: PASS/FAIL
- pytest: PASS/FAIL (<passed>/<total> tests)

### IMPLEMENT / 보충
- 残작업:
- 주의点:
- Artifacts: <files>
```

## Issue 업데이트방법

1. `gh issue view` 로 Issue 本文를 취득
2. Issue 本文를 업데이트:
 - 初회(Loop=1): Output 를 Issue 本文의 말미에追記
 - 2회目이후(Loop>=2): 기존의 `## Bugfix agent IMPLEMENT` 섹션를삭제し, 새로운 Output 를 말미에追記
3. `gh issue edit` 로 Issue 本文를 업데이트
4. `gh issue comment` 로 `IMPLEMENT agent Update` 코멘트로서업데이트내용의サマリーを投稿

## Issue 번호

${issue_number}

## 証跡저장선

`${artifacts_dir}`
