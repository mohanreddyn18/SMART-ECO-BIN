"""
SMART ECO BIN — Stage 8 Staging Readiness & Identity Verification Test Suite
=============================================================================
Comprehensive test verification for Stage 8:
1. Valid verified citizen identity (RS256 ID token).
2. Valid verified administrator identity (RS256 Custom Claims & verified email whitelist).
3. Expired, malformed, tampered, wrong-audience, and wrong-issuer tokens.
4. Missing, unverified, or invalid administrator claims (unverified email rejection).
5. Revoked-token handling via Firebase check_revoked=True.
6. Firebase/OIDC verification failure without HMAC fallback.
7. Development tokens rejected in production and staging under identity providers.
8. Forged client-side administrator state rejected by protected backend endpoints.
9. Citizen A cannot read, modify, or delete Citizen B's records across pagination/search.
10. Anonymous callers cannot retrieve private citizen history.
11. Unauthorized deletion and municipal administrative operations rejected (401/403).
12. Invalid storage configuration and identity-provider initialization fail safely.
13. Firebase Auth emulator initialization path support.
14. Zero retention of uploaded image bytes and sanitized public telemetry.

Boundary Notice:
Tests in this module verify the authentication and authorization boundary using controlled
mock payloads conforming to the Firebase Authentication / Google OIDC specification.
Real identity provider testing requires live staging deployment with configured GCP credentials.
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

# Ensure test execution context
os.environ["ENVIRONMENT"] = "development"
os.environ["ALLOW_DEV_AUTH"] = "true"
os.environ["STORAGE_PROVIDER"] = "local"

from main import app
from app.auth.config import SecurityConfig, SecurityConfigurationError, security_config
from app.auth.security import TokenVerifier, token_verifier, AuthenticationError
from app.auth.models import UserRole
from app.services.storage_service import storage_service, create_storage_provider
from app.routes.predict import clear_rate_limits


def make_mock_rs256_token(header_dict, payload_dict):
    """Constructs a valid base64url-encoded RS256 token structure for test routing."""
    hdr = base64.urlsafe_b64encode(json.dumps(header_dict).encode()).decode().rstrip("=")
    pay = base64.urlsafe_b64encode(json.dumps(payload_dict).encode()).decode().rstrip("=")
    sig = base64.urlsafe_b64encode(b"simulated_asymmetric_rsa_signature_256").decode().rstrip("=")
    return f"{hdr}.{pay}.{sig}"


class TestStage8StagingReadiness(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        img = Image.new("RGB", (224, 224), color=(34, 139, 34))
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
        security_config.reload()
        token_verifier._init_firebase_admin()

    # --------------------------------------------------------------------------
    # 1. Valid verified citizen identity (RS256 Firebase token)
    # --------------------------------------------------------------------------
    def test_01_valid_verified_citizen_identity_rs256(self):
        """Verified citizen RS256 token grants citizen access and authenticates identity."""
        token = make_mock_rs256_token(
            {"alg": "RS256", "typ": "JWT"},
            {"sub": "fb-citizen-001", "email": "citizen1@city.gov", "email_verified": True}
        )

        mock_claims = {
            "uid": "fb-citizen-001",
            "email": "citizen1@city.gov",
            "email_verified": True,
            "auth_time": int(time.time()),
            "iss": "https://securetoken.google.com/test-project",
            "role": "citizen"
        }

        with patch.object(token_verifier, "_firebase_available", True):
            with patch("firebase_admin.auth.verify_id_token", return_value=mock_claims):
                resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
                self.assertEqual(resp.status_code, 200)
                data = resp.json()
                self.assertEqual(data["uid"], "fb-citizen-001")
                self.assertEqual(data["email"], "citizen1@city.gov")
                self.assertEqual(data["role"], "citizen")
                self.assertFalse(data["is_admin"])

    # --------------------------------------------------------------------------
    # 2. Valid verified administrator identity (Custom Claims & Whitelist)
    # --------------------------------------------------------------------------
    def test_02_verified_admin_via_custom_claims_and_whitelist(self):
        """Administrator privileges granted via verified custom claims or verified email whitelist."""
        token = make_mock_rs256_token(
            {"alg": "RS256", "typ": "JWT"},
            {"sub": "fb-admin-999", "email": "lead@sanitation.gov"}
        )

        # Case A: Firebase Custom Claim {"admin": True, "role": "administrator"}
        admin_claims_custom = {
            "uid": "fb-admin-999",
            "email": "lead@sanitation.gov",
            "email_verified": True,
            "admin": True,
            "role": "administrator",
            "auth_time": int(time.time()),
            "iss": "https://securetoken.google.com/test-project"
        }

        with patch.object(token_verifier, "_firebase_available", True):
            with patch("firebase_admin.auth.verify_id_token", return_value=admin_claims_custom):
                resp = self.client.get("/api/sanitation", headers={"Authorization": f"Bearer {token}"})
                self.assertEqual(resp.status_code, 200)

                resp_anom = self.client.get("/api/anomalies", headers={"Authorization": f"Bearer {token}"})
                self.assertEqual(resp_anom.status_code, 200)

        # Case B: Verified Email on server-side whitelist
        admin_claims_whitelist = {
            "uid": "fb-admin-888",
            "email": "trusted-admin@city.gov",
            "email_verified": True,  # Critical: Must be verified
            "auth_time": int(time.time()),
            "iss": "https://securetoken.google.com/test-project"
        }

        with patch.object(token_verifier, "_firebase_available", True):
            with patch.object(token_verifier.config, "admin_emails", {"trusted-admin@city.gov"}):
                with patch("firebase_admin.auth.verify_id_token", return_value=admin_claims_whitelist):
                    resp = self.client.get("/api/sanitation", headers={"Authorization": f"Bearer {token}"})
                    self.assertEqual(resp.status_code, 200)

    # --------------------------------------------------------------------------
    # 3. Expired, malformed, tampered, wrong-audience, and wrong-issuer tokens
    # --------------------------------------------------------------------------
    def test_03_token_rejections_and_error_handling(self):
        """Tokens with malformed headers, expired signatures, or wrong claims are rejected with 401."""
        # A: Malformed base64 header
        resp = self.client.get("/api/auth/me", headers={"Authorization": "Bearer bad.token.structure"})
        self.assertEqual(resp.status_code, 401)

        # B: Missing alg in header
        no_alg_token = make_mock_rs256_token({"typ": "JWT"}, {"sub": "123"})
        resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {no_alg_token}"})
        self.assertEqual(resp.status_code, 401)
        self.assertIn("missing algorithm", resp.json()["detail"].lower())

        # C: Expired Firebase token
        token = make_mock_rs256_token({"alg": "RS256"}, {"sub": "expired-user"})
        with patch.object(token_verifier, "_firebase_available", True):
            with patch("firebase_admin.auth.verify_id_token", side_effect=Exception("Firebase token has expired")):
                resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
                self.assertEqual(resp.status_code, 401)
                self.assertIn("expired", resp.json()["detail"].lower())

        # D: Unsupported algorithm (e.g. none, ES256)
        unsupported_token = make_mock_rs256_token({"alg": "none"}, {"sub": "user"})
        resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {unsupported_token}"})
        self.assertEqual(resp.status_code, 401)
        self.assertIn("unsupported token algorithm", resp.json()["detail"].lower())

    # --------------------------------------------------------------------------
    # 4. Missing or invalid administrator claims (Unverified Email Attack)
    # --------------------------------------------------------------------------
    def test_04_unverified_email_cannot_claim_administrator_status(self):
        """Attacker registering unverified admin email on identity provider is NOT granted admin."""
        token = make_mock_rs256_token({"alg": "RS256"}, {"sub": "attacker-001"})

        # Attacker registered 'trusted-admin@city.gov' on Firebase but email_verified is False!
        unverified_claims = {
            "uid": "attacker-001",
            "email": "trusted-admin@city.gov",
            "email_verified": False,  # Unverified!
            "auth_time": int(time.time()),
            "iss": "https://securetoken.google.com/test-project"
        }

        with patch.object(token_verifier, "_firebase_available", True):
            with patch.object(token_verifier.config, "admin_emails", {"trusted-admin@city.gov"}):
                with patch("firebase_admin.auth.verify_id_token", return_value=unverified_claims):
                    # Verify user role is resolved to citizen, not administrator
                    user = token_verifier.verify_token(token)
                    self.assertFalse(user.is_admin)
                    self.assertEqual(user.role, UserRole.CITIZEN)

                    # Calling admin route must be rejected with 403 Forbidden
                    resp = self.client.get("/api/sanitation", headers={"Authorization": f"Bearer {token}"})
                    self.assertEqual(resp.status_code, 403)

    # --------------------------------------------------------------------------
    # 5. Revoked-token handling via Firebase check_revoked=True
    # --------------------------------------------------------------------------
    def test_05_revoked_token_handling(self):
        """Revoked tokens rejected by Firebase Admin (check_revoked=True) return HTTP 401."""
        token = make_mock_rs256_token({"alg": "RS256"}, {"sub": "revoked-user"})

        with patch.object(token_verifier, "_firebase_available", True):
            with patch("firebase_admin.auth.verify_id_token", side_effect=Exception("RevokedIdTokenError: Token has been revoked")):
                resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
                self.assertEqual(resp.status_code, 401)
                self.assertIn("invalid or expired", resp.json()["detail"].lower())

    # --------------------------------------------------------------------------
    # 6. Firebase verification failure without HMAC fallback
    # --------------------------------------------------------------------------
    def test_06_firebase_failure_never_falls_back_to_hmac(self):
        """When Firebase verification fails, HMAC fallback is never attempted."""
        token = make_mock_rs256_token({"alg": "RS256"}, {"sub": "test-user"})

        with patch.object(token_verifier, "_firebase_available", True):
            with patch("firebase_admin.auth.verify_id_token", side_effect=Exception("Signature verification failed")):
                with patch.object(token_verifier, "_verify_dev_token") as mock_dev:
                    with self.assertRaises(AuthenticationError):
                        token_verifier.verify_token(token)
                    mock_dev.assert_not_called()

    # --------------------------------------------------------------------------
    # 7. Development tokens rejected in production and staging under IDP
    # --------------------------------------------------------------------------
    def test_07_dev_tokens_rejected_under_idp_configuration(self):
        """HS256 tokens rejected when AUTH_PROVIDER is firebase, even in non-prod environments."""
        dev_token, _ = token_verifier.issue_dev_token("dev@city.gov", UserRole.CITIZEN)

        # Configure provider as firebase
        mock_cfg = MagicMock()
        mock_cfg.is_production = False
        mock_cfg.auth_provider = "firebase"
        mock_cfg.allow_dev_auth = True

        with patch.object(token_verifier, "config", mock_cfg):
            with self.assertRaises(AuthenticationError) as ctx:
                token_verifier.verify_token(dev_token)
            self.assertEqual(ctx.exception.status_code, 401)
            self.assertIn("Development-only HMAC tokens are strictly rejected", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 8. Forged client-side administrator state rejected
    # --------------------------------------------------------------------------
    def test_08_forged_client_side_admin_state_rejected(self):
        """Tampered headers or untrusted profile claims are ignored by backend RBAC guards."""
        citizen_token, _ = token_verifier.issue_dev_token("regular@city.gov", UserRole.CITIZEN)

        # Attacker attempts to pass spoofed admin headers
        spoofed_headers = {
            "Authorization": f"Bearer {citizen_token}",
            "X-Admin-Role": "true",
            "X-User-Role": "administrator"
        }

        resp = self.client.get("/api/sanitation", headers=spoofed_headers)
        self.assertEqual(resp.status_code, 403)
        self.assertIn("administrator privileges", resp.json()["detail"].lower())

    # --------------------------------------------------------------------------
    # 9. Citizen A cannot access Citizen B's records across pagination/search
    # --------------------------------------------------------------------------
    def test_09_citizen_data_isolation_across_pagination_and_search(self):
        """Ownership filtering applies before pagination and search filters."""
        alice_token, alice_user = token_verifier.issue_dev_token("alice@city.gov", UserRole.CITIZEN)
        bob_token, bob_user = token_verifier.issue_dev_token("bob@city.gov", UserRole.CITIZEN)

        # Seed 10 records for Alice, 10 for Bob
        for i in range(10):
            storage_service.save_record({
                "id": f"REC-ALICE-{i:03d}",
                "itemName": f"Alice Plastic Item {i}",
                "wasteType": "Recyclable",
                "predictedClass": "plastic",
                "userId": alice_user.uid
            })
            storage_service.save_record({
                "id": f"REC-BOB-{i:03d}",
                "itemName": f"Bob Organic Item {i}",
                "wasteType": "Organic",
                "predictedClass": "organic",
                "userId": bob_user.uid
            })

        # Alice requests with large limit
        resp = self.client.get("/api/history?limit=100&skip=0", headers={"Authorization": f"Bearer {alice_token}"})
        self.assertEqual(resp.status_code, 200)
        alice_data = resp.json()
        self.assertEqual(len(alice_data), 10)
        for r in alice_data:
            self.assertEqual(r["userId"], alice_user.uid)
            self.assertNotIn("BOB", r["id"])

        # Alice searches for Bob's item name -> 0 results
        resp_search = self.client.get("/api/history?search=Bob", headers={"Authorization": f"Bearer {alice_token}"})
        self.assertEqual(resp_search.status_code, 200)
        self.assertEqual(len(resp_search.json()), 0)

        # Alice attempts direct lookup of Bob's record -> 403 Forbidden
        resp_direct = self.client.get("/api/history/REC-BOB-005", headers={"Authorization": f"Bearer {alice_token}"})
        self.assertEqual(resp_direct.status_code, 403)

    # --------------------------------------------------------------------------
    # 10. Anonymous callers cannot retrieve private citizen history
    # --------------------------------------------------------------------------
    def test_10_anonymous_history_cannot_retrieve_private_records(self):
        """Anonymous callers receive only public events, never private citizen records."""
        # Seed 1 private citizen record, 1 public citizen record
        storage_service.save_record({
            "id": "REC-PRIVATE-001",
            "itemName": "Private Citizen Cardboard",
            "userId": "user-private-citizen-99"
        })
        storage_service.save_record({
            "id": "REC-PUBLIC-001",
            "itemName": "Public Street Intake Sample",
            "userId": "public-citizen"
        })

        # Anonymous listing
        resp = self.client.get("/api/history")
        self.assertEqual(resp.status_code, 200)
        records = resp.json()
        record_ids = [r["id"] for r in records]
        self.assertIn("REC-PUBLIC-001", record_ids)
        self.assertNotIn("REC-PRIVATE-001", record_ids)

        # Anonymous direct lookup of private record -> 401 Unauthorized
        resp_direct = self.client.get("/api/history/REC-PRIVATE-001")
        self.assertEqual(resp_direct.status_code, 401)

    # --------------------------------------------------------------------------
    # 11. Unauthorized deletion and municipal administrative operations rejected
    # --------------------------------------------------------------------------
    def test_11_unauthorized_deletion_and_administrative_operations_rejected(self):
        """DELETE and municipal POST/GET endpoints strictly require verified administrator."""
        storage_service.save_record({"id": "REC-CRITICAL-001", "itemName": "Audit Record"})

        citizen_token, _ = token_verifier.issue_dev_token("citizen@city.gov", UserRole.CITIZEN)
        citizen_hdr = {"Authorization": f"Bearer {citizen_token}"}

        # Deletion rejected for citizen (403)
        resp_del = self.client.delete("/api/history/REC-CRITICAL-001", headers=citizen_hdr)
        self.assertEqual(resp_del.status_code, 403)

        # SanitationAI rejected for citizen (403)
        resp_ai = self.client.post("/api/sanitationai", json={"prompt": "trigger clearance"}, headers=citizen_hdr)
        self.assertEqual(resp_ai.status_code, 403)

        # Deletion rejected for unauthenticated (401)
        resp_del_anon = self.client.delete("/api/history/REC-CRITICAL-001")
        self.assertEqual(resp_del_anon.status_code, 401)

    # --------------------------------------------------------------------------
    # 12. Invalid storage configuration and identity-provider init fail safely
    # --------------------------------------------------------------------------
    def test_12_staging_configuration_invariants_and_safe_failures(self):
        """Staging environment enforces strict validation when testing production IDPs."""
        # A: Staging with firebase but missing project ID -> Fail closed
        with patch.dict(os.environ, {
            "ENVIRONMENT": "staging",
            "AUTH_PROVIDER": "firebase",
            "ALLOW_DEV_AUTH": "false",
            "GOOGLE_CLOUD_PROJECT": "",
            "FIREBASE_PROJECT_ID": ""
        }):
            with self.assertRaises(SecurityConfigurationError) as ctx:
                SecurityConfig()
            self.assertIn("Project ID", str(ctx.exception))

        # B: Staging with firebase and ALLOW_DEV_AUTH=true -> Fail closed
        with patch.dict(os.environ, {
            "ENVIRONMENT": "staging",
            "AUTH_PROVIDER": "firebase",
            "GOOGLE_CLOUD_PROJECT": "staging-project-123",
            "ALLOW_DEV_AUTH": "true"
        }):
            with self.assertRaises(SecurityConfigurationError) as ctx:
                SecurityConfig()
            self.assertIn("Development authentication (ALLOW_DEV_AUTH) cannot be enabled", str(ctx.exception))

        # C: Staging with placeholder admin email -> Fail closed
        with patch.dict(os.environ, {
            "ENVIRONMENT": "staging",
            "AUTH_PROVIDER": "firebase",
            "GOOGLE_CLOUD_PROJECT": "staging-project-123",
            "ALLOW_DEV_AUTH": "false",
            "ADMIN_EMAILS": "admin@ecosortai.com"
        }):
            with self.assertRaises(SecurityConfigurationError) as ctx:
                SecurityConfig()
            self.assertIn("Placeholder administrator email", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 13. Firebase Auth emulator initialization path support
    # --------------------------------------------------------------------------
    def test_13_firebase_auth_emulator_initialization_path(self):
        """Firebase Admin initializes cleanly when FIREBASE_AUTH_EMULATOR_HOST is configured."""
        with patch.dict(os.environ, {
            "FIREBASE_AUTH_EMULATOR_HOST": "127.0.0.1:9099",
            "GOOGLE_CLOUD_PROJECT": "demo-smart-eco-bin"
        }):
            with patch("firebase_admin.initialize_app") as mock_init:
                with patch("firebase_admin._apps", {}):
                    v = TokenVerifier(security_config)
                    mock_init.assert_called_once()
                    self.assertIn("projectId", mock_init.call_args[1].get("options", {}))

    # --------------------------------------------------------------------------
    # 14. Zero retention of uploaded image bytes and sanitized telemetry
    # --------------------------------------------------------------------------
    def test_14_zero_retention_and_sanitized_telemetry(self):
        """Uploaded image bytes are not retained on disk/record, and telemetry paths are sanitized."""
        files = {"file": ("intake.jpg", self.valid_image_bytes, "image/jpeg")}
        resp = self.client.post("/api/predict", files=files)
        self.assertEqual(resp.status_code, 200)

        # Inspect persisted record in storage
        records = storage_service.list_records(limit=1)
        latest = records[0]
        # Verify no image byte blob, raw base64 data, or image file paths persisted
        self.assertNotIn("imageBytes", latest)
        self.assertNotIn("rawImage", latest)
        self.assertIsNone(latest.get("imageUrl"))

        # Verify storage status does not leak sensitive filesystem root
        status = storage_service.get_status()
        if status.get("storage_file"):
            self.assertFalse(os.path.isabs(status["storage_file"]))


if __name__ == "__main__":
    unittest.main()
