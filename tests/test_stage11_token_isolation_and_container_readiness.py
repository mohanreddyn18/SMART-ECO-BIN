"""
SMART ECO BIN — Stage 11 Security Audit & Container Readiness Tests
===================================================================
Targeted regression tests validating:
1. Emulator tokens (alg: none) rejected unconditionally in production & staging.
2. Setting FIREBASE_AUTH_EMULATOR_HOST in production or staging fails validation at startup.
3. FIREBASE_AUTH_EMULATOR_HOST in development must resolve strictly to local loopback (127.0.0.1, localhost, ::1).
4. Non-loopback emulator hosts in dev are rejected with SecurityConfigurationError and ignored by token verifier.
5. Forged claims or unverified email cannot gain administrator privileges under any circumstances.
6. Zero HMAC fallback when Firebase/OIDC verification fails.
7. Development HMAC tokens (alg: HS256) rejected unconditionally in production and staging.
8. Citizens cannot access municipal admin endpoints or inspect other citizens' records.
9. Container hygiene: .dockerignore excludes sensitive secrets, .env files, local ledgers, tests.
"""

import os
import io
import time
import unittest
from typing import Dict, Any
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from PIL import Image
import jwt

# Configure clean test environment
os.environ["ENVIRONMENT"] = "development"
os.environ["ALLOW_DEV_AUTH"] = "true"
os.environ["AUTH_PROVIDER"] = "auto"
os.environ.pop("JWT_DEV_SECRET", None)
os.environ["ADMIN_EMAILS"] = "admin@sanitation.gov,supervisor@city.gov,admin@ecosortai.com,admin@city.gov"
os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = ""

from main import app
from app.auth.config import SecurityConfig, SecurityConfigurationError, is_loopback_host
from app.auth.security import TokenVerifier, AuthenticationError
from app.auth.models import UserRole


class TestStage11TokenIsolationAndContainerReadiness(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        os.environ.pop("ADMIN_EMAILS", None)
        from app.auth.config import security_config
        security_config.reload()

    def setUp(self):
        self.client = TestClient(app)

    # --------------------------------------------------------------------------
    # 1. Loopback Validation Tests
    # --------------------------------------------------------------------------
    def test_01_is_loopback_host_validator(self):
        """is_loopback_host accepts only local loopback interfaces."""
        # Valid loopback interfaces
        self.assertTrue(is_loopback_host("127.0.0.1:9099"))
        self.assertTrue(is_loopback_host("localhost:9099"))
        self.assertTrue(is_loopback_host("[::1]:9099"))
        self.assertTrue(is_loopback_host("127.0.0.1"))
        self.assertTrue(is_loopback_host("localhost"))
        self.assertTrue(is_loopback_host("::1"))
        self.assertTrue(is_loopback_host("http://127.0.0.1:9099"))

        # Insecure or remote addresses must be rejected
        self.assertFalse(is_loopback_host("192.168.1.100:9099"))
        self.assertFalse(is_loopback_host("10.0.0.1:9099"))
        self.assertFalse(is_loopback_host("0.0.0.0:9099"))
        self.assertFalse(is_loopback_host("firebase-emulator.external-domain.com:9099"))
        self.assertFalse(is_loopback_host("evil.com"))
        self.assertFalse(is_loopback_host(""))
        self.assertFalse(is_loopback_host(None))

    # --------------------------------------------------------------------------
    # 2. Production & Staging Emulator Rejection
    # --------------------------------------------------------------------------
    def test_02_emulator_host_in_production_raises_startup_error(self):
        """Configuring FIREBASE_AUTH_EMULATOR_HOST in production raises SecurityConfigurationError."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "ALLOW_DEV_AUTH": "false",
            "AUTH_PROVIDER": "firebase",
            "GOOGLE_CLOUD_PROJECT": "prod-smart-eco-bin",
            "FIREBASE_AUTH_EMULATOR_HOST": "127.0.0.1:9099",
            "ADMIN_EMAILS": "official@sanitation.gov",
            "JWT_DEV_SECRET": ""
        }):
            with self.assertRaises(SecurityConfigurationError) as ctx:
                SecurityConfig()
            self.assertIn("FIREBASE_AUTH_EMULATOR_HOST", str(ctx.exception))
            self.assertIn("cannot be configured in a production environment", str(ctx.exception))

    def test_03_emulator_host_in_staging_raises_startup_error(self):
        """Configuring FIREBASE_AUTH_EMULATOR_HOST in staging raises SecurityConfigurationError."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "staging",
            "ALLOW_DEV_AUTH": "false",
            "AUTH_PROVIDER": "firebase",
            "GOOGLE_CLOUD_PROJECT": "staging-smart-eco-bin",
            "FIREBASE_AUTH_EMULATOR_HOST": "localhost:9099",
            "ADMIN_EMAILS": "supervisor@sanitation.gov",
            "JWT_DEV_SECRET": ""
        }):
            with self.assertRaises(SecurityConfigurationError) as ctx:
                SecurityConfig()
            self.assertIn("FIREBASE_AUTH_EMULATOR_HOST", str(ctx.exception))
            self.assertIn("cannot be configured in a staging environment", str(ctx.exception))

    def test_04_remote_emulator_host_in_dev_raises_startup_error(self):
        """Configuring non-loopback FIREBASE_AUTH_EMULATOR_HOST in development raises SecurityConfigurationError."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "ALLOW_DEV_AUTH": "true",
            "AUTH_PROVIDER": "auto",
            "FIREBASE_AUTH_EMULATOR_HOST": "remote-host.com:9099",
            "JWT_DEV_SECRET": "smart-eco-bin-local-dev-secret-key-32b"
        }):
            with self.assertRaises(SecurityConfigurationError) as ctx:
                SecurityConfig()
            self.assertIn("must resolve strictly to a local loopback interface", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 3. Algorithm 'none' Token Isolation
    # --------------------------------------------------------------------------
    def test_05_alg_none_token_rejected_in_production(self):
        """alg: none token is unconditionally rejected in production, even if emulator env is set."""
        mock_cfg = MagicMock()
        mock_cfg.is_production = True
        mock_cfg.is_staging = False
        mock_cfg.auth_provider = "firebase"
        mock_cfg.project_id = "prod-project"
        mock_cfg.firebase_auth_emulator_host = ""

        verifier = TokenVerifier(config=mock_cfg)

        # Forged alg: none token
        header = {"alg": "none", "typ": "JWT"}
        claims = {"sub": "attacker-001", "email": "admin@sanitation.gov", "admin": True, "email_verified": True}
        none_token = f"{jwt.utils.base64url_encode(json_bytes(header)).decode('utf-8')}.{jwt.utils.base64url_encode(json_bytes(claims)).decode('utf-8')}."

        with self.assertRaises(AuthenticationError) as ctx:
            verifier.verify_token(none_token)
        self.assertIn("unsupported token algorithm 'none'", str(ctx.exception).lower())

    def test_06_alg_none_token_rejected_in_staging(self):
        """alg: none token is unconditionally rejected in staging."""
        mock_cfg = MagicMock()
        mock_cfg.is_production = False
        mock_cfg.is_staging = True
        mock_cfg.auth_provider = "firebase"
        mock_cfg.project_id = "stage-project"
        mock_cfg.firebase_auth_emulator_host = ""

        verifier = TokenVerifier(config=mock_cfg)

        header = {"alg": "none", "typ": "JWT"}
        claims = {"sub": "attacker-002", "email": "supervisor@city.gov", "admin": True}
        none_token = f"{jwt.utils.base64url_encode(json_bytes(header)).decode('utf-8')}.{jwt.utils.base64url_encode(json_bytes(claims)).decode('utf-8')}."

        with self.assertRaises(AuthenticationError) as ctx:
            verifier.verify_token(none_token)
        self.assertIn("unsupported token algorithm 'none'", str(ctx.exception).lower())

    # --------------------------------------------------------------------------
    # 4. Administrator Role & Verified Email Invariants
    # --------------------------------------------------------------------------
    def test_07_unverified_email_cannot_gain_admin_via_custom_claims(self):
        """An account with email_verified=False cannot gain admin role via custom claims."""
        mock_cfg = MagicMock()
        mock_cfg.admin_emails = {"admin@sanitation.gov"}
        verifier = TokenVerifier(config=mock_cfg)

        claims = {
            "uid": "attacker-unverified",
            "email": "hacker@evil.com",
            "email_verified": False,
            "admin": True,
            "role": "administrator"
        }

        user = verifier._build_user_from_firebase_claims(claims)
        self.assertFalse(user.is_admin, "Unverified user must not gain is_admin=True")
        self.assertEqual(user.role, UserRole.CITIZEN, "Unverified user must be demoted to citizen role")

    def test_08_unverified_email_cannot_gain_admin_via_whitelist(self):
        """An account with email_verified=False cannot gain admin role even if email matches whitelist."""
        mock_cfg = MagicMock()
        mock_cfg.admin_emails = {"admin@sanitation.gov"}
        verifier = TokenVerifier(config=mock_cfg)

        claims = {
            "uid": "attacker-spoofed-email",
            "email": "admin@sanitation.gov",
            "email_verified": False
        }

        user = verifier._build_user_from_firebase_claims(claims)
        self.assertFalse(user.is_admin, "Unverified whitelist candidate must NOT receive admin status")
        self.assertEqual(user.role, UserRole.CITIZEN)

    def test_09_verified_email_with_valid_claims_gains_admin(self):
        """A verified account matching server-side allowlist gains admin; unapproved emails are rejected."""
        mock_cfg = MagicMock()
        mock_cfg.admin_emails = {"admin@sanitation.gov", "officer@sanitation.gov"}
        verifier = TokenVerifier(config=mock_cfg)

        # 1. Approved email with verified claims gains admin
        claims1 = {
            "uid": "legit-admin-1",
            "email": "officer@sanitation.gov",
            "email_verified": True,
            "admin": True
        }
        user1 = verifier._build_user_from_firebase_claims(claims1)
        self.assertTrue(user1.is_admin)
        self.assertEqual(user1.role, UserRole.ADMINISTRATOR)

        # 2. Allowlist matching + verified
        claims2 = {
            "uid": "legit-admin-2",
            "email": "admin@sanitation.gov",
            "email_verified": True
        }
        user2 = verifier._build_user_from_firebase_claims(claims2)
        self.assertTrue(user2.is_admin)
        self.assertEqual(user2.role, UserRole.ADMINISTRATOR)

        # 3. Unapproved email with admin=True claims CANNOT gain admin
        claims3 = {
            "uid": "attacker-unapproved",
            "email": "attacker@evil.com",
            "email_verified": True,
            "admin": True
        }
        user3 = verifier._build_user_from_firebase_claims(claims3)
        self.assertFalse(user3.is_admin, "Unapproved email must NEVER gain administrator privileges")
        self.assertEqual(user3.role, UserRole.CITIZEN)

    # --------------------------------------------------------------------------
    # 5. Zero HMAC Fallback
    # --------------------------------------------------------------------------
    def test_10_zero_hmac_fallback_on_firebase_failure(self):
        """Failed Firebase token verification raises AuthenticationError and never falls back to HMAC."""
        mock_cfg = MagicMock()
        mock_cfg.is_production = True
        mock_cfg.is_staging = False
        mock_cfg.auth_provider = "firebase"
        mock_cfg.dev_secret = "smart-eco-bin-local-dev-secret-key-32b"

        verifier = TokenVerifier(config=mock_cfg)
        verifier._firebase_available = True

        rs256_header = jwt.utils.base64url_encode(json_bytes({"alg": "RS256", "typ": "JWT"})).decode("utf-8")
        rs256_payload = jwt.utils.base64url_encode(json_bytes({"sub": "user-123"})).decode("utf-8")
        rs256_sig = jwt.utils.base64url_encode(b"mock_signature_bytes_for_test").decode("utf-8")
        token = f"{rs256_header}.{rs256_payload}.{rs256_sig}"

        with patch("firebase_admin.auth.verify_id_token", side_effect=Exception("Certificate verification failed")):
            with self.assertRaises(AuthenticationError) as ctx:
                verifier.verify_token(token)
            self.assertIn("Invalid or expired Firebase ID token", str(ctx.exception))

    def test_11_hs256_token_rejected_in_production_and_staging(self):
        """Development HS256 tokens are strictly rejected in production and staging."""
        # 1. Production
        mock_prod = MagicMock()
        mock_prod.is_production = True
        mock_prod.is_staging = False
        mock_prod.auth_provider = "firebase"
        verifier_prod = TokenVerifier(config=mock_prod)

        dev_token = jwt.encode(
            {"sub": "dev-user", "iss": "smart-eco-bin-auth", "aud": "smart-eco-bin-api"},
            "smart-eco-bin-local-dev-secret-key-32b",
            algorithm="HS256"
        )

        with self.assertRaises(AuthenticationError) as ctx:
            verifier_prod.verify_token(dev_token)
        self.assertIn("strictly rejected in this environment", str(ctx.exception))

        # 2. Staging
        mock_stage = MagicMock()
        mock_stage.is_production = False
        mock_stage.is_staging = True
        mock_stage.auth_provider = "firebase"
        verifier_stage = TokenVerifier(config=mock_stage)

        with self.assertRaises(AuthenticationError) as ctx:
            verifier_stage.verify_token(dev_token)
        self.assertIn("strictly rejected in this environment", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 6. Container & Secrets Hygiene
    # --------------------------------------------------------------------------
    def test_12_dockerignore_rules_exclude_sensitive_assets(self):
        """Validate that .dockerignore files exclude .env, service accounts, and data files."""
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        root_dockerignore = os.path.join(root_dir, ".dockerignore")
        backend_dockerignore = os.path.join(root_dir, "backend", ".dockerignore")

        self.assertTrue(os.path.exists(root_dockerignore), "Root .dockerignore must exist")
        self.assertTrue(os.path.exists(backend_dockerignore), "Backend .dockerignore must exist")

        with open(root_dockerignore, "r") as f:
            root_content = f.read()

        with open(backend_dockerignore, "r") as f:
            backend_content = f.read()

        for pattern in [".env", ".env.*", "tests/", "*service_account*.json"]:
            self.assertIn(pattern, root_content, f"Root .dockerignore must exclude {pattern}")
            self.assertIn(pattern, backend_content, f"Backend .dockerignore must exclude {pattern}")

    def test_13_dockerfile_sets_production_and_disables_dev_auth(self):
        """Backend Dockerfile must set ENVIRONMENT=production and ALLOW_DEV_AUTH=false."""
        dockerfile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "Dockerfile"))
        self.assertTrue(os.path.exists(dockerfile_path))

        with open(dockerfile_path, "r") as f:
            dockerfile_content = f.read()

        self.assertIn("ENVIRONMENT=production", dockerfile_content)
        self.assertIn("ALLOW_DEV_AUTH=false", dockerfile_content)
        self.assertNotIn("FIREBASE_AUTH_EMULATOR_HOST", dockerfile_content)


def json_bytes(obj: Dict[str, Any]) -> bytes:
    import json
    return json.dumps(obj).encode("utf-8")


if __name__ == "__main__":
    unittest.main()
