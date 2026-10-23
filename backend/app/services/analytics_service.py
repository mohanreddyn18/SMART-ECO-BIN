from collections import Counter
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.utils.helpers import get_current_iso_time
from app.services.storage_service import storage_service

CATEGORY_COLORS = {
    'Recyclable / Dry Waste': '#2563eb',
    'Organic / Wet Waste': '#10b981',
    'Hazardous / Other': '#ef4444',
    'Non-Recyclable': '#4b5563',
    'Uncertain / Manual Review': '#f59e0b',
    'General Waste': '#6b7280'
}


class AnalyticsService:
    """
    Analytics and operational intelligence engine.
    Derives all statistics dynamically from the unified storage_service ledger.
    Never fabricates statistics or claims physical sensors exist.
    """

    def __init__(self):
        self.storage = storage_service

    def add_record(self, record: Dict[str, Any], idempotency_key: Optional[str] = None) -> str:
        """Saves a record via unified storage provider with idempotency protection."""
        return self.storage.save_record(record, idempotency_key=idempotency_key)

    def get_history(self, limit: int = 50, skip: int = 0, category: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns history records from unified storage."""
        return self.storage.list_records(limit=limit, skip=skip, category=category, search=search)

    def count_records(self) -> int:
        return self.storage.count_records()

    def clear_records(self) -> None:
        """Resets the storage ledger (for testing empty states)."""
        self.storage.clear_records()

    def get_macro_analytics(
        self,
        period: str = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates macro and time-filtered telemetry metrics directly from verified storage events.
        Aggregates both single-item and multi-object mixed-waste detections.
        Never fabricates statistics or claims physical sensors exist.
        """
        from datetime import timedelta

        all_records = self.storage.list_records(limit=20000)
        now = datetime.utcnow()
        today_str = now.strftime("%Y-%m-%d")

        # 1. Parse timestamps and sort records
        def parse_ts(r: Dict[str, Any]) -> datetime:
            raw = r.get("timestamp", "")
            if not raw:
                return now
            try:
                # Handle ISO timestamps with Z or timezone offset
                clean = raw.replace("Z", "+00:00")
                return datetime.fromisoformat(clean).replace(tzinfo=None)
            except Exception:
                try:
                    return datetime.strptime(raw[:19], "%Y-%m-%dT%H:%M:%S")
                except Exception:
                    return now

        records_with_dt = [(r, parse_ts(r)) for r in all_records]
        records_with_dt.sort(key=lambda x: x[1])

        # 2. Determine time-filter boundaries
        filter_start = None
        filter_end = None
        prev_start = None
        prev_end = None
        bucket_format = "%Y-%m-%d"

        period_lower = (period or "all").lower().strip()

        if period_lower == "hourly":
            filter_start = now - timedelta(hours=24)
            filter_end = now
            prev_start = filter_start - timedelta(hours=24)
            prev_end = filter_start
            bucket_format = "%H:00"
        elif period_lower == "daily":
            filter_start = now - timedelta(days=7)
            filter_end = now
            prev_start = filter_start - timedelta(days=7)
            prev_end = filter_start
            bucket_format = "%Y-%m-%d"
        elif period_lower == "weekly":
            filter_start = now - timedelta(days=28)
            filter_end = now
            prev_start = filter_start - timedelta(days=28)
            prev_end = filter_start
            bucket_format = "W%W"
        elif period_lower == "monthly":
            filter_start = now - timedelta(days=90)
            filter_end = now
            prev_start = filter_start - timedelta(days=90)
            prev_end = filter_start
            bucket_format = "%Y-%m"
        elif period_lower == "yearly":
            filter_start = now - timedelta(days=365)
            filter_end = now
            prev_start = filter_start - timedelta(days=365)
            prev_end = filter_start
            bucket_format = "%Y-%m"
        elif period_lower == "custom" and start_date and end_date:
            try:
                filter_start = datetime.strptime(start_date[:10], "%Y-%m-%d")
                filter_end = datetime.strptime(end_date[:10], "%Y-%m-%d") + timedelta(days=1)
                window_duration = filter_end - filter_start
                prev_start = filter_start - window_duration
                prev_end = filter_start
                bucket_format = "%Y-%m-%d"
            except Exception:
                filter_start = None
                filter_end = None

        # 3. Filter current window records & previous window records
        if filter_start and filter_end:
            current_records = [r for r, dt in records_with_dt if filter_start <= dt <= filter_end]
            previous_records = [r for r, dt in records_with_dt if prev_start and prev_end and prev_start <= dt < prev_end]
        else:
            current_records = [r for r, dt in records_with_dt]
            previous_records = []

        total_uploads = len(current_records)

        # 4. Aggregate metrics across filtered records
        total_objects = 0
        wet_count = 0
        dry_count = 0
        hazardous_count = 0
        manual_review_count = 0
        class_counts: Dict[str, int] = {}
        confidence_sum = 0.0
        confidence_count = 0
        today_activity = 0
        bucket_map: Dict[str, Dict[str, Any]] = {}

        for r, dt in [(r, parse_ts(r)) for r in current_records]:
            # Today's activity check
            if dt.strftime("%Y-%m-%d") == today_str:
                today_activity += 1

            # Accumulate confidence
            conf = float(r.get("confidence", 0.0))
            if conf > 0:
                confidence_sum += conf
                confidence_count += 1

            # Determine bucket key
            bucket_key = dt.strftime(bucket_format)
            if bucket_key not in bucket_map:
                bucket_map[bucket_key] = {
                    "date": bucket_key,
                    "count": 0,
                    "objects": 0,
                    "recyclable": 0,
                    "organic": 0,
                    "hazardous": 0,
                    "trash": 0
                }
            bucket_map[bucket_key]["count"] += 1

            # Check if record is a multi-object detection
            if r.get("type") == "multi_object_detection" or "totalDetections" in r:
                objs = int(r.get("totalDetections", len(r.get("detections", []))))
                total_objects += objs
                bucket_map[bucket_key]["objects"] += objs

                sum_dict = r.get("summary", {})
                w = int(sum_dict.get("wet_items", 0))
                d = int(sum_dict.get("dry_items", 0))
                h = int(sum_dict.get("hazardous_items", 0))
                m = int(sum_dict.get("manual_review_items", 0))

                wet_count += w
                dry_count += d
                hazardous_count += h
                manual_review_count += m

                bucket_map[bucket_key]["organic"] += w
                bucket_map[bucket_key]["recyclable"] += d
                bucket_map[bucket_key]["hazardous"] += h
                bucket_map[bucket_key]["trash"] += m

                for det in r.get("detections", []):
                    lbl = det.get("label", "unknown")
                    class_counts[lbl] = class_counts.get(lbl, 0) + 1
            else:
                # Single-item classification
                total_objects += 1
                bucket_map[bucket_key]["objects"] += 1

                wt = r.get("wasteType", "")
                cls = r.get("predictedClass", "unknown")
                class_counts[cls] = class_counts.get(cls, 0) + 1

                if "Organic" in wt or "Wet" in wt or cls in ("biological", "apple", "banana", "broccoli"):
                    wet_count += 1
                    bucket_map[bucket_key]["organic"] += 1
                elif "Recyclable" in wt or "Dry" in wt or cls in ("plastic", "paper", "cardboard", "metal", "brown-glass", "white-glass", "green-glass"):
                    dry_count += 1
                    bucket_map[bucket_key]["recyclable"] += 1
                elif "Hazardous" in wt or cls in ("battery",):
                    hazardous_count += 1
                    bucket_map[bucket_key]["hazardous"] += 1
                else:
                    manual_review_count += 1
                    bucket_map[bucket_key]["trash"] += 1

        avg_conf = round(confidence_sum / confidence_count, 1) if confidence_count > 0 else 0.0

        # Category distribution for chart.js doughnut
        if total_objects > 0:
            distribution_labels = ['Recyclable / Dry', 'Organic / Wet', 'Hazardous / E-Waste', 'Residual / Review']
            distribution_counts = [dry_count, wet_count, hazardous_count, manual_review_count]
            distribution_colors = ['#2563eb', '#10b981', '#f59e0b', '#6b7280']
            volume_trends = sorted(bucket_map.values(), key=lambda x: x["date"])
            weekly_daily = volume_trends
        else:
            distribution_labels = []
            distribution_counts = []
            distribution_colors = []
            volume_trends = []
            weekly_daily = []

        # Determine dominant top category
        cat_map = {'Recyclable / Dry Waste': dry_count, 'Organic / Wet Waste': wet_count, 'Hazardous / Other': hazardous_count, 'Manual Review': manual_review_count}
        top_category = max(cat_map.items(), key=lambda x: x[1])[0] if total_objects > 0 else "None"

        # 5. Calculate comparison metrics with previous equivalent period
        prev_uploads = len(previous_records)
        prev_objects = 0
        prev_wet = 0
        prev_dry = 0
        prev_hazardous = 0

        for r in previous_records:
            if r.get("type") == "multi_object_detection" or "totalDetections" in r:
                prev_objects += int(r.get("totalDetections", len(r.get("detections", []))))
                s = r.get("summary", {})
                prev_wet += int(s.get("wet_items", 0))
                prev_dry += int(s.get("dry_items", 0))
                prev_hazardous += int(s.get("hazardous_items", 0))
            else:
                prev_objects += 1
                wt = r.get("wasteType", "")
                if "Organic" in wt or "Wet" in wt:
                    prev_wet += 1
                elif "Recyclable" in wt or "Dry" in wt:
                    prev_dry += 1
                elif "Hazardous" in wt:
                    prev_hazardous += 1

        def calc_pct_change(curr: int, prev: int) -> Dict[str, Any]:
            diff = curr - prev
            if prev == 0 and curr == 0:
                pct = 0.0
            elif prev == 0:
                pct = 100.0
            else:
                pct = round(((curr - prev) / prev) * 100.0, 1)
            return {"current": curr, "previous": prev, "absolute_change": diff, "percentage_change": pct}

        comparison = {
            "has_baseline": len(previous_records) > 0,
            "uploads": calc_pct_change(total_uploads, prev_uploads),
            "objects": calc_pct_change(total_objects, prev_objects),
            "wet": calc_pct_change(wet_count, prev_wet),
            "dry": calc_pct_change(dry_count, prev_dry),
            "hazardous": calc_pct_change(hazardous_count, prev_hazardous)
        }

        # Operational status and active anomalies
        storage_meta = self.storage.get_status()
        active_provider = storage_meta.get("cloud_provider", "Local Registry")

        # Evaluate sanitation status
        sanitation_status = "GOOD"
        if manual_review_count > 0 and (manual_review_count / max(total_objects, 1)) > 0.20:
            sanitation_status = "ATTENTION REQUIRED"

        return {
            "totalClassifications": total_uploads,
            "distribution": {
                "labels": distribution_labels,
                "counts": distribution_counts,
                "colors": distribution_colors
            },
            "weeklyTrends": {
                "daily": weekly_daily
            },
            "averageConfidence": avg_conf,
            "topCategory": top_category,
            "dataSource": f"{active_provider} (Verified Event Ledger)",
            "hardwareSensors": False,

            # Enhanced Schema Fields for Dashboard, Graphs & Period Filters
            "categoryBreakdown": {
                "recyclable": dry_count,
                "organic": wet_count,
                "hazardous": hazardous_count,
                "trash": manual_review_count
            },
            "volumeTrends": volume_trends,
            "classBreakdown": class_counts,
            "todayActivity": today_activity,
            "storageProvider": active_provider,
            "sanitationStatus": sanitation_status,
            "activeAnomalies": 0,

            # Time-Filter Dimensions
            "timePeriod": period_lower,
            "totalUploads": total_uploads,
            "totalObjectsDetected": total_objects,
            "wetCount": wet_count,
            "dryCount": dry_count,
            "hazardousCount": hazardous_count,
            "manualReviewCount": manual_review_count,
            "comparison": comparison,
            "timeSeries": volume_trends
        }

    def get_sanitation_posture(self) -> Dict[str, Any]:
        """
        Computes software sanitation indicators based on real event streams.
        Explicitly declares that no physical IoT sensors are deployed.
        """
        records = self.storage.list_records(limit=1000)
        total = len(records)

        if total == 0:
            return {
                "currentStatus": "UNAVAILABLE",
                "reason": "No classification events recorded. Computational sanitation assessment requires minimum baseline intake telemetry.",
                "lastUpdated": get_current_iso_time(),
                "hardwareSensors": False,
                "telemetrySource": "Software Classification Ledger (Zero IoT Hardware)",
                "supportingIndicators": [],
                "locationSignals": [],
                "recommendations": ["Submit initial waste items for classification to calibrate municipal baseline."]
            }

        high_conf_count = sum(1 for r in records if float(r.get("confidence", 0.0)) >= 85.0)
        quarantine_count = sum(1 for r in records if r.get("requiresManualReview") or r.get("routingStatus") != "AUTOMATED_ROUTED")
        organic_count = sum(1 for r in records if "Organic" in r.get("wasteType", ""))
        hazardous_count = sum(1 for r in records if "Hazardous" in r.get("wasteType", ""))

        high_confidence_share = round((high_conf_count / total) * 100.0, 1)
        quarantine_rate = round((quarantine_count / total) * 100.0, 1)
        organic_skew = round((organic_count / total) * 100.0, 1)

        if quarantine_rate > 20.0 or high_confidence_share < 70.0:
            status = "ATTENTION REQUIRED"
            reason = (
                f"Record-derived indicators show {quarantine_rate}% of items require manual review "
                f"and {high_confidence_share}% have confidence of at least 85%. No live sensors are connected."
            )
        else:
            status = "GOOD"
            reason = (
                f"Stored records show {quarantine_rate}% of items require manual review and "
                f"{high_confidence_share}% have confidence of at least 85%. No live sensors are connected."
            )

        recommendations = []
        if quarantine_count:
            recommendations.append(
                f"Review the {quarantine_count} stored records routed for manual review before disposal."
            )
        if hazardous_count:
            recommendations.append(
                f"Check local hazardous-waste guidance for the {hazardous_count} records classified as hazardous."
            )
        if organic_count:
            recommendations.append(
                f"Review local organic-waste requirements for the {organic_count} records classified as organic."
            )
        if not recommendations:
            recommendations.append(
                "No manual-review, hazardous, or organic events appear in the records currently available."
            )

        return {
            "currentStatus": status,
            "lastUpdated": get_current_iso_time(),
            "reason": reason,
            "hardwareSensors": False,
            "telemetrySource": "Software Event Ledger (Zero IoT Hardware)",
            "supportingIndicators": [
                {"indicator": "High-Confidence Classification Share", "value": f"{high_confidence_share}%", "threshold": "≥ 70.0%", "status": "NORMAL" if high_confidence_share >= 70 else "WARNING"},
                {"indicator": "Organic / Wet Stream Skew", "value": f"{organic_skew}%", "threshold": "15% - 40%", "status": "NORMAL" if 15 <= organic_skew <= 40 else "WARNING"},
                {"indicator": "Quarantine / Contamination Rate", "value": f"{quarantine_rate}%", "threshold": "≤ 10.0%", "status": "NORMAL" if quarantine_rate <= 10 else "WARNING"},
                {"indicator": "Active Verified Ledger Events", "value": str(total), "threshold": "≥ 1", "status": "NORMAL"}
            ],
            "locationSignals": [],
            "recommendations": recommendations
        }


analytics_service = AnalyticsService()
