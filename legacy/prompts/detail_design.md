# DETAIL_DESIGN State Prompt

Issue ${issue_url} 의 INVESTIGATE 결과에 기반하여, 상세설계를 생성해 주세요.

## 태스크

1. **변경計画**: 대상파일·함수와計画한다변경내용를상세에기재
 - 구현에十분한 상세度로 기술
 - 필요에応じて코드스니펫를 포함하다

2. **구현절차**: 스텝バイ스텝의구현절차를기재

3. **테스트케이스목록**: 테스트케이스를列挙(목적, 입력, 期待결과, サイズ를 포함)
 - Size S: 단일함수·境界값·정상系 등単体테스트
 - Size M: 복수컴포넌트연계·이상系·エッジ케이스
 - Size L: エンドツーエンド·통합테스트·시나리오테스트

4. **영향문서**: 본구현에 수반하여업데이트이필요한 문서를列挙

5. **보충**: 추가의구현주의事項

## 출력형식

```
## Bugfix agent DETAIL_DESIGN

### DETAIL_DESIGN / 변경計画
- File/Function: <...>
- Steps: <bullet list>

### DETAIL_DESIGN / 테스트케이스
| ID | Purpose | Input | Expected | Size(S/M/L) |
|----|---------|-------|----------|-------------|

### DETAIL_DESIGN / 영향문서
| 문서 | 업데이트내용 | 필요性 |
|-------------|---------|--------|

### DETAIL_DESIGN / 보충
- ...
```

## Issue 업데이트방법

1. `gh issue view` 로 Issue 本文를 취득
2. Issue 本文를 업데이트:
 - 初회(Loop=1): Output 를 Issue 本文의 말미에追記
 - 2회目이후(Loop>=2): 기존의 `## Bugfix agent DETAIL_DESIGN` 섹션를삭제し, 새로운 Output 를 말미에追記
3. `gh issue edit` 로 Issue 本文를 업데이트
4. `gh issue comment` 로 `DETAIL_DESIGN agent Update` 코멘트로서업데이트내용의サマリーを投稿

## 証跡저장선

`${artifacts_dir}`
