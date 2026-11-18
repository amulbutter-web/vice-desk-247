"""
Quality Control Supervisor.
Orchestrates hard deterministic gates and editorial review.
Manages the automated repair loop with strict 2-revision cap.
"""
from typing import Dict, Any, List, Optional
from src.config import settings
from src.core.contracts import QCResult
from src.qc.hard_gates import HardQualityGates
from src.qc.editorial_judge import EditorialJudge


class QCSupervisor:
    def __init__(self, hard_gates: HardQualityGates, judge: EditorialJudge):
        self.hard_gates = hard_gates
        self.judge = judge

    def audit_render(
        self,
        audit_id: str,
        trace_id: str,
        render_id: str,
        media_path: str,
        event_candidate: Dict[str, Any],
        edit_plan: Dict[str, Any],
        current_revision: int = 1,
        hud_occluded: bool = False,
    ) -> QCResult:
        """
        Executes complete QC audit.
        If hard gates fail -> editorial cannot pass.
        If revision >= max_repair_revisions -> escalates to human_review or reject.
        """
        hard_pass, gates = self.hard_gates.run_all_gates(media_path)
        editorial = self.judge.evaluate(event_candidate, edit_plan, hud_occluded=hud_occluded)

        # Enforce hard-gate override
        if not hard_pass:
            editorial.result = "reject"

        # Check revision limits for repair
        if editorial.result == "repair" and current_revision >= settings.max_repair_revisions:
            editorial.result = "human_review"

        return QCResult(
            id=audit_id,
            trace_id=trace_id,
            render_id=render_id,
            evaluator_kind="deterministic" if hard_pass else "deterministic",
            evaluator_version="v2.0",
            hard_gates=gates,
            editorial=editorial,
            source_evidence_refs=[render_id],
        )
