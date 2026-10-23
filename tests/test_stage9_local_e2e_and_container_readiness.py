"""
SMART ECO BIN — Stage 9 Local End-to-End & Container Readiness Test Suite
========================================================================
Validates the actual running FastAPI application, MobileNetV2 12-class
classifier, software segregation simulation, privacy lifecycle, boundary
protections, and local Firebase Emulator integration guardrails.

Testing Categories & Boundaries:
- Local Application E2E: Real model inference, real HTTP request/response cycle.
- Privacy & Persistence: Zero image byte retention, metadata-only storage.
- Boundary Safety: Corrupted image handling, unsupported MIME types, oversized payloads.
- Rate Limiting: Per-instance concurrency guard (30 req/min).
- Emulator Guardrails: Rejection in production/staging; safe verification in dev.
"""

import os
import io
import time
import json
import base64
import unittest
from unittest.mock import patch, MagicMock
import jwt
from PIL import Image
from fastapi.testclient import TestClient

# Local test environment setup
os.environ["ENVIRONMENT"] = "development"
os.environ["ALLOW_DEV_AUTH"] = "true"
os.environ["STORAGE_PROVIDER"] = "local"

from main import app
from app.auth.config import SecurityConfig, SecurityConfigurationError, security_config
from app.auth.security import TokenVerifier, token_verifier, AuthenticationError
from app.auth.models import UserRole
from app.services.storage_service import storage_service
from app.services.model_service import classifier_service
from app.routes.predict import clear_rate_limits


def make_mock_rs256_token(header_dict, payload_dict):
    """Constructs a valid base64url-encoded RS256 token structure for test routing."""
    hdr = base64.urlsafe_b64encode(json.dumps(header_dict).encode()).decode().rstrip("=")
    pay = base64.urlsafe_b64encode(json.dumps(payload_dict).encode()).decode().rstrip("=")
    sig = base64.urlsafe_b64encode(b"simulated_asymmetric_rsa_signature_256").decode().rstrip("=")
    return f"{hdr}.{pay}.{sig}"


class TestStage9LocalE2EAndContainerReadiness(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

        # Generate a valid 224x224 RGB test image (JPEG) for genuine MobileNetV2 inference
        img = Image.new("RGB", (224, 224), color=(60, 140, 200))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        cls.valid_image_bytes = buf.getvalue()

    def setUp(self):
        clear_rate_limits()
        security_config.reload()
        token_verifier._init_firebase_admin()

    def tearDown(self):
        clear_rate_limits()
        security_config.reload()
        token_verifier._init_firebase_admin()

    # --------------------------------------------------------------------------
    # 1. Emulator guardrails: forbidden in production
    # --------------------------------------------------------------------------
    def test_01_emulator_configuration_forbidden_in_production(self):
        """Setting FIREBASE_AUTH_EMULATOR_HOST in production immediately fails closed."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "ALLOW_DEV_AUTH": "false",
            "AUTH_PROVIDER": "firebase",
            "GOOGLE_CLOUD_PROJECT": "prod-smart-eco-bin",
            "ADMIN_EMAILS": "admin@sanitation.gov",
            "FIREBASE_AUTH_EMULATOR_HOST": "127.0.0.1:9099"
        }):
            cfg = SecurityConfig.__new__(SecurityConfig)
            with self.assertRaises(SecurityConfigurationError) as ctx:
                cfg.reload()
            self.assertIn("FIREBASE_AUTH_EMULATOR_HOST", str(ctx.exception))
            self.assertIn("production", str(ctx.exception).lower())

    # --------------------------------------------------------------------------
    # 2. Emulator guardrails: forbidden in staging
    # --------------------------------------------------------------------------
    def test_02_emulator_configuration_forbidden_in_staging(self):
        """Setting FIREBASE_AUTH_EMULATOR_HOST in staging immediately fails closed."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "staging",
            "ALLOW_DEV_AUTH": "false",
            "AUTH_PROVIDER": "firebase",
            "GOOGLE_CLOUD_PROJECT": "staging-smart-eco-bin",
            "ADMIN_EMAILS": "admin@sanitation.gov",
            "FIREBASE_AUTH_EMULATOR_HOST": "127.0.0.1:9099"
        }):
            cfg = SecurityConfig.__new__(SecurityConfig)
            with self.assertRaises(SecurityConfigurationError) as ctx:
                cfg.reload()
            self.assertIn("FIREBASE_AUTH_EMULATOR_HOST", str(ctx.exception))
            self.assertIn("staging", str(ctx.exception).lower())

    # --------------------------------------------------------------------------
    # 3. Emulator guardrails: permitted in local development
    # --------------------------------------------------------------------------
    def test_03_emulator_configuration_permitted_in_development(self):
        """Setting FIREBASE_AUTH_EMULATOR_HOST in development reloads successfully."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "ALLOW_DEV_AUTH": "true",
            "AUTH_PROVIDER": "firebase",
            "GOOGLE_CLOUD_PROJECT": "demo-smart-eco-bin",
            "FIREBASE_AUTH_EMULATOR_HOST": "127.0.0.1:9099"
        }):
            cfg = SecurityConfig.__new__(SecurityConfig)
            cfg.reload()
            self.assertEqual(cfg.firebase_auth_emulator_host, "127.0.0.1:9099")

    # --------------------------------------------------------------------------
    # 4. E2E Health, Diagnostics & Posture Probes
    # --------------------------------------------------------------------------
    def test_04_e2e_health_and_telemetry_probes(self):
        """Health and diagnostics endpoints report genuine state and sanitize paths."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["model_loaded"])
        self.assertEqual(data["mode"], "Software-Only (Pure Computational Intelligence)")
        self.assertFalse(data["hardware_sensors"])

        # Storage status check
        resp_storage = self.client.get("/api/storage/status")
        self.assertEqual(resp_storage.status_code, 200)
        storage_data = resp_storage.json()
        # Verify no absolute OS path leaked (no Windows drive letter or backslashes)
        file_path = storage_data.get("storage_file") or ""
        self.assertNotIn(":", file_path)
        self.assertNotIn("\\", file_path)

        # Security posture check
        resp_posture = self.client.get("/api/security/posture")
        self.assertEqual(resp_posture.status_code, 200)
        posture_data = resp_posture.json()
        self.assertIn("admin_auth_mode", posture_data)
        self.assertIn("rbac_enforced", posture_data)
        self.assertIn("citizen_privacy_zero_retention", posture_data)
        # Ensure private keys / secrets are NOT exposed
        self.assertNotIn("secret", posture_data)
        self.assertNotIn("dev_secret", posture_data)

    # --------------------------------------------------------------------------
    # 5. E2E Real MobileNetV2 Inference and Software Segregation
    # --------------------------------------------------------------------------
    def test_05_e2e_real_mobilenetv2_inference_and_segregation(self):
        """Authentic image bytes process through real MobileNetV2 returning 12-class prediction."""
        valid_classes = {
            "battery", "biological", "brown-glass", "cardboard", "clothes",
            "green-glass", "metal", "paper", "plastic", "shoes", "trash", "white-glass"
        }
        files = {"file": ("test_intake.jpg", self.valid_image_bytes, "image/jpeg")}
        resp = self.client.post("/api/predict", files=files)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertIn(data["predictedClass"], valid_classes)
        self.assertIsInstance(data["confidence"], (int, float))
        self.assertGreaterEqual(data["confidence"], 0.0)
        self.assertLessEqual(data["confidence"], 100.0)
        self.assertIn("disposalBin", data)
        self.assertIn("destinationCompartment", data)
        self.assertIn(data.get("simulationStatus"), ("READY", "SIMULATED"))

    # --------------------------------------------------------------------------
    # 6. E2E Zero Image Byte Retention
    # --------------------------------------------------------------------------
    def test_06_e2e_zero_byte_retention(self):
        """Classification records persist metadata only, never raw image bytes or file paths."""
        files = {"file": ("privacy_test.jpg", self.valid_image_bytes, "image/jpeg")}
        resp = self.client.post("/api/predict", files=files)
        self.assertEqual(resp.status_code, 200)

        records = storage_service.list_records(limit=1)
        self.assertGreater(len(records), 0)
        latest = records[0]
        self.assertNotIn("imageBytes", latest)
        self.assertNotIn("rawImage", latest)
        self.assertNotIn("fileData", latest)
        self.assertIsNone(latest.get("imageUrl"))

    # --------------------------------------------------------------------------
    # 7. E2E Boundary: Unsupported File MIME Types
    # --------------------------------------------------------------------------
    def test_07_e2e_intake_boundary_invalid_file_types(self):
        """Intake rejects non-image MIME types with HTTP 400."""
        text_data = b"This is plain text data, not a valid image."
        files = {"file": ("document.txt", text_data, "text/plain")}
        resp = self.client.post("/api/predict", files=files)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid image type", resp.json()["detail"])

    # --------------------------------------------------------------------------
    # 8. E2E Boundary: Corrupted Image Bytes
    # --------------------------------------------------------------------------
    def test_08_e2e_intake_boundary_corrupted_image(self):
        """Corrupted image payload claiming to be JPEG returns HTTP 400."""
        corrupted_bytes = b"\xFF\xD8\xFF\xE0" + b"CORRUPTED_GARBAGE_PAYLOAD_NOT_A_VALID_IMAGE"
        files = {"file": ("corrupt.jpg", corrupted_bytes, "image/jpeg")}
        resp = self.client.post("/api/predict", files=files)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid image format", resp.json()["detail"])

    # --------------------------------------------------------------------------
    # 9. E2E Boundary: Oversized Image Payloads (> 10MB)
    # --------------------------------------------------------------------------
    def test_09_e2e_intake_boundary_oversized_payload(self):
        """Image payloads exceeding 10MB are rejected with HTTP 400."""
        oversized_bytes = b"0" * (10 * 1024 * 1024 + 1024)  # 10MB + 1KB
        files = {"file": ("large.jpg", oversized_bytes, "image/jpeg")}
        resp = self.client.post("/api/predict", files=files)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("exceeds 10MB", resp.json()["detail"])

    # --------------------------------------------------------------------------
    # 10. E2E Rate Limiting Enforcement & Reset
    # --------------------------------------------------------------------------
    def test_10_e2e_rate_limiting_enforcement_and_recovery(self):
        """Per-client rate limit enforces 30 req/min cap and recovers after reset."""
        files = {"file": ("rate_test.jpg", self.valid_image_bytes, "image/jpeg")}

        # Rapidly execute 30 calls
        for i in range(30):
            r = self.client.post("/api/predict", files=files)
            self.assertEqual(r.status_code, 200, f"Request {i+1} should succeed")

        # 31st call must trigger HTTP 429
        r_blocked = self.client.post("/api/predict", files=files)
        self.assertEqual(r_blocked.status_code, 429)
        self.assertIn("Rate limit exceeded", r_blocked.json()["detail"])

        # Reset rate limits and verify immediate recovery
        clear_rate_limits()
        r_recovered = self.client.post("/api/predict", files=files)
        self.assertEqual(r_recovered.status_code, 200)

    # --------------------------------------------------------------------------
    # 11. E2E Idempotency Key Handling
    # --------------------------------------------------------------------------
    def test_11_e2e_idempotency_handling(self):
        """Submitting with identical X-Idempotency-Key returns original record without duplication."""
        idempotency_key = f"IDEM-STAGE9-{int(time.time())}"
        files1 = {"file": ("idem1.jpg", self.valid_image_bytes, "image/jpeg")}
        headers = {"X-Idempotency-Key": idempotency_key}

        initial_count = storage_service.count_records()

        resp1 = self.client.post("/api/predict", files=files1, headers=headers)
        self.assertEqual(resp1.status_code, 200)
        count_after_first = storage_service.count_records()
        self.assertEqual(count_after_first, initial_count + 1)

        # Second request with same idempotency key
        files2 = {"file": ("idem2.jpg", self.valid_image_bytes, "image/jpeg")}
        resp2 = self.client.post("/api/predict", files=files2, headers=headers)
        self.assertEqual(resp2.status_code, 200)
        count_after_second = storage_service.count_records()
        self.assertEqual(count_after_second, count_after_first)

    # --------------------------------------------------------------------------
    # 12. Local Emulator Flow: Citizen Access & Strict History Isolation
    # --------------------------------------------------------------------------
    def test_12_emulator_flow_citizen_access_and_isolation(self):
        """Simulated emulator citizen token authenticates and strictly isolates citizen records."""
        citizen_token = make_mock_rs256_token(
            {"alg": "RS256", "kid": "emulator-key-1"},
            {"uid": "emu-citizen-001", "email": "citizen@test.local", "email_verified": True}
        )

        with patch.object(token_verifier, "_firebase_available", True):
            with patch("firebase_admin.auth.verify_id_token", return_value={
                "uid": "emu-citizen-001",
                "email": "citizen@test.local",
                "email_verified": True
            }):
                # 1. Profile retrieval
                resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {citizen_token}"})
                self.assertEqual(resp.status_code, 200)
                user_info = resp.json()
                self.assertEqual(user_info["uid"], "emu-citizen-001")
                self.assertEqual(user_info["role"], "citizen")

                # 2. Intake prediction creates record owned by emu-citizen-001
                files = {"file": ("citizen_waste.jpg", self.valid_image_bytes, "image/jpeg")}
                resp_pred = self.client.post("/api/predict", files=files, headers={"Authorization": f"Bearer {citizen_token}"})
                self.assertEqual(resp_pred.status_code, 200)

                # Query history as this citizen
                resp_hist = self.client.get("/api/history", headers={"Authorization": f"Bearer {citizen_token}"})
                self.assertEqual(resp_hist.status_code, 200)
                records = resp_hist.json()
                self.assertGreater(len(records), 0)
                for r in records:
                    self.assertEqual(r.get("userId"), "emu-citizen-001")

        # 3. Another citizen requests history and cannot see emu-citizen-001's records
        citizen_b_token = make_mock_rs256_token(
            {"alg": "RS256", "kid": "emulator-key-1"},
            {"uid": "emu-citizen-002", "email": "other@test.local", "email_verified": True}
        )
        with patch.object(token_verifier, "_firebase_available", True):
            with patch("firebase_admin.auth.verify_id_token", return_value={
                "uid": "emu-citizen-002",
                "email": "other@test.local",
                "email_verified": True
            }):
                resp_b = self.client.get("/api/history", headers={"Authorization": f"Bearer {citizen_b_token}"})
                self.assertEqual(resp_b.status_code, 200)
                records_b = resp_b.json()
                for r in records_b:
                    self.assertNotEqual(r.get("userId"), "emu-citizen-001")

    # --------------------------------------------------------------------------
    # 13. Local Emulator Flow: Admin Role Enforcement & Unverified Email Guard
    # --------------------------------------------------------------------------
    def test_13_emulator_flow_admin_and_unverified_email_guard(self):
        """Admin endpoints strictly enforce verified email or custom claim on emulator tokens."""
        with patch.object(security_config, "admin_emails", {"admin@sanitation.gov"}):
            # Case A: Attacker with unverified email matching admin address
            attacker_token = make_mock_rs256_token(
                {"alg": "RS256", "kid": "emulator-key-1"},
                {"uid": "attacker-999", "email": "admin@sanitation.gov", "email_verified": False}
            )
            with patch.object(token_verifier, "_firebase_available", True):
                with patch("firebase_admin.auth.verify_id_token", return_value={
                    "uid": "attacker-999",
                    "email": "admin@sanitation.gov",
                    "email_verified": False
                }):
                    resp = self.client.get("/api/sanitation", headers={"Authorization": f"Bearer {attacker_token}"})
                    self.assertEqual(resp.status_code, 403)

            # Case B: Verified administrator
            admin_token = make_mock_rs256_token(
                {"alg": "RS256", "kid": "emulator-key-1"},
                {"uid": "admin-verified-001", "email": "admin@sanitation.gov", "email_verified": True}
            )
            with patch.object(token_verifier, "_firebase_available", True):
                with patch("firebase_admin.auth.verify_id_token", return_value={
                    "uid": "admin-verified-001",
                    "email": "admin@sanitation.gov",
                    "email_verified": True
                }):
                    resp_admin = self.client.get("/api/sanitation", headers={"Authorization": f"Bearer {admin_token}"})
                    self.assertEqual(resp_admin.status_code, 200)

                    resp_anom = self.client.get("/api/anomalies", headers={"Authorization": f"Bearer {admin_token}"})
                    self.assertEqual(resp_anom.status_code, 200)

    # --------------------------------------------------------------------------
    # 14. Local Emulator Flow: Revoked Tokens & Zero HMAC Fallback
    # --------------------------------------------------------------------------
    def test_14_emulator_flow_revoked_tokens_and_zero_fallback(self):
        """Revoked emulator tokens return HTTP 401 and never fallback to HMAC."""
        token = make_mock_rs256_token(
            {"alg": "RS256", "kid": "emulator-key-1"},
            {"uid": "revoked-user", "email": "user@test.local", "email_verified": True}
        )

        import firebase_admin.auth
        with patch.object(token_verifier, "_firebase_available", True):
            with patch("firebase_admin.auth.verify_id_token", side_effect=firebase_admin.auth.RevokedIdTokenError("Token revoked")):
                resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
                self.assertEqual(resp.status_code, 401)
                self.assertIn("revoked", resp.json()["detail"].lower())

        # Test HMAC token rejection when auth provider is firebase
        with patch.object(security_config, "auth_provider", "firebase"):
            hmac_token = jwt.encode(
                {"sub": "attacker", "role": "administrator"},
                "smart-eco-bin-local-dev-secret-key-32b",
                algorithm="HS256"
            )
            resp_hmac = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {hmac_token}"})
            self.assertEqual(resp_hmac.status_code, 401)


if __name__ == "__main__":
    unittest.main()
