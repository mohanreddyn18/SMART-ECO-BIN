import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from app.services.storage_service import BaseStorageProvider, storage_service

logger = logging.getLogger("ecosort.migration")


class MigrationService:
    """
    Service for securely migrating existing local JSON classification records
    into Google Cloud Firestore (or another BaseStorageProvider target).
    Guarantees:
    - Never overwrites or deletes the local JSON file.
    - Repeatable and idempotent: skips existing records to prevent duplication.
    - Validates record integrity and reports malformed entries.
    - Supports dry-run simulation mode.
    """

    REQUIRED_FIELDS = ("id", "predictedClass", "wasteType", "confidence")

    def __init__(self, target_provider: Optional[BaseStorageProvider] = None):
        self.target_provider = target_provider or storage_service

    def validate_record(self, record: Any) -> Tuple[bool, Optional[str]]:
        """Validates that a record dictionary satisfies the minimal event schema."""
        if not isinstance(record, dict):
            return False, "Record is not a valid JSON object."

        for field in self.REQUIRED_FIELDS:
            if field not in record or record[field] is None:
                return False, f"Missing required schema field: '{field}'."

        try:
            float(record.get("confidence", 0.0))
        except (ValueError, TypeError):
            return False, f"Invalid confidence value: {record.get('confidence')}."

        return True, None

    def migrate_from_file(
        self,
        json_file_path: str,
        dry_run: bool = False,
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Migrates records from a source JSON file into the target storage provider.
        Does NOT alter or delete the source JSON file.
        """
        report: Dict[str, Any] = {
            "source_file": os.path.abspath(json_file_path),
            "target_provider": self.target_provider.__class__.__name__,
            "dry_run": dry_run,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_found": 0,
            "imported": 0,
            "skipped": 0,
            "failed": 0,
            "errors": []
        }

        if not os.path.exists(json_file_path):
            report["errors"].append({"id": "N/A", "error": f"Source file not found: {json_file_path}"})
            return report

        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception as e:
            report["errors"].append({"id": "N/A", "error": f"Failed to parse JSON from {json_file_path}: {e}"})
            return report

        if not isinstance(records, list):
            report["errors"].append({"id": "N/A", "error": f"Root JSON in {json_file_path} must be a list."})
            return report

        report["total_found"] = len(records)
        logger.info(f"Starting migration of {len(records)} records from {json_file_path} (dry_run={dry_run}).")

        for idx, rec in enumerate(records):
            is_valid, validation_err = self.validate_record(rec)
            record_id = rec.get("id") if isinstance(rec, dict) else f"index_{idx}"

            if not is_valid:
                report["failed"] += 1
                report["errors"].append({"id": record_id, "error": validation_err})
                continue

            # Idempotency check: does record already exist in the target provider?
            try:
                existing = self.target_provider.get_record(record_id)
                if existing:
                    report["skipped"] += 1
                    continue
            except Exception as e:
                logger.warning(f"Error checking existing record '{record_id}' in target: {e}")

            # If dry_run, do not write to target
            if dry_run:
                report["imported"] += 1
                continue

            # Perform genuine persistence
            try:
                idempotency_key = rec.get("idempotencyKey")
                self.target_provider.save_record(rec, idempotency_key=idempotency_key)
                report["imported"] += 1
            except Exception as e:
                report["failed"] += 1
                report["errors"].append({"id": record_id, "error": f"Failed to persist: {str(e)}"})
                logger.error(f"Migration error for record '{record_id}': {e}")

        logger.info(
            f"Migration completed. Processed: {report['total_found']}, "
            f"Imported: {report['imported']}, Skipped: {report['skipped']}, Failed: {report['failed']}."
        )
        return report
