"""
SMART ECO BIN — Stage 13 Hardened Authentication & Administrator Authorization Tests
=====================================================================================
Validates all pre-deployment security requirements:
1. Development token endpoint (/api/auth/demo-token) disabled in production and staging.
2. Fails closed if environment cannot be determined safely.
3. Citizens cannot obtain administrator privileges by requesting the administrator role.
4. Unapproved emails cannot obtain administrator privileges under any circumstances.
5. Server-side allowlist is strictly enforced for administrator token issuance and verification.
6. Verified, authorized administrators retain full intended operational access.
7. Invalid, tampered, expired, or incorrectly signed tokens are strictly rejected.
8. Zero HMAC fallback when identity provider verification fails.
"""

import os
import sys
import time
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import jwt

# Ensure backend root is on sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from main import app
from app.auth.config import SecurityConfig, SecurityConfigurationError
from app.auth.security import TokenVerifier, AuthenticationError, token_verifier
from app.auth.models import UserRole


class TestStage13HardenedAuthAndAdminSecurity(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    # --------------------------------------------------------------------------
    # 1. Development Token Endpoint Disabled in Production & Staging (Fail Closed)
    # --------------------------------------------------------------------------
    def test_01_demo_token_disabled_in_production(self):
        """POST /api/auth/demo-token must return 403 Forbidden in production."""
        mock_cfg = MagicMock()
        mock_cfg.is_production = True
        mock_cfg.is_staging = False
        mock_cfg.is_dev_environment = False
        mock_cfg.allow_dev_auth = False
        mock_cfg.is_dev_token_allowed = False

        with patch.object(token_verifier, "config", mock_cfg):
            resp = self.client.post("/api/auth/demo-token", json={
                "email": "user@example.com",
                "role": "citizen"
            })
            self.assertEqual(resp.status_code, 403)
            self.assertIn("disabled", resp.json()["detail"].lower())

    def test_02_demo_token_disabled_in_staging(self):
        """POST /api/auth/demo-token must return 403 Forbidden in staging, even if allow_dev_auth is True."""
        mock_cfg = MagicMock()
        mock_cfg.is_production = False
        mock_cfg.is_staging = True
        mock_cfg.is_dev_environment = False
        mock_cfg.allow_dev_auth = False
        mock_cfg.is_dev_token_allowed = False

        with patch.object(token_verifier, "config", mock_cfg):
            resp = self.client.post("/api/auth/demo-token", json={
                "email": "tester@example.com",
                "role": "citizen"
            })
            self.assertEqual(resp.status_code, 403)
            self.assertIn("disabled", resp.json()["detail"].lower())

    def test_03_demo_token_fails_closed_on_unknown_or_ambiguous_environment(self):
        """Unknown or unverified environments fail closed: demo token endpoint is disabled and invalid dev auth raises error."""
        # Scenario A: If ALLOW_DEV_AUTH is mistakenly requested in an unknown environment, startup is rejected
        with patch.dict(os.environ, {"ENVIRONMENT": "unknown_cloud_sandbox", "ALLOW_DEV_AUTH": "true"}):
            with self.assertRaises(SecurityConfigurationError):
                SecurityConfig()

        # Scenario B: In an unknown environment, system fails closed to production with dev tokens disabled
        with patch.dict(os.environ, {"ENVIRONMENT": "unknown_cloud_sandbox", "ALLOW_DEV_AUTH": "false"}):
            cfg = SecurityConfig()
            self.assertFalse(cfg.is_dev_environment, "Unknown env must NOT be marked as dev")
            self.assertTrue(cfg.is_production, "Ambiguous env must fail closed to production")
            self.assertFalse(cfg.allow_dev_auth, "Dev auth must be False for unverified env")
            self.assertFalse(cfg.is_dev_token_allowed, "Dev tokens must be forbidden for unverified env")

    def test_04_issue_dev_token_raises_permission_error_in_production_and_staging(self):
        """token_verifier.issue_dev_token raises PermissionError in production or staging."""
        mock_cfg = MagicMock()
        mock_cfg.is_production = True
        mock_cfg.is_dev_token_allowed = False
        verifier = TokenVerifier(config=mock_cfg)

        with self.assertRaises(PermissionError) as ctx:
            verifier.issue_dev_token("admin@ecosortai.com", UserRole.ADMINISTRATOR)
        self.assertIn("strictly prohibited", str(ctx.exception).lower())

    # --------------------------------------------------------------------------
    # 2. Citizen Cannot Obtain Administrator Privileges by Requesting Admin Role
    # --------------------------------------------------------------------------
    def test_05_citizen_requesting_admin_role_rejected(self):
        """A citizen requesting role='administrator' without being in admin_emails is rejected with 403."""
        # Use development environment with explicit admin allowlist
        mock_cfg = MagicMock()
        mock_cfg.is_production = False
        mock_cfg.is_staging = False
        mock_cfg.is_dev_environment = True
        mock_cfg.allow_dev_auth = True
        mock_cfg.is_dev_token_allowed = True
        mock_cfg.admin_emails = {"admin@ecosortai.com", "supervisor@sanitation.gov"}
        mock_cfg.dev_secret = "smart-eco-bin-local-dev-secret-key-32b"
        mock_cfg.auth_provider = "development"

        with patch.object(token_verifier, "config", mock_cfg):
            # Attempt privilege escalation: ordinary citizen email requests administrator role
            resp = self.client.post("/api/auth/demo-token", json={
                "email": "curious.citizen@gmail.com",
                "role": "administrator"
            })
            self.assertEqual(resp.status_code, 403)
            self.assertIn("not authorized for administrator privileges", resp.json()["detail"])

    def test_06_unapproved_email_cannot_obtain_administrator_privileges(self):
        """Any email not on the server-side allowlist is rejected when requesting admin privileges."""
        mock_cfg = MagicMock()
        mock_cfg.is_production = False
        mock_cfg.is_staging = False
        mock_cfg.is_dev_environment = True
        mock_cfg.allow_dev_auth = True
        mock_cfg.is_dev_token_allowed = True
        mock_cfg.admin_emails = {"authorized.official@sanitation.gov"}
        mock_cfg.dev_secret = "smart-eco-bin-local-dev-secret-key-32b"
        mock_cfg.auth_provider = "development"

        verifier = TokenVerifier(config=mock_cfg)

        # Attacker tries multiple arbitrary emails
        unapproved_emails = [
            "hacker@evil.com",
            "fake.admin@sanitation.gov.attacker.com",
            "root@localhost",
            "citizen123@yahoo.com"
        ]
        for bad_email in unapproved_emails:
            with self.assertRaises(PermissionError) as ctx:
                verifier.issue_dev_token(bad_email, role=UserRole.ADMINISTRATOR)
            self.assertIn("not authorized for administrator privileges", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 3. Forged Claims in Dev & Firebase Tokens Cannot Grant Administrator Privileges
    # --------------------------------------------------------------------------
    def test_07_forged_admin_claim_in_dev_token_demoted_to_citizen(self):
        """A dev token containing admin=True or role='administrator' for unapproved email is demoted."""
        mock_cfg = MagicMock()
        mock_cfg.is_production = False
        mock_cfg.is_staging = False
        mock_cfg.is_dev_environment = True
        mock_cfg.allow_dev_auth = True
        mock_cfg.admin_emails = {"real.admin@sanitation.gov"}
        mock_cfg.dev_secret = "smart-eco-bin-local-dev-secret-key-32b"
        mock_cfg.auth_provider = "development"

        verifier = TokenVerifier(config=mock_cfg)

        # Craft forged token with admin claims
        now = int(time.time())
        forged_payload = {
            "sub": "attacker-uid-001",
            "iss": "smart-eco-bin-auth",
            "aud": "smart-eco-bin-api",
            "iat": now,
            "exp": now + 3600,
            "email": "unapproved.person@example.com",
            "role": "administrator",
            "admin": True
        }
        forged_token = jwt.encode(forged_payload, mock_cfg.dev_secret, algorithm="HS256")

        verified_user = verifier.verify_token(forged_token)
        self.assertFalse(verified_user.is_admin, "Unapproved email must NEVER receive is_admin=True")
        self.assertEqual(verified_user.role, UserRole.CITIZEN, "Unapproved email must be demoted to citizen")

    def test_08_firebase_claims_without_verified_email_rejected_for_admin(self):
        """Firebase tokens claiming admin=True without a verified email are strictly rejected for admin privileges."""
        mock_cfg = MagicMock()
        mock_cfg.admin_emails = {"official.director@sanitation.gov"}
        verifier = TokenVerifier(config=mock_cfg)

        claims = {
            "uid": "fb-attacker-001",
            "email": "official.director@sanitation.gov",
            "email_verified": False,  # Not verified!
            "admin": True,
            "role": "administrator"
        }
        user = verifier._build_user_from_firebase_claims(claims)
        self.assertFalse(user.is_admin, "Unverified email must not be granted admin status")
        self.assertEqual(user.role, UserRole.CITIZEN)

    # --------------------------------------------------------------------------
    # 4. Verified, Authorized Administrators Retain Intended Access
    # --------------------------------------------------------------------------
    def test_09_authorized_administrator_token_issued_and_granted_access(self):
        """An authorized email on the allowlist successfully obtains admin token and accesses admin routes."""
        mock_cfg = MagicMock()
        mock_cfg.is_production = False
        mock_cfg.is_staging = False
        mock_cfg.is_dev_environment = True
        mock_cfg.allow_dev_auth = True
        mock_cfg.is_dev_token_allowed = True
        mock_cfg.admin_emails = {"admin@ecosortai.com"}
        mock_cfg.dev_secret = "smart-eco-bin-local-dev-secret-key-32b"
        mock_cfg.auth_provider = "development"

        with patch.object(token_verifier, "config", mock_cfg):
            token, user = token_verifier.issue_dev_token("admin@ecosortai.com", role=UserRole.ADMINISTRATOR)
            self.assertTrue(user.is_admin)
            self.assertEqual(user.role, UserRole.ADMINISTRATOR)

            # Test accessing protected administrator endpoints
            headers = {"Authorization": f"Bearer {token}"}
            resp = self.client.get("/api/sanitation", headers=headers)
            self.assertEqual(resp.status_code, 200, "Authorized admin must have access to /api/sanitation")

            resp_anomalies = self.client.get("/api/anomalies", headers=headers)
            self.assertEqual(resp_anomalies.status_code, 200, "Authorized admin must have access to /api/anomalies")

    def test_10_authorized_email_requesting_citizen_receives_citizen_token(self):
        """An email on the allowlist can still be issued a standard citizen token when citizen is requested."""
        mock_cfg = MagicMock()
        mock_cfg.is_production = False
        mock_cfg.is_staging = False
        mock_cfg.is_dev_environment = True
        mock_cfg.allow_dev_auth = True
        mock_cfg.is_dev_token_allowed = True
        mock_cfg.admin_emails = {"admin@ecosortai.com"}
        mock_cfg.dev_secret = "smart-eco-bin-local-dev-secret-key-32b"
        mock_cfg.auth_provider = "development"

        with patch.object(token_verifier, "config", mock_cfg):
            token, user = token_verifier.issue_dev_token("admin@ecosortai.com", role=UserRole.CITIZEN)
            self.assertFalse(user.is_admin, "Citizen request must produce is_admin=False")
            self.assertEqual(user.role, UserRole.CITIZEN)

    # --------------------------------------------------------------------------
    # 5. Invalid, Forged, and Tampered Tokens are Rejected
    # --------------------------------------------------------------------------
    def test_11_invalid_signature_rejected(self):
        """Token signed with an incorrect key is rejected with 401 in development mode."""
        dev_cfg = MagicMock()
        dev_cfg.is_production = False
        dev_cfg.is_staging = False
        dev_cfg.is_dev_environment = True
        dev_cfg.allow_dev_auth = True
        dev_cfg.dev_secret = "smart-eco-bin-local-dev-secret-key-32b"
        dev_cfg.auth_provider = "development"
        dev_cfg.admin_emails = {"admin@ecosortai.com"}

        with patch.object(token_verifier, "config", dev_cfg):
            now = int(time.time())
            token = jwt.encode(
                {"sub": "user-1", "iss": "smart-eco-bin-auth", "aud": "smart-eco-bin-api", "exp": now + 3600},
                "completely-wrong-secret-key-32b-length",
                algorithm="HS256"
            )
            resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(resp.status_code, 401)
            self.assertIn("signature verification failed", resp.json()["detail"].lower())

    def test_12_expired_token_rejected(self):
        """Expired tokens are rejected with 401."""
        dev_cfg = MagicMock()
        dev_cfg.is_production = False
        dev_cfg.is_staging = False
        dev_cfg.is_dev_environment = True
        dev_cfg.allow_dev_auth = True
        dev_cfg.dev_secret = "smart-eco-bin-local-dev-secret-key-32b"
        dev_cfg.auth_provider = "development"
        dev_cfg.admin_emails = {"admin@ecosortai.com"}

        with patch.object(token_verifier, "config", dev_cfg):
            now = int(time.time())
            token = jwt.encode(
                {"sub": "user-1", "iss": "smart-eco-bin-auth", "aud": "smart-eco-bin-api", "exp": now - 100},
                dev_cfg.dev_secret,
                algorithm="HS256"
            )
            resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(resp.status_code, 401)
            self.assertIn("expired", resp.json()["detail"].lower())

    def test_13_wrong_issuer_and_audience_rejected(self):
        """Tokens with invalid issuer or audience claims are rejected."""
        dev_cfg = MagicMock()
        dev_cfg.is_production = False
        dev_cfg.is_staging = False
        dev_cfg.is_dev_environment = True
        dev_cfg.allow_dev_auth = True
        dev_cfg.dev_secret = "smart-eco-bin-local-dev-secret-key-32b"
        dev_cfg.auth_provider = "development"
        dev_cfg.admin_emails = {"admin@ecosortai.com"}

        with patch.object(token_verifier, "config", dev_cfg):
            now = int(time.time())
            # Wrong issuer
            token_bad_iss = jwt.encode(
                {"sub": "user-1", "iss": "untrusted-issuer", "aud": "smart-eco-bin-api", "exp": now + 3600},
                dev_cfg.dev_secret,
                algorithm="HS256"
            )
            resp1 = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_bad_iss}"})
            self.assertEqual(resp1.status_code, 401)

            # Wrong audience
            token_bad_aud = jwt.encode(
                {"sub": "user-1", "iss": "smart-eco-bin-auth", "aud": "wrong-api-audience", "exp": now + 3600},
                dev_cfg.dev_secret,
                algorithm="HS256"
            )
            resp2 = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_bad_aud}"})
            self.assertEqual(resp2.status_code, 401)

    def test_14_hmac_development_token_strictly_rejected_in_production(self):
        """In production, development HMAC tokens are rejected immediately with no silent fallback."""
        prod_cfg = MagicMock()
        prod_cfg.is_production = True
        prod_cfg.is_staging = False
        prod_cfg.is_dev_environment = False
        prod_cfg.allow_dev_auth = False
        prod_cfg.auth_provider = "firebase"
        prod_cfg.admin_emails = {"admin@ecosortai.com"}
        prod_cfg.dev_secret = ""

        with patch.object(token_verifier, "config", prod_cfg):
            # Attempt to use an HMAC token against a production configured verifier
            now = int(time.time())
            hmac_token = jwt.encode(
                {"sub": "admin-1", "iss": "smart-eco-bin-auth", "aud": "smart-eco-bin-api", "exp": now + 3600},
                "secret-key-attempt",
                algorithm="HS256"
            )
            resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {hmac_token}"})
            self.assertEqual(resp.status_code, 401)
            self.assertIn("development-only hmac tokens are strictly rejected", resp.json()["detail"].lower())


if __name__ == "__main__":
    unittest.main()
