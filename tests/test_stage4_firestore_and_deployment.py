import os
import sys
import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.services.storage_service import (
    LocalStorageProvider,
    FirestoreStorageProvider,
    create_storage_provider
)
from app.services.migration_service import MigrationService
from app.services.image_storage_service import GoogleCloudImageStorageService


class TestStage4FirestoreAndDeployment(unittest.TestCase):
    """
    Automated verification suite for Stage 4:
    - Google Cloud Firestore storage provider abstraction
    - Atomic idempotency and bounded query controls
    - Explicit failure reporting without silent fallback
    - Safe, repeatable local-to-cloud migration
    - Private GCS image storage policy (zero-retention default)
    """

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_json_file = os.path.join(self.test_dir.name, "test_records.json")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_01_local_storage_creation_and_retrieval(self):
        """Verifies that LocalStorageProvider persists and retrieves valid records."""
        provider = LocalStorageProvider(storage_file=self.test_json_file)
        self.assertEqual(provider.count_records(), 0)

        record = {
            "itemName": "Aluminum Beverage Can",
            "predictedClass": "metal",
            "wasteType": "Recyclable / Dry Waste",
            "confidence": 98.5,
            "recommendation": "Crush can and deposit in metal stream.",
            "destinationCompartment": "Metal & Can Stream Bin",
            "routingStatus": "AUTOMATED_ROUTED"
        }
        rec_id = provider.save_record(record, idempotency_key="TEST-KEY-001")
        self.assertTrue(rec_id.startswith("REC-"))
        self.assertEqual(provider.count_records(), 1)

        retrieved = provider.get_record(rec_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["predictedClass"], "metal")
        self.assertEqual(retrieved["idempotencyKey"], "TEST-KEY-001")

    def test_02_firestore_provider_mocked_operations(self):
        """Verifies FirestoreStorageProvider operations using a mocked Firestore client."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_doc_ref = MagicMock()
        mock_doc = MagicMock()

        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref
        mock_doc_ref.get.return_value = mock_doc
        mock_doc.exists = False  # Initially document does not exist

        provider = FirestoreStorageProvider(mock_db, project_id="test-eco-bin-project", collection_name="waste_records")

        record = {
            "id": "REC-FIRESTORE-001",
            "itemName": "Cardboard Box",
            "predictedClass": "cardboard",
            "wasteType": "Recyclable / Dry Waste",
            "confidence": 95.0,
            "destinationCompartment": "Cardboard Recycling Bin"
        }

        # 1. Save record
        saved_id = provider.save_record(record)
        self.assertEqual(saved_id, "REC-FIRESTORE-001")
        mock_doc_ref.set.assert_called_once()
        saved_payload = mock_doc_ref.set.call_args[0][0]
        self.assertEqual(saved_payload["id"], "REC-FIRESTORE-001")
        self.assertEqual(saved_payload["predictedClass"], "cardboard")
        self.assertEqual(saved_payload["simulationStatus"], "SIMULATED")

        # 2. Get record
        mock_doc.exists = True
        mock_doc.to_dict.return_value = saved_payload
        fetched = provider.get_record("REC-FIRESTORE-001")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["predictedClass"], "cardboard")

        # 3. Status
        status = provider.get_status()
        self.assertEqual(status["mode"], "firestore")
        self.assertEqual(status["project_id"], "test-eco-bin-project")
        self.assertTrue(status["persistent_cloud_enabled"])

    def test_03_firestore_idempotency_safeguards(self):
        """Verifies that duplicate requests in Firestore are detected and return the existing record."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_query = MagicMock()
        mock_existing_doc = MagicMock()

        mock_existing_doc.id = "REC-EXISTING-999"
        mock_existing_doc.to_dict.return_value = {
            "id": "REC-EXISTING-999",
            "predictedClass": "plastic",
            "idempotencyKey": "REPEAT-KEY-XYZ"
        }

        mock_db.collection.return_value = mock_collection
        mock_collection.where.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = [mock_existing_doc]

        provider = FirestoreStorageProvider(mock_db, project_id="test-eco-bin-project")

        # Submit new payload with same idempotency key
        duplicate_record = {
            "itemName": "Plastic Bottle",
            "predictedClass": "plastic",
            "wasteType": "Recyclable / Dry Waste",
            "confidence": 92.0
        }
        res_id = provider.save_record(duplicate_record, idempotency_key="REPEAT-KEY-XYZ")

        self.assertEqual(res_id, "REC-EXISTING-999")
        # Document.set should NOT be called since idempotent record was returned
        mock_collection.document().set.assert_not_called()

    def test_04_firestore_write_failure_raises_exception_without_silent_fallback(self):
        """
        CRITICAL REQUIREMENT:
        When Firestore write fails, the provider MUST raise an explicit exception
        and NEVER silently report success or fall back to local disk.
        """
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_doc_ref = MagicMock()

        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref
        mock_doc_ref.get.return_value = MagicMock(exists=False)
        mock_doc_ref.set.side_effect = Exception("DeadlineExceeded: Firestore write timeout")

        provider = FirestoreStorageProvider(mock_db, project_id="test-eco-bin-project")

        record = {
            "itemName": "Biological Waste",
            "predictedClass": "biological",
            "wasteType": "Organic / Wet Waste",
            "confidence": 88.0
        }

        with self.assertRaises(RuntimeError) as ctx:
            provider.save_record(record)

        self.assertIn("Google Cloud Firestore write failed", str(ctx.exception))

    def test_05_provider_selection_and_validation(self):
        """Verifies that STORAGE_PROVIDER environment variable is strictly validated."""
        # 1. Invalid provider value must raise ValueError
        with patch.dict(os.environ, {"STORAGE_PROVIDER": "unsupported_engine"}):
            with self.assertRaises(ValueError) as ctx:
                create_storage_provider()
            self.assertIn("Unsupported STORAGE_PROVIDER", str(ctx.exception))

        # 2. Local mode returns LocalStorageProvider
        with patch.dict(os.environ, {"STORAGE_PROVIDER": "local"}):
            provider = create_storage_provider()
            self.assertIsInstance(provider, LocalStorageProvider)

        # 3. Firestore mode with missing ADC raises RuntimeError with configuration instructions
        with patch.dict(os.environ, {"STORAGE_PROVIDER": "firestore", "FIREBASE_CREDENTIALS_PATH": "", "GOOGLE_APPLICATION_CREDENTIALS": ""}):
            with patch("google.cloud.firestore.Client", side_effect=Exception("DefaultCredentialsError")):
                with self.assertRaises(RuntimeError) as ctx:
                    create_storage_provider()
                self.assertIn("STORAGE_PROVIDER is set to 'firestore', but Firestore initialization failed", str(ctx.exception))

    def test_06_safe_migration_service(self):
        """Verifies that MigrationService validates records and skips duplicates safely."""
        mock_target = MagicMock(spec=FirestoreStorageProvider)
        mock_target.__class__.__name__ = "MockFirestoreProvider"

        # Record 1 is already in target (should be skipped)
        # Record 2 is new and valid (should be imported)
        # Record 3 is malformed missing predictedClass (should fail validation)
        sample_records = [
            {
                "id": "REC-EXISTING-001",
                "predictedClass": "paper",
                "wasteType": "Recyclable / Dry Waste",
                "confidence": 91.0
            },
            {
                "id": "REC-NEW-002",
                "predictedClass": "glass",
                "wasteType": "Recyclable / Dry Waste",
                "confidence": 89.0
            },
            {
                "id": "REC-INVALID-003",
                # missing predictedClass
                "wasteType": "Unknown",
                "confidence": 0.0
            }
        ]

        with open(self.test_json_file, "w", encoding="utf-8") as f:
            json.dump(sample_records, f)

        # Configure mock_target: get_record returns doc for REC-EXISTING-001, None for REC-NEW-002
        def mock_get(rec_id):
            if rec_id == "REC-EXISTING-001":
                return {"id": "REC-EXISTING-001"}
            return None

        mock_target.get_record.side_effect = mock_get

        migration = MigrationService(target_provider=mock_target)

        # 1. Test Dry Run
        dry_result = migration.migrate_from_file(self.test_json_file, dry_run=True)
        self.assertEqual(dry_result["total_found"], 3)
        self.assertEqual(dry_result["skipped"], 1)
        self.assertEqual(dry_result["imported"], 1)  # Simulated import
        self.assertEqual(dry_result["failed"], 1)
        mock_target.save_record.assert_not_called()

        # 2. Test Live Migration
        live_result = migration.migrate_from_file(self.test_json_file, dry_run=False)
        self.assertEqual(live_result["total_found"], 3)
        self.assertEqual(live_result["skipped"], 1)
        self.assertEqual(live_result["imported"], 1)
        self.assertEqual(live_result["failed"], 1)
        mock_target.save_record.assert_called_once()

        # Verify source file is completely intact
        self.assertTrue(os.path.exists(self.test_json_file))
        with open(self.test_json_file, "r", encoding="utf-8") as f:
            persisted = json.load(f)
        self.assertEqual(len(persisted), 3)

    def test_07_image_storage_service_policy(self):
        """Verifies private GCS image storage policy adheres to zero-retention defaults."""
        service = GoogleCloudImageStorageService()
        self.assertFalse(service.enabled)

        # 1. Under default zero-retention posture, upload returns None
        gcs_uri = service.upload_audit_image("REC-123", b"dummy image bytes")
        self.assertIsNone(gcs_uri)

        # 2. Validation strictly enforces MIME type and size limits
        valid, err = service.validate_image_payload(b"valid bytes", "image/jpeg")
        self.assertTrue(valid)
        self.assertIsNone(err)

        # Reject unsupported MIME type
        valid, err = service.validate_image_payload(b"valid bytes", "application/pdf")
        self.assertFalse(valid)
        self.assertIn("Unsupported MIME type", err)

        # Reject oversized payload
        oversized_bytes = b"0" * (11 * 1024 * 1024)
        valid, err = service.validate_image_payload(oversized_bytes, "image/jpeg")
        self.assertFalse(valid)
        self.assertIn("exceeds maximum limit", err)

    def test_08_storage_status_schema_completeness(self):
        """Verifies that storage_service get_status() returns all required schema attributes."""
        provider = LocalStorageProvider(storage_file=self.test_json_file)
        status = provider.get_status()

        expected_keys = [
            "mode",
            "storage_backend",
            "persistent_cloud_enabled",
            "cloud_provider",
            "record_count",
            "idempotency_enabled",
            "notes"
        ]
        for key in expected_keys:
            self.assertIn(key, status, f"Missing key '{key}' in storage status dictionary.")


if __name__ == "__main__":
    unittest.main()
