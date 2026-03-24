"""GitHub integration for Bugfix Agent v5

This module provides:
- post_issue_comment: Post comments to GitHub Issues with retry
"""

from __future__ import annotations

import subprocess
import time
from typing import TYPE_CHECKING

from .config import get_config_value

if TYPE_CHECKING:
 from .run_logger import RunLogger


def post_issue_comment(
 issue_number: int,
 body: str,
 logger: RunLogger | None = None,
) -> bool:
 """GitHub Issue 에 코멘트를投稿한다(리트라이付き)

 Args:
 issue_number: Issue 번호
 body: 코멘트本文
 logger: 로그기록용(임의)

 Returns:
 성공한 경우 True, 전리트라이실패시 False
 """
 max_retries = get_config_value("github.max_comment_retries", 2)
 retry_delay = get_config_value("github.retry_delay", 1.0)

 for attempt in range(max_retries + 1):
 try:
 subprocess.run(
 ["gh", "issue", "comment", str(issue_number), "--body", body],
 check=True,
 capture_output=True,
 text=True,
 )
 print(f"✅ Posted comment to Issue #{issue_number}")
 return True
 except subprocess.CalledProcessError as e:
 error_msg = (
 f"Failed to post comment (attempt {attempt + 1}/{max_retries + 1}): {e.stderr}"
 )
 print(f"❌ {error_msg}")
 if logger:
 logger._log("comment_error", issue=issue_number, error=error_msg)
 if attempt < max_retries:
 time.sleep(retry_delay)

 print(f"⚠️ All retries exhausted for Issue #{issue_number} comment")
 return False
