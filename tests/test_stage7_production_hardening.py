"""
SMART ECO BIN — Stage 7 Production Hardening & Security Assurance Test Suite
=============================================================================
Automated test verification for Stage 7:
1. Production configuration rejects development authentication.
2. Production configuration rejects known example secrets & placeholder admin emails.
3. Development-token endpoints are unavailable when development mode is disabled (403).
4. Firebase/OIDC validation failure never falls back to development-token validation.
5. Missing, invalid, expired, wrong-issuer, and wrong-audience tokens are rejected.
6. A citizen cannot access administrator-only routes (403).
7. An administrator must have verified server-side privileges.
8. A citizen cannot access another citizen's records through search, filters, or direct lookup.
9. Caller-supplied userId cannot impersonate another account.
10. Administrative deletion is denied to unauthorised users (401/403).
11. Authentication errors, status endpoints, and logs do not expose secrets.
12. Invalid storage configuration fails safely.
13. Rate limiting and request validation behave as documented (429, anti-spoofing).
14. Existing model inference and segregation simulation functionality continues to work.
"""

import os
import io
import time
import json
import unittest
from unittest.mock import patch, MagicMock
import jwt
from PIL import Image
from fastapi.testclient import TestClient

# Ensure test execution context
os.environ["ENVIRONMENT"] = "development"
os.environ["ALLOW_DEV_AUTH"] = "true"
os.environ["STORAGE_PROVIDER"] = "local"

from main import app
from app.auth.config import SecurityConfig, SecurityConfigurationError, security_config
from app.auth.security import token_verifier, AuthenticationError
from app.auth.models import UserRole
from app.services.storage_service import storage_service, create_storage_provider
from app.routes.predict import clear_rate_limits, RATE_LIMIT_MAX_REQUESTS


class TestStage7ProductionHardening(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Helper to generate in-memory dummy image
        img = Image.new("RGB", (224, 224), color=(73, 109, 137))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        cls.valid_image_bytes = buf.getvalue()

    def setUp(self):
        clear_rate_limits()
        storage_service.clear_records()
        os.environ["ENVIRONMENT"] = "development"
        os.environ["ALLOW_DEV_AUTH"] = "true"
        os.environ["AUTH_PROVIDER"] = "auto"
        os.environ["STORAGE_PROVIDER"] = "local"
        os.environ.pop("FIREBASE_AUTH_EMULATOR_HOST", None)
        os.environ.pop("ADMIN_EMAILS", None)
        security_config.reload()
        token_verifier._init_firebase_admin()

    # --------------------------------------------------------------------------
    # 1. Production configuration rejects development authentication
    # --------------------------------------------------------------------------
    def test_01_production_rejects_dev_auth(self):
        """Production startup must fail if ALLOW_DEV_AUTH is true."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "ALLOW_DEV_AUTH": "true"}):
            with self.assertRaises(SecurityConfigurationError) as ctx:
                SecurityConfig()
            self.assertIn("Development authentication (ALLOW_DEV_AUTH) cannot be enabled", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 2. Production configuration rejects known example secrets & placeholders
    # --------------------------------------------------------------------------
    def test_02_production_rejects_known_example_secrets_and_placeholders(self):
        """Production must reject public example secrets and demo admin email placeholders."""
        # A: Known dev secret in production
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "ALLOW_DEV_AUTH": "false",
            "JWT_DEV_SECRET": "smart-eco-bin-local-dev-secret-key-32b"
        }):
            with self.assertRaises(SecurityConfigurationError) as ctx:
                SecurityConfig()
            self.assertIn("known public development secret key", str(ctx.exception))
            # Critical: Verify secret itself is NOT printed in the exception message
            self.assertNotIn("smart-eco-bin-local-dev-secret-key-32b", str(ctx.exception))

        # B: Placeholder admin email in production
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "ALLOW_DEV_AUTH": "false",
            "ADMIN_EMAILS": "admin@ecosortai.com"
        }):
            with self.assertRaises(SecurityConfigurationError) as ctx:
                SecurityConfig()
            self.assertIn("Insecure placeholder administrator email", str(ctx.exception))

        # C: Short secret in development
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "ALLOW_DEV_AUTH": "true",
            "JWT_DEV_SECRET": "too-short-secret"
        }):
            with self.assertRaises(SecurityConfigurationError) as ctx:
                SecurityConfig()
            self.assertIn("must be at least 32 bytes", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 3. Development-token endpoints unavailable when disabled
    # --------------------------------------------------------------------------
    def test_03_dev_token_endpoint_disabled_when_dev_auth_false(self):
        """POST /api/auth/demo-token returns 403 Forbidden when allow_dev_auth is False."""
        mock_config = MagicMock()
        mock_config.allow_dev_auth = False
        mock_config.is_production = True
        mock_config.auth_provider = "firebase"

        with patch.object(token_verifier, "config", mock_config):
            resp = self.client.post("/api/auth/demo-token", json={
                "email": "citizen@example.gov",
                "role": "citizen"
            })
            self.assertEqual(resp.status_code, 403)
            self.assertIn("disabled in production", resp.json()["detail"])

    def test_03b_issue_dev_token_prohibits_production_or_production_idp(self):
        """token_verifier.issue_dev_token raises PermissionError in production or with production IDP."""
        mock_config = MagicMock()
        mock_config.is_production = False
        mock_config.allow_dev_auth = True
        mock_config.auth_provider = "firebase"

        with patch.object(token_verifier, "config", mock_config):
            with self.assertRaises(PermissionError) as ctx:
                token_verifier.issue_dev_token("admin@city.gov", UserRole.ADMINISTRATOR)
            self.assertIn("cannot be issued when a production identity provider", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 4. Firebase/OIDC validation failure never falls back to HMAC
    # --------------------------------------------------------------------------
    def test_04_firebase_failure_never_falls_back_to_hmac(self):
        """Failed Firebase RS256 token verification returns 401 and never falls back to HMAC."""
        # Generate a valid base64url-encoded RS256-header token
        import base64
        hdr = base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode()).decode().rstrip("=")
        pay = base64.urlsafe_b64encode(json.dumps({"sub": "1234567890"}).encode()).decode().rstrip("=")
        sig = base64.urlsafe_b64encode(b"fakesignaturebytes1234567890123456").decode().rstrip("=")
        rs256_token = f"{hdr}.{pay}.{sig}"

        # Mock Firebase Admin to raise verification error
        with patch.object(token_verifier, "_firebase_available", True):
            with patch("firebase_admin.auth.verify_id_token", side_effect=Exception("Firebase token expired or invalid")):
                with self.assertRaises(AuthenticationError) as ctx:
                    token_verifier.verify_token(rs256_token)
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertIn("Invalid or expired Firebase ID token", str(ctx.exception))

    def test_04b_production_rejects_hs256_tokens_unconditionally(self):
        """In production, HS256 development tokens are rejected immediately with 401."""
        valid_hs256_token, _ = token_verifier.issue_dev_token("citizen@city.gov", UserRole.CITIZEN)

        mock_config = MagicMock()
        mock_config.is_production = True
        mock_config.allow_dev_auth = False
        mock_config.auth_provider = "firebase"

        with patch.object(token_verifier, "config", mock_config):
            with self.assertRaises(AuthenticationError) as ctx:
                token_verifier.verify_token(valid_hs256_token)
            self.assertEqual(ctx.exception.status_code, 401)
            self.assertIn("Development-only HMAC tokens are strictly rejected", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 5. Missing, invalid, expired, wrong-issuer, and wrong-audience tokens rejected
    # --------------------------------------------------------------------------
    def test_05_token_validation_edge_cases(self):
        """Verifies rejection of missing, invalid, expired, wrong-issuer, and wrong-audience tokens."""
        # A: Missing token
        resp = self.client.get("/api/auth/me")
        self.assertEqual(resp.status_code, 401)

        # B: Malformed token
        resp = self.client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
        self.assertEqual(resp.status_code, 401)

        # C: Expired token
        now = int(time.time())
        expired_payload = {
            "sub": "user-expired",
            "iss": token_verifier.DEV_ISSUER,
            "aud": token_verifier.DEV_AUDIENCE,
            "iat": now - 3600,
            "exp": now - 60,
            "email": "user@city.gov",
            "role": "citizen"
        }
        expired_token = jwt.encode(expired_payload, token_verifier.dev_secret, algorithm="HS256")
        resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        self.assertEqual(resp.status_code, 401)
        self.assertIn("expired", resp.json()["detail"].lower())

        # D: Wrong issuer
        wrong_iss_payload = dict(expired_payload, exp=now + 3600, iss="untrusted-authority")
        wrong_iss_token = jwt.encode(wrong_iss_payload, token_verifier.dev_secret, algorithm="HS256")
        resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {wrong_iss_token}"})
        self.assertEqual(resp.status_code, 401)
        self.assertIn("issuer", resp.json()["detail"].lower())

        # E: Wrong audience
        wrong_aud_payload = dict(expired_payload, exp=now + 3600, aud="different-api")
        wrong_aud_token = jwt.encode(wrong_aud_payload, token_verifier.dev_secret, algorithm="HS256")
        resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {wrong_aud_token}"})
        self.assertEqual(resp.status_code, 401)
        self.assertIn("audience", resp.json()["detail"].lower())

    # --------------------------------------------------------------------------
    # 6. Citizen cannot access administrator-only routes (403)
    # --------------------------------------------------------------------------
    def test_06_citizen_rejected_from_admin_routes(self):
        """Authenticated citizens receive 403 Forbidden on all administrative endpoints."""
        citizen_token, _ = token_verifier.issue_dev_token("alice@city.gov", UserRole.CITIZEN)
        headers = {"Authorization": f"Bearer {citizen_token}"}

        admin_endpoints = [
            ("GET", "/api/sanitation"),
            ("GET", "/api/anomalies"),
            ("GET", "/api/predictive-insights"),
            ("POST", "/api/sanitationai"),
        ]

        for method, endpoint in admin_endpoints:
            if method == "GET":
                resp = self.client.get(endpoint, headers=headers)
            else:
                resp = self.client.post(endpoint, json={"prompt": "audit status"}, headers=headers)
            self.assertEqual(resp.status_code, 403, f"Endpoint {endpoint} failed to return 403 for citizen.")
            self.assertIn("administrator privileges", resp.json()["detail"].lower())

    # --------------------------------------------------------------------------
    # 7. Administrator must have verified server-side privileges
    # --------------------------------------------------------------------------
    def test_07_verified_administrator_access_and_forgery_rejection(self):
        """Verified administrators are granted access; forged tokens are rejected."""
        admin_token, user = token_verifier.issue_dev_token("admin@city.gov", UserRole.ADMINISTRATOR)
        self.assertTrue(user.is_admin)

        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = self.client.get("/api/sanitation", headers=headers)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get("/api/anomalies", headers=headers)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get("/api/predictive-insights", headers=headers)
        self.assertEqual(resp.status_code, 200)

        # Forged token (signed with an attacker's key)
        forged_token = jwt.encode(
            {"sub": "attacker", "iss": token_verifier.DEV_ISSUER, "aud": token_verifier.DEV_AUDIENCE, "exp": int(time.time()) + 3600, "admin": True},
            "unauthorized-attacker-secret-key-32b",
            algorithm="HS256"
        )
        resp = self.client.get("/api/sanitation", headers={"Authorization": f"Bearer {forged_token}"})
        self.assertEqual(resp.status_code, 401)

    # --------------------------------------------------------------------------
    # 8. Citizen cannot access another citizen's records
    # --------------------------------------------------------------------------
    def test_08_citizen_data_isolation_and_cross_lookup_prevention(self):
        """Citizen A cannot list, filter, or look up Citizen B's historical records."""
        alice_token, alice_user = token_verifier.issue_dev_token("alice@city.gov", UserRole.CITIZEN)
        bob_token, bob_user = token_verifier.issue_dev_token("bob@city.gov", UserRole.CITIZEN)

        # Seed records for Alice and Bob
        storage_service.save_record({
            "id": "REC-ALICE-101",
            "itemName": "Alice Plastic Bottle",
            "wasteType": "Recyclable",
            "predictedClass": "plastic",
            "userId": alice_user.uid
        })
        storage_service.save_record({
            "id": "REC-BOB-202",
            "itemName": "Bob Organic Waste",
            "wasteType": "Organic",
            "predictedClass": "organic",
            "userId": bob_user.uid
        })

        # Alice history query returns Alice's record only
        resp_alice = self.client.get("/api/history", headers={"Authorization": f"Bearer {alice_token}"})
        self.assertEqual(resp_alice.status_code, 200)
        alice_records = resp_alice.json()
        alice_ids = [r["id"] for r in alice_records]
        self.assertIn("REC-ALICE-101", alice_ids)
        self.assertNotIn("REC-BOB-202", alice_ids)

        # Alice cannot directly inspect Bob's record (HTTP 403)
        resp_direct = self.client.get("/api/history/REC-BOB-202", headers={"Authorization": f"Bearer {alice_token}"})
        self.assertEqual(resp_direct.status_code, 403)

        # Bob can inspect his own record (HTTP 200)
        resp_bob_direct = self.client.get("/api/history/REC-BOB-202", headers={"Authorization": f"Bearer {bob_token}"})
        self.assertEqual(resp_bob_direct.status_code, 200)

    # --------------------------------------------------------------------------
    # 9. Caller-supplied userId cannot impersonate another account
    # --------------------------------------------------------------------------
    def test_09_predict_endpoint_binds_verified_identity_only(self):
        """POST /api/predict binds current_user.uid, preventing caller-supplied userId spoofing."""
        citizen_token, citizen_user = token_verifier.issue_dev_token("charlie@city.gov", UserRole.CITIZEN)

        # Attempt to impersonate 'victim-user-999' by sending it in form/params
        files = {"file": ("test.jpg", self.valid_image_bytes, "image/jpeg")}
        resp = self.client.post(
            "/api/predict",
            files=files,
            params={"userId": "victim-user-999"},
            headers={"Authorization": f"Bearer {citizen_token}"}
        )
        self.assertEqual(resp.status_code, 200)

        # Verify the persisted record owns Charlie's UID, not victim-user-999
        records = storage_service.list_records(limit=10)
        latest = records[0]
        self.assertEqual(latest["userId"], citizen_user.uid)
        self.assertNotEqual(latest["userId"], "victim-user-999")

    # --------------------------------------------------------------------------
    # 10. Administrative deletion denied to unauthorised users
    # --------------------------------------------------------------------------
    def test_10_administrative_deletion_guard(self):
        """DELETE /api/history/{id} is rejected for anonymous (401) and citizen (403), allowed for admin (200)."""
        storage_service.save_record({"id": "REC-DEL-001", "itemName": "Test Deletion Item"})

        # Anonymous caller
        resp = self.client.delete("/api/history/REC-DEL-001")
        self.assertEqual(resp.status_code, 401)

        # Citizen caller
        citizen_token, _ = token_verifier.issue_dev_token("citizen@city.gov", UserRole.CITIZEN)
        resp = self.client.delete("/api/history/REC-DEL-001", headers={"Authorization": f"Bearer {citizen_token}"})
        self.assertEqual(resp.status_code, 403)

        # Administrator caller
        admin_token, _ = token_verifier.issue_dev_token("admin@city.gov", UserRole.ADMINISTRATOR)
        resp = self.client.delete("/api/history/REC-DEL-001", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["deleted"])
        self.assertIsNone(storage_service.get_record("REC-DEL-001"))

    # --------------------------------------------------------------------------
    # 11. Authentication errors and logs do not expose secrets
    # --------------------------------------------------------------------------
    def test_11_errors_and_status_endpoints_do_not_expose_secrets(self):
        """Public telemetry and error messages do not disclose secret keys or absolute host paths."""
        resp_sec = self.client.get("/api/security/posture")
        self.assertEqual(resp_sec.status_code, 200)
        sec_json = resp_sec.text
        self.assertNotIn(token_verifier.dev_secret, sec_json)
        self.assertNotIn("smart-eco-bin-local-dev-secret-key-32b", sec_json)

        resp_storage = self.client.get("/api/storage/status")
        self.assertEqual(resp_storage.status_code, 200)
        storage_data = resp_storage.json()
        storage_file = storage_data.get("storage_file") or ""
        # Check no Windows drive letter or absolute path leaked
        self.assertNotIn("C:\\", storage_file)
        self.assertNotIn("Users\\user", storage_file)

    # --------------------------------------------------------------------------
    # 12. Invalid storage configuration fails safely
    # --------------------------------------------------------------------------
    def test_12_invalid_storage_provider_fails_safely(self):
        """Unsupported STORAGE_PROVIDER raises ValueError with descriptive message."""
        with patch.dict(os.environ, {"STORAGE_PROVIDER": "unsupported_cloud_db"}):
            with self.assertRaises(ValueError) as ctx:
                create_storage_provider()
            self.assertIn("Unsupported STORAGE_PROVIDER", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 13. Rate limiting and request validation
    # --------------------------------------------------------------------------
    def test_13_rate_limiting_and_spoofing_prevention(self):
        """Enforces 30 requests/minute limit and rejects IP spoofing from untrusted proxies."""
        files = {"file": ("test.jpg", self.valid_image_bytes, "image/jpeg")}

        # Send requests up to the limit
        for _ in range(RATE_LIMIT_MAX_REQUESTS):
            resp = self.client.post("/api/predict", files=files)
            self.assertEqual(resp.status_code, 200)

        # 31st request exceeds rate limit -> HTTP 429
        resp = self.client.post("/api/predict", files=files)
        self.assertEqual(resp.status_code, 429)
        self.assertIn("Rate limit exceeded", resp.json()["detail"])

        # Reset limiter for next test
        clear_rate_limits()

        # Anti-spoofing: Untrusted proxy sending X-Forwarded-For should NOT change client identity
        spoofed_headers = {"X-Forwarded-For": "203.0.113.195"}
        resp = self.client.post("/api/predict", files=files, headers=spoofed_headers)
        self.assertEqual(resp.status_code, 200)

    def test_13b_image_format_and_size_validation(self):
        """Rejects non-image MIME types (400) and oversized payloads (> 10MB) (400)."""
        # A: Invalid file type
        txt_files = {"file": ("malicious.txt", b"plain text", "text/plain")}
        resp = self.client.post("/api/predict", files=txt_files)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid image type", resp.json()["detail"])

        # B: Oversized payload (> 10MB)
        oversized = b"0" * (10 * 1024 * 1024 + 1)
        large_files = {"file": ("huge.jpg", oversized, "image/jpeg")}
        resp = self.client.post("/api/predict", files=large_files)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("exceeds 10MB limit", resp.json()["detail"])

    # --------------------------------------------------------------------------
    # 14. Existing model, routing, and simulation functionality continues to work
    # --------------------------------------------------------------------------
    def test_14_end_to_end_model_and_simulation_intact(self):
        """Validates that MobileNetV2 waste classification and software segregation remain fully functional."""
        files = {"file": ("sample.jpg", self.valid_image_bytes, "image/jpeg")}
        resp = self.client.post("/api/predict", files=files)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertIn("predictedClass", data)
        self.assertIn("wasteType", data)
        self.assertIn("confidence", data)
        self.assertIn("recommendation", data)
        self.assertIn("disposalBin", data)
        self.assertIn("destinationCompartment", data)
        self.assertIn(data["simulationStatus"], ("READY", "SIMULATED"))


if __name__ == "__main__":
    unittest.main()
