"""
SMART ECO BIN — Centralized Security & Authentication Configuration Engine
==========================================================================
Enforces production-grade validation at startup and runtime:
- Disables development authentication by default in production environments.
- Rejects known example/insecure secrets and weak keys (< 32 bytes).
- Rejects development token issuance when a production identity provider is configured.
- Prevents silent fallback between Firebase/OIDC and HMAC tokens.
- Ensures error messages describe the defect without printing sensitive secrets.
"""

import os
import logging
from typing import Set, Optional

logger = logging.getLogger("ecosort.auth.config")

KNOWN_INSECURE_SECRETS: Set[str] = {
    "smart-eco-bin-local-dev-secret-key-32b",
    "smart-eco-bin-dev-insecure-secret-key-32b",
    "secret",
    "changeme",
    "password",
    "12345678",
    "development",
    "jwt_secret",
    "default_secret",
    "supersecret",
    "your-jwt-secret-key"
}


KNOWN_DEV_ENVIRONMENTS: Set[str] = {"development", "dev", "local", "test", "testing"}
KNOWN_PROD_ENVIRONMENTS: Set[str] = {"production", "prod"}
KNOWN_STAGING_ENVIRONMENTS: Set[str] = {"staging", "stage"}


def is_loopback_host(host_str: Optional[str]) -> bool:
    """
    Validates whether a host address string resolves strictly to a local loopback interface.
    Accepts formats such as '127.0.0.1:9099', 'localhost:9099', '[::1]:9099', '127.0.0.1', 'localhost', '::1'.
    Rejects any remote IPs, external hostnames, wildcards (0.0.0.0), or empty strings.
    """
    if not host_str:
        return False
    host = host_str.strip()
    if "://" in host:
        host = host.split("://", 1)[1]
    host = host.split("/")[0]
    if host.startswith("[") and "]" in host:
        host = host[1:host.index("]")]
    elif host.startswith("["):
        return False
    elif host == "::1":
        host = "::1"
    elif ":" in host and host.count(":") == 1:
        # IPv4 or hostname with port, e.g. 127.0.0.1:9099 or localhost:9099
        host = host.split(":", 1)[0]
    return host.lower() in ("127.0.0.1", "localhost", "::1")


class SecurityConfigurationError(Exception):
    """Raised when security configuration violates environment safety constraints."""
    pass


class SecurityConfig:
    """Central validated security configuration model."""

    def __init__(self):
        self.reload()

    def reload(self):
        """Reloads and strictly validates environment configuration with fail-closed semantics."""
        raw_env = os.getenv("ENVIRONMENT") or os.getenv("ENV") or ""
        norm_env = raw_env.strip().lower()

        # Fail-closed environment determination:
        # Only explicitly recognized development strings enable dev features.
        # Any empty, ambiguous, staging, or production strings disable dev token issuance.
        if norm_env in KNOWN_DEV_ENVIRONMENTS:
            self.environment = norm_env
            self.is_dev_environment = True
            self.is_production = False
            self.is_staging = False
        elif norm_env in KNOWN_STAGING_ENVIRONMENTS:
            self.environment = norm_env
            self.is_dev_environment = False
            self.is_production = False
            self.is_staging = True
        elif norm_env in KNOWN_PROD_ENVIRONMENTS:
            self.environment = norm_env
            self.is_dev_environment = False
            self.is_production = True
            self.is_staging = False
        else:
            # Ambiguous or unknown environment: Fail closed by treating as production
            self.environment = norm_env or "production"
            self.is_dev_environment = False
            self.is_production = True
            self.is_staging = False
            logger.warning(
                f"[SECURITY NOTICE] Environment '{raw_env}' cannot be safely determined as development. "
                "Failing closed: treating environment as production with development features disabled."
            )

        self.auth_provider = os.getenv("AUTH_PROVIDER", "auto").strip().lower()
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("FIREBASE_PROJECT_ID") or ""
        self.firebase_auth_emulator_host = os.getenv("FIREBASE_AUTH_EMULATOR_HOST", "").strip()

        # Dev auth flag: strictly False in production, staging, or unverified environments
        raw_dev_auth = os.getenv("ALLOW_DEV_AUTH")
        if self.is_production or self.is_staging or not self.is_dev_environment:
            self.allow_dev_auth = False
        else:
            self.allow_dev_auth = True if raw_dev_auth is None else (raw_dev_auth.strip().lower() == "true")

        self.dev_secret = os.getenv("JWT_DEV_SECRET", "").strip()
        if not self.dev_secret and self.is_dev_environment and not self.is_production and not self.is_staging:
            # Fallback for local dev testing only
            self.dev_secret = "smart-eco-bin-local-dev-secret-key-32b"

        # Admin whitelist configuration
        raw_admin_emails = os.getenv("ADMIN_EMAILS", "")
        if raw_admin_emails:
            self.admin_emails = {e.strip().lower() for e in raw_admin_emails.split(",") if e.strip()}
        elif self.is_dev_environment and not self.is_production and not self.is_staging:
            # Default development admin email for local evaluation only
            self.admin_emails = {
                "admin@ecosortai.com",
                "admin@city.gov",
                "lead@sanitation.gov",
                "supervisor@sanitation.gov",
            }
        else:
            # In production or staging, never default to a placeholder account
            self.admin_emails = set()

        self.validate()

    @property
    def is_dev_token_allowed(self) -> bool:
        """
        Determines whether development token issuance (/demo-token) is permitted.
        Strictly fails closed:
        - Must NOT be production.
        - Must NOT be staging.
        - Must be an explicitly recognized development environment.
        - Must NOT have a production auth provider (firebase/oidc) configured.
        - allow_dev_auth must be True.
        """
        if self.is_production or self.is_staging or not self.is_dev_environment:
            return False
        if self.auth_provider in ("firebase", "oidc"):
            return False
        return bool(self.allow_dev_auth)

    def validate(self):
        """Enforces strict production and staging security invariants."""
        raw_dev_auth = os.getenv("ALLOW_DEV_AUTH", "").strip().lower()

        # 1. Production invariants
        if self.is_production:
            if raw_dev_auth == "true" or self.allow_dev_auth:
                raise SecurityConfigurationError(
                    "Production Startup Rejected: Development authentication (ALLOW_DEV_AUTH) cannot be "
                    "enabled in a production environment."
                )

            if self.auth_provider in ("dev", "development"):
                raise SecurityConfigurationError(
                    "Production Startup Rejected: AUTH_PROVIDER cannot be 'development' in production. "
                    "Must be configured to 'firebase' or 'oidc'."
                )

            if self.dev_secret and self.dev_secret in KNOWN_INSECURE_SECRETS:
                raise SecurityConfigurationError(
                    "Production Startup Rejected: The environment contains a known public development "
                    "secret key in JWT_DEV_SECRET. Production requires verified identity provider tokens."
                )

            # Check for placeholder admin emails
            for email in self.admin_emails:
                if email in ("admin@ecosortai.com", "admin@example.com", "test@example.com") or email.endswith("@example.com"):
                    raise SecurityConfigurationError(
                        f"Production Startup Rejected: Insecure placeholder administrator email '{email}' detected. "
                        "Production requires verified institutional or organizational administrator accounts."
                    )

            if self.firebase_auth_emulator_host:
                raise SecurityConfigurationError(
                    f"Production Startup Rejected: FIREBASE_AUTH_EMULATOR_HOST ('{self.firebase_auth_emulator_host}') "
                    "cannot be configured in a production environment. Production must connect to live identity provider certificates."
                )

            if self.auth_provider == "firebase" and not self.project_id:
                raise SecurityConfigurationError(
                    "Production Startup Rejected: Google Cloud Project ID (GOOGLE_CLOUD_PROJECT or FIREBASE_PROJECT_ID) "
                    "must be configured when AUTH_PROVIDER is 'firebase'."
                )

        # 2. Staging invariants (Validation Gate for Staging Identity Integration)
        if self.is_staging:
            if raw_dev_auth == "true" or self.allow_dev_auth:
                raise SecurityConfigurationError(
                    "Staging Startup Rejected: Development authentication (ALLOW_DEV_AUTH) cannot be "
                    "enabled in a staging environment."
                )

            if self.firebase_auth_emulator_host:
                raise SecurityConfigurationError(
                    f"Staging Startup Rejected: FIREBASE_AUTH_EMULATOR_HOST ('{self.firebase_auth_emulator_host}') "
                    "cannot be configured in a staging environment. Staging must validate genuine identity provider configuration."
                )

            if self.auth_provider in ("firebase", "oidc"):
                if not self.project_id:
                    raise SecurityConfigurationError(
                        "Staging Startup Rejected: Google Cloud Project ID (GOOGLE_CLOUD_PROJECT or FIREBASE_PROJECT_ID) "
                        "must be configured for staging identity integration."
                    )

            for email in self.admin_emails:
                if email in ("admin@ecosortai.com", "admin@example.com", "test@example.com") or email.endswith("@example.com"):
                    raise SecurityConfigurationError(
                        f"Staging Startup Rejected: Placeholder administrator email '{email}' detected in staging. "
                        "Staging requires configured authorized administrator accounts."
                    )

        # 3. Development safety rules
        if not self.is_production and not self.is_staging:
            if self.firebase_auth_emulator_host:
                if not is_loopback_host(self.firebase_auth_emulator_host):
                    raise SecurityConfigurationError(
                        f"Development Security Invariant Violated: FIREBASE_AUTH_EMULATOR_HOST ('{self.firebase_auth_emulator_host}') "
                        "must resolve strictly to a local loopback interface (127.0.0.1, localhost, or ::1). "
                        "Remote emulator endpoints are strictly forbidden to prevent SSRF and token forgery."
                    )

        # 2. Development safety rules
        if not self.is_production and self.allow_dev_auth:
            if len(self.dev_secret.encode("utf-8")) < 32:
                raise SecurityConfigurationError(
                    "Development Security Invariant Violated: JWT_DEV_SECRET must be at least 32 bytes "
                    "(256 bits) in length for HMAC-SHA256 signature security."
                )
            if self.dev_secret in KNOWN_INSECURE_SECRETS:
                logger.warning(
                    "[SECURITY NOTICE] Local evaluation is using a known public demonstration key. "
                    "This key is strictly forbidden and rejected in production environments."
                )


# Global validated configuration instance
security_config = SecurityConfig()
