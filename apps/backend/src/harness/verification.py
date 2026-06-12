"""Verification Loop — Gather-Act-Verify for Harness.

Aligned with dev-plan H3: "Verification Loop: Gather-Act-Verify".

Each verification step:
  1. GATHER — collect evidence (tool outputs, state, memory)
  2. ACT    — re-run or patch if needed
  3. VERIFY — check assertions against rubric

Used by ComplianceGuard, PoolPredictor, and Publisher as VERIFY gates.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VerificationStep:
    step_name: str
    gather: Dict[str, Any] = field(default_factory=dict)
    act_result: Dict[str, Any] = field(default_factory=dict)
    verify_passed: bool = False
    verify_notes: List[str] = field(default_factory=list)
    retry_count: int = 0


@dataclass
class VerificationReport:
    task_id: str
    overall_passed: bool = False
    steps: List[VerificationStep] = field(default_factory=list)
    summary: str = ""


def _gather_evidence(tool_outputs: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
    """Collect all available evidence for verification."""
    return {
        "tool_outputs": tool_outputs,
        "state": state,
        "tool_count": len(tool_outputs),
        "success_count": sum(1 for o in tool_outputs if o.get("success")),
    }


def _verify_assertions(evidence: Dict[str, Any], assertions: List[Dict[str, Any]]) -> tuple[bool, List[str]]:
    """Check assertions against evidence.

    assertion format: {"type": "all_success", "expected": True}
                      {"type": "field_eq", "field": "state.status", "expected": "approved"}
    """
    notes: List[str] = []
    passed = True

    for assertion in assertions:
        atype = assertion.get("type", "")
        expected = assertion.get("expected")

        if atype == "all_success":
            actual = all(o.get("success") for o in evidence.get("tool_outputs", []))
            if actual != expected:
                passed = False
                notes.append(f"Assertion 'all_success' failed: expected={expected}, actual={actual}")

        elif atype == "min_success":
            min_count = assertion.get("min_count", 1)
            actual = sum(1 for o in evidence.get("tool_outputs", []) if o.get("success"))
            if actual < min_count:
                passed = False
                notes.append(f"Assertion 'min_success' failed: min={min_count}, actual={actual}")

        elif atype == "field_eq":
            field_path = assertion.get("field", "")
            # Simple dot-path resolution
            value = evidence
            for part in field_path.split("."):
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break
            if value != expected:
                passed = False
                notes.append(f"Assertion 'field_eq' failed: {field_path} expected={expected}, actual={value}")

        else:
            notes.append(f"Unknown assertion type: {atype}")

    if not notes:
        notes.append("All assertions passed")

    return passed, notes


def run_verification(
    task_id: str,
    tool_outputs: List[Dict[str, Any]],
    state: Dict[str, Any],
    assertions: List[Dict[str, Any]],
    max_retries: int = 1,
) -> VerificationReport:
    """Run Gather-Act-Verify loop.

    MVP: GATHER and VERIFY only. ACT is a no-op placeholder
    (production would trigger re-run / patch logic).
    """
    report = VerificationReport(task_id=task_id)
    step = VerificationStep(step_name="main")

    # GATHER
    step.gather = _gather_evidence(tool_outputs, state)

    # ACT (placeholder — production: re-run failed tools)
    step.act_result = {"action": "verify_only", "patched": False}

    # VERIFY
    step.verify_passed, step.verify_notes = _verify_assertions(step.gather, assertions)
    step.retry_count = 0

    report.steps.append(step)
    report.overall_passed = step.verify_passed
    report.summary = f"Verification {'PASSED' if step.verify_passed else 'FAILED'} for task {task_id}"
    return report
