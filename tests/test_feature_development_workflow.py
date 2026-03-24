"""Tests for feature-development.yaml workflow structure.

Verifies the workflow stops at PR creation (no auto close step).
Issue: #93
"""

from __future__ import annotations

from pathlib import Path

import pytest

from kuku_harness.cli_main import main
from kuku_harness.workflow import load_workflow, validate_workflow

WORKFLOW_PATH = Path(__file__).resolve().parent.parent / "workflows" / "feature-development.yaml"


# ============================================================
# Small tests — YAML structure verification
# ============================================================


class TestFeatureDevelopmentWorkflowSmall:
 """Small: verify workflow YAML structure after #93 changes."""

 @pytest.mark.small
 def test_pr_step_pass_transitions_to_end(self) -> None:
 """pr step PASS should transition to 'end', not 'close'."""
 wf = load_workflow(WORKFLOW_PATH)
 pr_step = wf.find_step("pr")
 assert pr_step is not None
 assert pr_step.on["PASS"] == "end"

 @pytest.mark.small
 def test_close_step_does_not_exist(self) -> None:
 """close step should not exist in the workflow."""
 wf = load_workflow(WORKFLOW_PATH)
 assert wf.find_step("close") is None

 @pytest.mark.small
 def test_description_says_pr_creation(self) -> None:
 """description should reference PR creation, not PR close."""
 wf = load_workflow(WORKFLOW_PATH)
 assert "PR 생성까지" in wf.description
 assert "클로즈" not in wf.description

 @pytest.mark.small
 def test_workflow_passes_validation(self) -> None:
 """Changed workflow must pass validate_workflow."""
 wf = load_workflow(WORKFLOW_PATH)
 validate_workflow(wf)


# ============================================================
# Medium tests — CLI validation integration
# ============================================================


class TestFeatureDevelopmentWorkflowMedium:
 """Medium: validate via CLI with real file I/O."""

 @pytest.mark.medium
 def test_kuku_validate_feature_development(self) -> None:
 """kuku validate should pass for the modified workflow."""
 exit_code = main(["validate", str(WORKFLOW_PATH)])
 assert exit_code == 0


# ============================================================
# Large tests — /kuku-run-verify 에 의한 실기 검증
# ============================================================
# Large 검증는 pytest 이 아니라 /kuku-run-verify 에 의한수동실행로실시한다.
# 검증명령어: /kuku-run-verify workflows/feature-development.yaml <issue>
# 검증결과는 Issue 코멘트로서기록된다.
# 설계書: draft/design/issue-93-workflow-stop-at-pr.md (Large 테스트 절)
