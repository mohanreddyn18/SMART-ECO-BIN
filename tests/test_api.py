import io
import os
import sys
import unittest
from unittest.mock import AsyncMock, patch
from PIL import Image
from fastapi.testclient import TestClient

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import main
from app.routes.ai import clear_gemini_rate_limits


class TestEcoSortAPI(unittest.TestCase):
    """Automated integration tests for FastAPI REST API endpoints."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("ENVIRONMENT", "development")
        os.environ.setdefault("ALLOW_DEV_AUTH", "true")
        os.environ.pop("ADMIN_EMAILS", None)
        from app.auth.config import security_config
        security_config.reload()
        from app.auth.security import token_verifier
        token, _ = token_verifier.issue_dev_token("admin@ecosortai.com", role="administrator")
        cls.client = TestClient(main.app, headers={"Authorization": f"Bearer {token}"})

    def setUp(self):
        clear_gemini_rate_limits()

    def test_health_endpoint(self):
        """GET /health must return 200 OK with health status and software-only declaration."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn(data["status"], ["healthy", "degraded"])
        self.assertIn("service", data)
        self.assertEqual(data.get("hardware_sensors"), False)
        self.assertIn("model_loaded", data)

    def test_root_endpoint(self):
        """GET / must return 200 OK with project metadata and endpoint listing."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "online")
        self.assertIn("endpoints", data)
        self.assertIn("predict", data["endpoints"])
        self.assertIn("history", data["endpoints"])
        self.assertIn("analytics", data["endpoints"])

    def test_history_endpoint(self):
        """GET /api/history must return 200 OK with list of records."""
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if len(data) > 0:
            rec = data[0]
            self.assertIn("id", rec)
            self.assertIn("predictedClass", rec)
            self.assertIn("wasteType", rec)
            self.assertIn("confidence", rec)

    def test_analytics_endpoint(self):
        """GET /api/analytics must return 200 OK with macro statistics and distribution."""
        response = self.client.get("/api/analytics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("totalClassifications", data)
        self.assertIsInstance(data["totalClassifications"], int)
        self.assertIn("distribution", data)
        self.assertIn("labels", data["distribution"])
        self.assertIn("counts", data["distribution"])

    def test_sanitation_endpoint(self):
        """GET /api/sanitation must return 200 OK with computed posture and indicators."""
        response = self.client.get("/api/sanitation")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("currentStatus", data)
        self.assertIn(data["currentStatus"], ["GOOD", "ATTENTION REQUIRED", "CRITICAL", "UNAVAILABLE"])
        self.assertIn("supportingIndicators", data)
        self.assertIsInstance(data["supportingIndicators"], list)

    def test_storage_status_endpoint(self):
        """GET /api/storage/status must return operational mode and cloud readiness details."""
        response = self.client.get("/api/storage/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("mode", data)
        self.assertEqual(data["mode"], "development_emulation")
        self.assertIn("storage_backend", data)
        self.assertIn("persistent_cloud_enabled", data)
        self.assertEqual(data["persistent_cloud_enabled"], False)

    def test_anomalies_endpoint(self):
        """GET /api/anomalies must return 200 OK with anomaly list."""
        response = self.client.get("/api/anomalies")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("totalAnomalies", data)
        self.assertIn("anomalies", data)
        self.assertIsInstance(data["anomalies"], list)

    def test_predictive_insights_endpoint(self):
        """GET /api/predictive-insights must return 200 OK and data sufficiency status."""
        response = self.client.get("/api/predictive-insights")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("sufficientData", data)
        self.assertIsInstance(data["sufficientData"], bool)
        self.assertIn("message", data)

    def test_predict_endpoint_valid_image(self):
        """POST /api/predict must process a valid JPEG image and return a classification."""
        img = Image.new("RGB", (224, 224), color=(60, 100, 140))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        response = self.client.post(
            "/api/predict",
            files={"file": ("test_sample.jpg", buf, "image/jpeg")}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("predictedClass", data)
        self.assertIn("confidence", data)
        self.assertIn("wasteType", data)
        self.assertIn("recommendation", data)
        self.assertIn("disposalBin", data)
        self.assertIn("timestamp", data)
        self.assertIsInstance(data["confidence"], (int, float))

    def test_predict_endpoint_invalid_file_type(self):
        """POST /api/predict must reject non-image file uploads with HTTP 400."""
        text_file = io.BytesIO(b"Hello waste classification")
        response = self.client.post(
            "/api/predict",
            files={"file": ("document.txt", text_file, "text/plain")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid image type", response.json()["detail"])

    def test_predict_endpoint_corrupted_image(self):
        """POST /api/predict must reject corrupted image content."""
        corrupted = io.BytesIO(b"\xff\xd8\xff\xe0not-a-valid-jpeg-body")
        response = self.client.post(
            "/api/predict",
            files={"file": ("corrupt.jpg", corrupted, "image/jpeg")}
        )
        self.assertIn(response.status_code, [400, 422])

    def test_wasteai_endpoint(self):
        """POST /api/wasteai returns a generated answer when Gemini is configured."""
        with patch(
            "app.routes.ai.gemini_service.query_waste_ai",
            new_callable=AsyncMock,
            return_value="Use a designated battery collection point.",
        ):
            response = self.client.post(
                "/api/wasteai",
                json={"prompt": "How do I safely recycle lithium batteries?"}
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("reply", data)
        self.assertIn("source", data)
        self.assertTrue(len(data["reply"]) > 0)

    def test_wasteai_explains_classifier_metadata_without_uploading_an_image(self):
        classification = {
            "predicted_class": "battery",
            "confidence": 92.5,
            "waste_type": "Hazardous / E-Waste",
            "recommendation": "Keep isolated and use a battery collection point.",
            "disposal_bin": "Hazardous Waste Depot",
            "requires_manual_review": True,
        }
        with patch(
            "app.routes.ai.gemini_service.query_waste_ai",
            new_callable=AsyncMock,
            return_value="The classifier identified a battery.",
        ) as query:
            response = self.client.post(
                "/api/wasteai",
                json={
                    "prompt": "Explain this classifier result.",
                    "classification_result": classification,
                },
            )

        self.assertEqual(response.status_code, 200)
        query.assert_awaited_once_with(
            "Explain this classifier result.",
            classification,
        )

    def test_wasteai_rate_limit_is_enforced(self):
        with patch(
            "app.routes.ai.gemini_service.query_waste_ai",
            new_callable=AsyncMock,
            return_value="Use a designated battery collection point.",
        ):
            for _ in range(10):
                response = self.client.post(
                    "/api/wasteai",
                    json={"prompt": "How do I recycle a battery?"},
                )
                self.assertEqual(response.status_code, 200)

            limited = self.client.post(
                "/api/wasteai",
                json={"prompt": "How do I recycle a battery?"},
            )

        self.assertEqual(limited.status_code, 429)

    def test_wasteai_unavailable_without_gemini_does_not_fake_a_response(self):
        with patch("app.routes.ai.gemini_service.client", None):
            response = self.client.post(
                "/api/wasteai",
                json={"prompt": "What is the current recycling policy?"},
            )
        self.assertEqual(response.status_code, 503)
        self.assertIn("not configured", response.json()["detail"])

    def test_sanitationai_endpoint(self):
        """POST /api/sanitationai returns a generated telemetry-grounded answer."""
        with patch(
            "app.routes.ai.gemini_service.query_sanitation_ai",
            new_callable=AsyncMock,
            return_value={"reply": "The stored sanitation assessment is unavailable.", "function_called": "get_sanitation_status()", "telemetry_grounded": True},
        ):
            response = self.client.post(
                "/api/sanitationai",
                json={"prompt": "What is the overall sanitation status?"}
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("reply", data)
        self.assertTrue(data.get("telemetry_grounded"))
        self.assertTrue(len(data["reply"]) > 0)


if __name__ == "__main__":
    unittest.main()
