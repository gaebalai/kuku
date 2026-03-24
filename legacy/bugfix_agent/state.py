"""State machine definitions for Bugfix Agent v5

This module provides:
- State: Workflow state enumeration (9 states)
- ExecutionMode: Execution mode enumeration
- ExecutionConfig: Execution configuration dataclass
- SessionState: Runtime session state dataclass
- infer_result_label: State transition label inference
"""

from dataclasses import dataclass, field
from enum import Enum, auto

from .verdict import Verdict


class State(Enum):
 """상태 머신의 상태정의 (Issue #194 Protocol)

 9스테이트구성(QA/QA_REVIEWはIMPLEMENT_REVIEW에 통합완료):
 - INIT: Issue정보의확인
 - INVESTIGATE: 再現·원인조사
 - INVESTIGATE_REVIEW: 조사결과리뷰
 - DETAIL_DESIGN: 상세설계
 - DETAIL_DESIGN_REVIEW: 설계 리뷰
 - IMPLEMENT: 구현
 - IMPLEMENT_REVIEW: 구현리뷰(QA기능통합)
 - PR_CREATE: PR생성
 - COMPLETE: 완료
 """

 INIT = auto()
 INVESTIGATE = auto()
 INVESTIGATE_REVIEW = auto()
 DETAIL_DESIGN = auto()
 DETAIL_DESIGN_REVIEW = auto()
 IMPLEMENT = auto()
 IMPLEMENT_REVIEW = auto()
 PR_CREATE = auto()
 COMPLETE = auto()


def infer_result_label(current: State, next_state: State) -> str:
 """스테이트전이부터판정라벨를推論한다

 리뷰스테이트의 전이패턴부터결과를판정:
 - 前進 → PASS
 - 직전의ワーク스테이트へ戻る → BLOCKED (INVESTIGATE/DETAIL_DESIGN系) or FIX_REQUIRED (IMPLEMENT系)
 - 설계까지戻る → DESIGN_FIX

 Note:
 이함수는 State 列挙타입와密결합하여い합니다.State 에 새로운리뷰스테이트を
 추가한 경우는, transitions 맵도동시에 업데이트한다필요가 있り합니다.

 Args:
 current: 현재의스테이트
 next_state: 다음스테이트

 Returns:
 판정라벨 ("PASS", "BLOCKED", "FIX_REQUIRED", "DESIGN_FIX")
 """
 # 비리뷰스테이트は常에 PASS(작업실행만)
 if not current.name.endswith("_REVIEW"):
 return "PASS"

 # 리뷰스테이트의 전이패턴
 # Issue #194 Protocol: VERDICT형식에統一
 transitions = {
 # INVESTIGATE_REVIEW: PASS→DETAIL_DESIGN, RETRY→INVESTIGATE
 (State.INVESTIGATE_REVIEW, State.DETAIL_DESIGN): Verdict.PASS.value,
 (State.INVESTIGATE_REVIEW, State.INVESTIGATE): Verdict.RETRY.value,
 # DETAIL_DESIGN_REVIEW: PASS→IMPLEMENT, RETRY→DETAIL_DESIGN
 (State.DETAIL_DESIGN_REVIEW, State.IMPLEMENT): Verdict.PASS.value,
 (State.DETAIL_DESIGN_REVIEW, State.DETAIL_DESIGN): Verdict.RETRY.value,
 # IMPLEMENT_REVIEW (QA통합): PASS→PR_CREATE, RETRY→IMPLEMENT, BACK_DESIGN→DETAIL_DESIGN
 (State.IMPLEMENT_REVIEW, State.PR_CREATE): Verdict.PASS.value,
 (State.IMPLEMENT_REVIEW, State.IMPLEMENT): Verdict.RETRY.value,
 (State.IMPLEMENT_REVIEW, State.DETAIL_DESIGN): Verdict.BACK_DESIGN.value,
 }

 return transitions.get((current, next_state), "UNKNOWN")


class ExecutionMode(Enum):
 """실행모드정의"""

 FULL = auto() # INIT → COMPLETE 까지통상실행
 SINGLE = auto() # 지정스테이트만1회실행하여종료
 FROM_END = auto() # 지정스테이트부터 COMPLETE 까지실행


@dataclass
class ExecutionConfig:
 """실행설정"""

 mode: ExecutionMode # 실행모드
 target_state: State | None = None # SINGLE/FROM_END 시의 대상스테이트
 issue_url: str = "" # Issue URL
 issue_number: int = 0 # issue_url 부터추출
 tool_override: str | None = None # 도구지정 (codex, gemini, claude)
 model_override: str | None = None # 모델지정 (--tool-model 로 사용)


@dataclass
class SessionState:
 """실행中의 상태(변수로서보유)"""

 completed_states: list[str] = field(default_factory=list)
 current_state: State = State.INIT
 loop_counters: dict[str, int] = field(
 default_factory=lambda: {
 "Investigate_Loop": 0,
 "Detail_Design_Loop": 0,
 "Implement_Loop": 0,
 }
 )
 active_conversations: dict[str, str | None] = field(
 default_factory=lambda: {
 "Design_Thread_conversation_id": None,
 "Implement_Loop_conversation_id": None,
 }
 )
