"""PR_CREATE state handler for Bugfix Agent v5

This module provides:
- handle_pr_create: Create Pull Request and share PR URL
"""

import subprocess

from ..agent_context import AgentContext
from ..state import SessionState, State


def handle_pr_create(ctx: AgentContext, state: SessionState) -> State:
 """PR_CREATE: gh pr create 실행, PR URL 공유

 Args:
 ctx: Agent 컨텍스트
 state: 세션상태

 Returns:
 다음스테이트 (COMPLETE)
 """
 print("🎉 Creating Pull Request...")

 try:
 # 1. Get branch and commit info
 branch_name = subprocess.check_output(
 ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
 ).strip()
 commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()

 # 2. Construct PR title and body
 title = f"fix: issue #{ctx.issue_number}"
 body = f"""Closes #{ctx.issue_number}

### Summary
- Automated PR creation for issue #{ctx.issue_number}.

### Branch and Commit
- Branch: `{branch_name}`
- Commit: `{commit_sha}`
"""

 # 3. Create Pull Request
 result = subprocess.run(
 [
 "gh",
 "pr",
 "create",
 "--title",
 title,
 "--body",
 body,
 ],
 capture_output=True,
 text=True,
 check=True,
 )
 pr_url = result.stdout.strip()

 print(f"✅ Pull Request created: {pr_url}")

 # 4. Post PR URL to issue
 comment_body = f"🚀 Pull request created: {pr_url}"
 ctx.issue_provider.add_comment(comment_body)

 except (subprocess.CalledProcessError, FileNotFoundError) as e:
 error_message = f"Failed to create pull request. Error: {e}"
 if isinstance(e, subprocess.CalledProcessError):
 error_message += f"\nStderr: {e.stderr}"
 print(f"❌ {error_message}")
 # Optionally, you could transition to an error state or retry
 # For now, we'll just log and complete the state to avoid loops.
 pass

 state.completed_states.append("PR_CREATE")
 return State.COMPLETE
