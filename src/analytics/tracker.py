"""
Performance Metrics Tracker and Normalizer.
Collects standardized performance metrics at aligned age windows (24h, 7d, 30d).
Maintains explicit availability flags so unmeasured metrics are not treated as zeros.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from src.core.contracts import MetricSnapshot


class MetricsTracker:
    def __init__(self):
        self.snapshots: List[MetricSnapshot] = []

    def record_snapshot(
        self,
        snapshot_id: str,
        trace_id: str,
        publish_intent_id: str,
        metric_name: str,
        metric_value: Optional[float],
        unit: str,
        window: str = "24h",
        platform_definition: str = "YouTube Shorts Views",
        availability: str = "available",
    ) -> MetricSnapshot:
        """
        Creates a validated MetricSnapshot conforming to contracts/metric_snapshot.json.
        """
        snapshot = MetricSnapshot(
            id=snapshot_id,
            trace_id=trace_id,
            publish_intent_id=publish_intent_id,
            metric_name=metric_name,
            availability=availability,
            metric_value=metric_value,
            unit=unit,
            platform_definition=platform_definition,
            window=window,
            captured_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        self.snapshots.append(snapshot)
        return snapshot
