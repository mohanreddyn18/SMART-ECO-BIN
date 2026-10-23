from typing import List, Dict, Any, Optional
from app.utils.helpers import get_current_iso_time
from app.services.storage_service import storage_service

MINIMUM_EVENTS = 10
RECENT_WINDOW = 20
HAZARDOUS_SHARE_THRESHOLD = 0.20
LOW_CONFIDENCE_THRESHOLD = 60.0
LOW_CONFIDENCE_MINIMUM = 3


class AnomalyDetector:
    """
    Applies transparent threshold checks to recent classification records.
    It does not infer physical sensor readings or locations.
    """

    def get_active_anomalies(self, records: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Checks the most recent records for hazardous-stream concentration and
        repeated low-confidence classifications.
        """
        if records is None:
            records = storage_service.list_records(limit=500)

        if len(records) < MINIMUM_EVENTS:
            return []

        anomalies: List[Dict[str, Any]] = []
        recent = records[:RECENT_WINDOW]
        sample_size = len(recent)
        event_reference = recent[0].get("id", "LATEST")
        latest_timestamp = recent[0].get("timestamp", get_current_iso_time())
        hazard_count = sum(1 for r in recent if r.get("compartmentId") == "bin_hazardous")
        hazardous_share = hazard_count / sample_size

        if hazardous_share >= HAZARDOUS_SHARE_THRESHOLD:
            anomalies.append({
                "id": f"ANOM-HAZ-{event_reference}",
                "type": "High Hazardous-Stream Share",
                "severity": "High",
                "category": "Waste Stream Distribution",
                "location": "Not recorded",
                "reason": (
                    f"{hazard_count} of the {sample_size} most recent records "
                    f"({hazardous_share:.0%}) are classified as hazardous; "
                    f"the review threshold is {HAZARDOUS_SHARE_THRESHOLD:.0%}."
                ),
                "recommendation": (
                    "Review the flagged classifications and confirm handling against "
                    "local hazardous-waste guidance."
                ),
                "timestamp": latest_timestamp
            })

        low_confidence_count = 0
        for record in recent:
            try:
                confidence = float(record.get("confidence"))
            except (TypeError, ValueError):
                continue
            if confidence < LOW_CONFIDENCE_THRESHOLD:
                low_confidence_count += 1

        if low_confidence_count >= LOW_CONFIDENCE_MINIMUM:
            anomalies.append({
                "id": f"ANOM-CONF-{event_reference}",
                "type": "Low-Confidence Classification Cluster",
                "severity": "Medium",
                "category": "Classification Uncertainty",
                "location": "Not recorded",
                "reason": (
                    f"{low_confidence_count} of the {sample_size} most recent records "
                    f"have classifier confidence below {LOW_CONFIDENCE_THRESHOLD:.0f}%."
                ),
                "recommendation": (
                    "Manually review the affected classifications before relying on their "
                    "disposal guidance."
                ),
                "timestamp": latest_timestamp
            })

        return anomalies


anomaly_detector = AnomalyDetector()
