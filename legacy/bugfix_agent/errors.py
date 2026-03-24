"""Custom exceptions for Bugfix Agent v5

This module defines all custom exception classes:
- ToolError: AI tool returned an error
- LoopLimitExceeded: Circuit breaker for loop count
- VerdictParseError: Failed to parse VERDICT format
- AgentAbortError: Agent returned ABORT verdict
"""


class ToolError(Exception):
 """AI 도구이 에러를返한 경우의예외"""

 pass


class LoopLimitExceeded(Exception):
 """ループ회수제한를초과한 경우의예외(Circuit Breaker)"""

 pass


class VerdictParseError(Exception):
 """VERDICT형식의파싱에실패한 경우의예외

 This is raised when no Result/Status line is found.
 Recoverable via fallback parsing (Step 2) or AI formatter (Step 3).
 """

 pass


class InvalidVerdictValueError(VerdictParseError):
 """VERDICT값이부정한 경우의예외

 This is raised when a Result/Status line is found but contains an invalid value.
 NOT recoverable via fallback - indicates a prompt violation or implementation bug.
 """

 pass


class AgentAbortError(Exception):
 """에이전트이ABORTを返한 경우의예외

 Attributes:
 reason: ABORT이유
 suggestion: 다음アクション提案
 """

 def __init__(self, reason: str, suggestion: str = ""):
 self.reason = reason
 self.suggestion = suggestion
 super().__init__(f"Agent aborted: {reason}")


def check_tool_result(result: str, tool_name: str) -> str:
 """도구결과를체크し, ERROR 라면예외를投げる

 Args:
 result: 도구의 반환값
 tool_name: 도구명(에러메시지용)

 Returns:
 result 를 그まま반환하다(ERROR 로 없는 경우)

 Raises:
 ToolError: result 이 "ERROR" 의 경우
 """
 if result == "ERROR":
 raise ToolError(f"{tool_name} returned ERROR")
 return result
