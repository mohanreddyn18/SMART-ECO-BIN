import io
import os
import sys
import unittest
from PIL import Image
from fastapi.testclient import TestClient

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import main
from app.services.storage_service import storage_service, LocalStorageProvider
from app.services.analytics_service import analytics_service


class TestStage3StorageAndDataflow(unittest.TestCase):
    """
    Automated tests verifying Stage 3 storage abstraction, dynamic dataflow,
    idempotency safeguards, and honest empty/insufficient telemetry states.
    """

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("ENVIRONMENT", "development")
        os.environ.setdefault("ALLOW_DEV_AUTH", "true")
        from app.auth.config import security_config
        security_config.reload()
        from app.auth.security import token_verifier
        token, _ = token_verifier.issue_dev_token("admin@ecosortai.com", role="administrator")
        cls.client = TestClient(main.app, headers={"Authorization": f"Bearer {token}"})

    def setUp(self):
        # Save existing records snapshot before test
        self._saved_records = storage_service.list_records(limit=1000)

    def tearDown(self):
        # Restore storage state after test
        storage_service.clear_records()
        for rec in reversed(self._saved_records):
            storage_service.save_record(rec)

    def test_01_create_and_retrieve_event_with_consistent_schema(self):
        """A valid classification event can be created and retrieved from history with consistent fields."""
        img = Image.new("RGB", (224, 224), color=(30, 80, 160))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        response = self.client.post(
            "/api/predict",
            files={"file": ("glass_bottle.jpg", buf, "image/jpeg")}
        )
        self.assertEqual(response.status_code, 200)
        prediction = response.json()

        # Check required Stage 2 & 3 schema
        self.assertIn("predictedClass", prediction)
        self.assertIn("destinationCompartment", prediction)
        self.assertIn("compartmentId", prediction)
        self.assertIn("routingStatus", prediction)
        self.assertIn("simulationStatus", prediction)

        # Retrieve history
        hist_response = self.client.get("/api/history?limit=10")
        self.assertEqual(hist_response.status_code, 200)
        history = hist_response.json()
        self.assertTrue(len(history) > 0)

        latest = history[0]
        self.assertEqual(latest["predictedClass"], prediction["predictedClass"])
        self.assertEqual(latest["destinationCompartment"], prediction["destinationCompartment"])
        self.assertEqual(latest["compartmentId"], prediction["compartmentId"])
        self.assertEqual(latest["routingStatus"], prediction["routingStatus"])

        # Retrieve single record by ID
        single_res = self.client.get(f"/api/history/{latest['id']}")
        self.assertEqual(single_res.status_code, 200)
        self.assertEqual(single_res.json()["id"], latest["id"])

    def test_02_idempotency_prevents_duplicate_records(self):
        """Duplicate submissions with identical idempotency key do not create duplicate events."""
        img = Image.new("RGB", (224, 224), color=(100, 150, 200))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        idempotency_key = "IDEMPOTENT-TEST-KEY-001"

        # First submission
        buf.seek(0)
        res1 = self.client.post(
            "/api/predict",
            files={"file": ("sample.jpg", buf, "image/jpeg")},
            headers={"X-Idempotency-Key": idempotency_key}
        )
        self.assertEqual(res1.status_code, 200)
        count_after_first = storage_service.count_records()

        # Second submission with identical key
        buf.seek(0)
        res2 = self.client.post(
            "/api/predict",
            files={"file": ("sample.jpg", buf, "image/jpeg")},
            headers={"X-Idempotency-Key": idempotency_key}
        )
        self.assertEqual(res2.status_code, 200)
        count_after_second = storage_service.count_records()

        # Count must NOT have increased
        self.assertEqual(count_after_first, count_after_second, "Duplicate submission with same idempotency key must not create a new record")

    def test_03_empty_dataset_returns_valid_response_without_fabricated_records(self):
        """When the event store is cleared, analytics reports zero without fabricating data."""
        storage_service.clear_records()
        self.assertEqual(storage_service.count_records(), 0)

        # Analytics endpoint
        analytics_res = self.client.get("/api/analytics")
        self.assertEqual(analytics_res.status_code, 200)
        analytics = analytics_res.json()

        self.assertEqual(analytics["totalClassifications"], 0)
        self.assertEqual(analytics["distribution"]["labels"], [])
        self.assertEqual(analytics["distribution"]["counts"], [])
        self.assertEqual(analytics["weeklyTrends"]["daily"], [])
        self.assertEqual(analytics["averageConfidence"], 0.0)

        # History endpoint
        history_res = self.client.get("/api/history")
        self.assertEqual(history_res.status_code, 200)
        self.assertEqual(history_res.json(), [])

    def test_04_sanitation_honest_state_on_empty_and_populated_data(self):
        """Sanitation returns UNAVAILABLE when empty, and calculated indicators when populated."""
        # Test empty state
        storage_service.clear_records()
        res_empty = self.client.get("/api/sanitation")
        self.assertEqual(res_empty.status_code, 200)
        data_empty = res_empty.json()
        self.assertEqual(data_empty["currentStatus"], "UNAVAILABLE")
        self.assertEqual(data_empty["hardwareSensors"], False)
        self.assertEqual(data_empty["supportingIndicators"], [])

        # Add a record and test populated state
        sample_rec = {
            "id": "REC-TEST-SANITATION-001",
            "predictedClass": "plastic",
            "wasteType": "Recyclable / Dry Waste",
            "confidence": 95.0,
            "recommendation": "Recycle plastic container.",
            "destinationCompartment": "Blue Plastic Recycling Bin",
            "compartmentId": "bin_plastic",
            "routingStatus": "AUTOMATED_ROUTED",
            "requiresManualReview": False,
            "timestamp": "2026-10-20T10:00:00Z"
        }
        storage_service.save_record(sample_rec)

        res_populated = self.client.get("/api/sanitation")
        self.assertEqual(res_populated.status_code, 200)
        data_pop = res_populated.json()
        self.assertIn(data_pop["currentStatus"], ["GOOD", "ATTENTION REQUIRED"])
        self.assertEqual(data_pop["hardwareSensors"], False)
        self.assertTrue(len(data_pop["supportingIndicators"]) > 0)

    def test_05_anomalies_honest_state_on_insufficient_data(self):
        """Anomaly detection reports 'Awaiting Telemetry' when records < 10."""
        storage_service.clear_records()
        res = self.client.get("/api/anomalies")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "Awaiting Telemetry")
        self.assertEqual(data["totalAnomalies"], 0)
        self.assertIn("Insufficient historical observations", data["message"])

    def test_06_anomaly_alerts_use_actual_record_thresholds_without_sensor_claims(self):
        storage_service.clear_records()
        for index in range(20):
            storage_service.save_record({
                "id": f"REC-ANOMALY-{index:02d}",
                "compartmentId": "bin_hazardous" if index < 4 else "bin_residual",
                "confidence": 45.0 if index < 3 else 90.0,
                "timestamp": "2026-10-20T10:00:00Z",
            })

        response = self.client.get("/api/anomalies")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["algorithm"], "Rule-based checks on recent classification records")
        self.assertEqual(data["totalAnomalies"], 2)
        self.assertIn("20%", data["anomalies"][0]["reason"])
        self.assertIn("Not recorded", data["anomalies"][0]["location"])
        self.assertNotIn("sensor", data["anomalies"][0]["recommendation"].lower())

    def test_07_predictive_insights_threshold_enforcement(self):
        """Predictive insights honestly reports insufficient data when count < threshold."""
        storage_service.clear_records()
        res = self.client.get("/api/predictive-insights")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["sufficientData"])
        self.assertIsNone(data["projections"])
        self.assertIn("Insufficient historical telemetry", data["message"])

    def test_07_storage_status_endpoint_reports_dev_emulation(self):
        """Storage status endpoint accurately describes development emulation mode."""
        res = self.client.get("/api/storage/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["mode"], "development_emulation")
        self.assertFalse(data["persistent_cloud_enabled"])
        self.assertTrue(data["idempotency_enabled"])
        self.assertIn("LocalStorageProvider", data["storage_backend"])


if __name__ == "__main__":
    unittest.main()
