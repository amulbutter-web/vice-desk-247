"""
Cohort Analysis and Hypothesis Engine.
Compares performance across creative dimensions (e.g., layout mode, duration, hook length)
and generates empirical, testable policy updates.
"""
from typing import List, Dict, Any
import statistics


class HypothesisEngine:
    def evaluate_layout_cohorts(
        self, performance_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyzes retention and view metrics grouped by creative layout mode:
        split_cam_game vs center_roi vs pip.
        """
        cohorts: Dict[str, List[float]] = {}

        for item in performance_data:
            layout = item.get("layout_mode", "center_roi")
            retention = item.get("average_percentage_viewed", 0.0)
            if layout not in cohorts:
                cohorts[layout] = []
            cohorts[layout].append(retention)

        averages = {k: statistics.mean(v) if v else 0.0 for k, v in cohorts.items()}
        counts = {k: len(v) for k, v in cohorts.items()}

        best_layout = max(averages.items(), key=lambda x: x[1])[0] if averages else "split_cam_game"

        hypothesis = {
            "metric_evaluated": "average_percentage_viewed",
            "cohort_averages": averages,
            "sample_counts": counts,
            "recommended_policy_change": f"Promote {best_layout} as default layout",
            "statistical_significance": len(performance_data) >= 10,
        }

        return hypothesis
