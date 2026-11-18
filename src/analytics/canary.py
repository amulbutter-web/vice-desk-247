"""
Canary Rollout and Safe Rollback Manager.
Guards experimental policy updates by testing on a canary cohort
with automatic rollback on detected regressions.
"""
from typing import Dict, Any, List


class CanaryManager:
    def __init__(self, canary_traffic_pct: float = 0.20):
        self.canary_traffic_pct = canary_traffic_pct
        self.active_policy: str = "v1_default"
        self.canary_policy: Optional[str] = None
        self.is_rolled_back: bool = False

    def deploy_canary(self, new_policy_id: str):
        """Activates a new candidate policy for canary traffic."""
        self.canary_policy = new_policy_id
        self.is_rolled_back = False

    def evaluate_and_decide(
        self,
        baseline_pass_rate: float,
        canary_pass_rate: float,
        min_allowed_pass_rate: float = 0.85,
    ) -> Dict[str, Any]:
        """
        Evaluates canary quality metrics against baseline.
        Triggers instant rollback if regression is detected.
        """
        if canary_pass_rate < min_allowed_pass_rate or canary_pass_rate < (baseline_pass_rate - 0.10):
            # Rollback
            reverted_policy = self.canary_policy
            self.canary_policy = None
            self.is_rolled_back = True
            return {
                "decision": "ROLLBACK",
                "reason": f"Canary pass rate ({canary_pass_rate:.2f}) dropped below threshold ({min_allowed_pass_rate:.2f})",
                "active_policy": self.active_policy,
                "reverted_policy": reverted_policy,
            }

        # Promote canary to full production
        promoted = self.canary_policy
        self.active_policy = promoted
        self.canary_policy = None
        return {
            "decision": "PROMOTE",
            "reason": f"Canary pass rate ({canary_pass_rate:.2f}) confirmed stable vs baseline ({baseline_pass_rate:.2f})",
            "active_policy": self.active_policy,
        }
