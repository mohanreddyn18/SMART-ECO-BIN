"""
SMART ECO BIN — Server-Side Token Verification & Security Engine
================================================================
Validates identity tokens against Firebase Authentication, Google Cloud Identity
Platform, or signed cryptographic development tokens with strict production hardening.

Hardened Invariants:
- Rejects development tokens in production by default.
- Prevents silent fallback between Firebase/OIDC and development HMAC tokens.
- Refuses to issue dev tokens when a production provider is active.
- Verifies token algorithm (RS256 vs HS256) and prevents algorithm confusion.
- Server-side role resolution prevents privilege escalation.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, Tuple
import jwt
from app.auth.models import AuthenticatedUser, UserRole
from app.auth.config import security_config, SecurityConfigurationError, is_loopback_host

logger = logging.getLogger("ecosort.auth")


class AuthenticationError(Exception):
    """Raised when token verification fails."""
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class TokenVerifier:
    """
    Central server-side token verifier with hardened production defaults.
    """

    DEV_ISSUER = "smart-eco-bin-auth"
    DEV_AUDIENCE = "smart-eco-bin-api"

    def __init__(self, config=None):
        self.config = config or security_config
        self._firebase_available = False
        self._init_firebase_admin()

    @property
    def dev_secret(self) -> str:
        return self.config.dev_secret

    @property
    def is_dev_token_allowed(self) -> bool:
        """
        Determines whether development token issuance is permitted.
        Strictly fails closed:
        - Disabled in production and staging.
        - Disabled when auth_provider is firebase or oidc.
        - Disabled unless explicitly verified development environment.
        - Disabled if allow_dev_auth is False.
        """
        if getattr(self.config, "is_production", False) or getattr(self.config, "is_staging", False):
            return False
        if not getattr(self.config, "is_dev_environment", True):
            return False
        if getattr(self.config, "auth_provider", "auto") in ("firebase", "oidc"):
            return False
        return bool(getattr(self.config, "allow_dev_auth", False))

    @property
    def allow_dev_auth(self) -> bool:
        return self.is_dev_token_allowed

    @property
    def is_production(self) -> bool:
        return self.config.is_production

    @property
    def auth_provider(self) -> str:
        return self.config.auth_provider

    def _init_firebase_admin(self):
        """Initializes Firebase Admin SDK if credentials, project context, or emulator exist."""
        try:
            import firebase_admin
            from firebase_admin import auth
            if not firebase_admin._apps:
                cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                raw_emu = os.getenv("FIREBASE_AUTH_EMULATOR_HOST")
                emulator_host = raw_emu if not (self.is_production or self.config.is_staging) else None
                if (self.is_production or self.config.is_staging) and raw_emu:
                    logger.error("Security Warning: FIREBASE_AUTH_EMULATOR_HOST detected but ignored in production/staging environments.")
                elif emulator_host and not is_loopback_host(emulator_host):
                    logger.error(f"Security Warning: FIREBASE_AUTH_EMULATOR_HOST ('{emulator_host}') is not a loopback address. Ignored.")
                    emulator_host = None

                project_id = self.config.project_id or os.getenv("GCLOUD_PROJECT") or ("demo-smart-eco-bin" if emulator_host else "")

                if cred_path and os.path.exists(cred_path):
                    from firebase_admin import credentials
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred, {"projectId": project_id})
                    logger.info(f"Firebase Admin initialized with credentials file: {cred_path}")
                elif project_id:
                    firebase_admin.initialize_app(options={"projectId": project_id})
                    if emulator_host:
                        logger.info(f"Firebase Admin initialized with Auth Emulator: {emulator_host} (project: {project_id})")
                    else:
                        logger.info(f"Firebase Admin initialized with project ID: {project_id}")
            self._firebase_available = bool(firebase_admin._apps)
        except Exception as e:
            logger.debug(f"Firebase Admin SDK not initialized: {e}. Using configured provider mode.")
            self._firebase_available = False

    def verify_token(self, token: str) -> AuthenticatedUser:
        """
        Cryptographically verifies an incoming bearer token.
        Rejects missing, expired, forged, or wrong-algorithm tokens.
        Never silently falls back between production and development verification.
        """
        if not token or not isinstance(token, str):
            raise AuthenticationError("Missing or empty bearer token.", status_code=401)

        token = token.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        # Inspect token header without verification to prevent algorithm confusion
        try:
            header = jwt.get_unverified_header(token)
            alg = header.get("alg")
        except Exception as e:
            raise AuthenticationError(f"Malformed token header: {str(e)}", status_code=401)

        if not alg:
            raise AuthenticationError("Token missing algorithm ('alg') header.", status_code=401)

        # Local emulator mode support (strictly prohibited and guarded against in prod/staging)
        raw_emulator_host = os.getenv("FIREBASE_AUTH_EMULATOR_HOST") or self.config.firebase_auth_emulator_host
        is_emulator_active = (
            not self.config.is_production
            and not self.config.is_staging
            and bool(raw_emulator_host)
            and is_loopback_host(raw_emulator_host)
            and self.config.auth_provider in ("firebase", "auto")
            and self._firebase_available
        )

        # ----------------------------------------------------------------------
        # Case A: Asymmetric RS256 Token (Firebase Authentication / Google OIDC)
        #         (or 'none' algorithm strictly when local Firebase Emulator is active)
        # ----------------------------------------------------------------------
        if alg == "RS256" or (alg == "none" and is_emulator_active):
            if self.config.auth_provider == "oidc":
                return self._verify_google_oidc(token)
            
            # Default to Firebase verification
            if self._firebase_available:
                try:
                    from firebase_admin import auth
                    decoded_claims = auth.verify_id_token(token, check_revoked=True)
                    return self._build_user_from_firebase_claims(decoded_claims)
                except Exception as e:
                    logger.warning(f"Firebase token verification failed: {e}")
                    # Strict: Never fall back to HMAC on failed verification
                    raise AuthenticationError(f"Invalid or expired Firebase ID token: {str(e)}", status_code=401)
            else:
                # If identity token received but Firebase is not connected
                raise AuthenticationError(
                    "Received identity token but Firebase Admin credentials are not configured.",
                    status_code=401
                )

        # ----------------------------------------------------------------------
        # Case B: Symmetric HS256 Token (Development / Local Evaluation Only)
        # ----------------------------------------------------------------------
        elif alg == "HS256":
            # Production & Staging Guard: Strict rejection in production, staging, unverified env, under IDP, or if dev auth is disabled
            if (
                self.config.is_production
                or self.config.is_staging
                or not getattr(self.config, "is_dev_environment", False)
                or self.config.auth_provider in ("firebase", "oidc")
                or not self.config.allow_dev_auth
            ):
                raise AuthenticationError(
                    "Development-only HMAC tokens are strictly rejected in this environment. "
                    "Production identity provider authentication required.",
                    status_code=401
                )

            return self._verify_dev_token(token)

        # ----------------------------------------------------------------------
        # Case C: Unsupported Algorithm
        # ----------------------------------------------------------------------
        else:
            if alg == "none":
                raise AuthenticationError(
                    "Unsupported token algorithm 'none'. Algorithm 'none' tokens are strictly rejected. Emulator tokens are only permitted "
                    "when running against an authorized local loopback emulator in development.",
                    status_code=401
                )
            raise AuthenticationError(
                f"Unsupported token algorithm '{alg}'. Only RS256 (Identity Provider) and HS256 (Dev) are allowed.",
                status_code=401
            )

    def _verify_dev_token(self, token: str) -> AuthenticatedUser:
        """
        Verifies cryptographically signed HMAC-SHA256 tokens issued for development.
        Strictly verifies signature, expiration, issuer, audience, and server-side roles.
        """
        try:
            payload = jwt.decode(
                token,
                self.config.dev_secret,
                algorithms=["HS256"],
                issuer=self.DEV_ISSUER,
                audience=self.DEV_AUDIENCE,
                options={"require": ["exp", "iss", "aud", "sub"]}
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Authentication token has expired. Please sign in again.", status_code=401)
        except jwt.InvalidSignatureError:
            raise AuthenticationError("Token signature verification failed. Forged or corrupted token.", status_code=401)
        except jwt.InvalidIssuerError:
            raise AuthenticationError("Invalid token issuer claim.", status_code=401)
        except jwt.InvalidAudienceError:
            raise AuthenticationError("Invalid token audience claim.", status_code=401)
        except Exception as e:
            raise AuthenticationError(f"Token decoding failed: {str(e)}", status_code=401)

        uid = payload.get("sub")
        email = payload.get("email")
        claims_role = payload.get("role", UserRole.CITIZEN)

        # Server-side authoritative role determination:
        # Never grant administrator privileges solely because a request supplies role="administrator" or admin=true.
        # Administrator privileges strictly require:
        # 1. Email is present and exists in self.config.admin_emails allowlist.
        # 2. Token payload was genuinely issued with administrator privileges.
        is_admin = False
        if email and email.lower() in self.config.admin_emails:
            if payload.get("admin") is True and claims_role == UserRole.ADMINISTRATOR:
                is_admin = True

        resolved_role = UserRole.ADMINISTRATOR if is_admin else UserRole.CITIZEN

        return AuthenticatedUser(
            uid=uid,
            email=email,
            role=resolved_role,
            is_admin=is_admin,
            auth_time=payload.get("auth_time", int(time.time())),
            token_issuer=payload.get("iss"),
            claims=payload
        )

    def _build_user_from_firebase_claims(self, claims: Dict[str, Any]) -> AuthenticatedUser:
        """
        Constructs AuthenticatedUser from validated Firebase Authentication token claims.
        Enforces server-side authorization policy:
        - Administrator privileges require verified email (email_verified=True).
        - Administrator privileges require verified custom claims set by the trusted identity provider (Firebase Admin SDK)
          OR email to match the server-side admin_emails allowlist.
        - Unverified accounts cannot gain administrative privileges under any circumstances.
        """
        uid = claims.get("uid") or claims.get("sub")
        email = claims.get("email")
        email_verified = bool(claims.get("email_verified") is True)

        # Authoritative server-side role resolution:
        # Administrator status STRICTLY requires email_verified is True.
        # If server-side admin_emails allowlist is configured, email MUST match allowlist.
        # Otherwise, custom claims from trusted IdP (Firebase Admin SDK) are evaluated.
        is_admin = False
        if email_verified and email:
            email_clean = email.strip().lower()
            admin_emails = getattr(self.config, "admin_emails", set())
            if admin_emails:
                if email_clean in admin_emails:
                    is_admin = True
            else:
                if claims.get("admin") is True or claims.get("role") == UserRole.ADMINISTRATOR:
                    is_admin = True

        resolved_role = UserRole.ADMINISTRATOR if is_admin else UserRole.CITIZEN

        return AuthenticatedUser(
            uid=uid,
            email=email,
            role=resolved_role,
            is_admin=is_admin,
            auth_time=claims.get("auth_time"),
            token_issuer=claims.get("iss"),
            claims=claims
        )

    def _verify_google_oidc(self, token: str) -> AuthenticatedUser:
        """Verifies Google Cloud Identity Platform / Google Workspace OIDC tokens using Google certs."""
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests
            request = requests.Request()
            claims = id_token.verify_oauth2_token(token, request, audience=self.config.project_id)
            return self._build_user_from_firebase_claims(claims)
        except Exception as e:
            raise AuthenticationError(f"Google OIDC token verification failed: {e}", status_code=401)

    def issue_dev_token(
        self,
        email: str,
        role: str = UserRole.CITIZEN,
        name: str = "Authorized User",
        expires_in_seconds: int = 3600
    ) -> Tuple[str, AuthenticatedUser]:
        """
        Issues a cryptographically signed HMAC token for local development evaluation.
        Refuses to issue if development auth is disabled, in production, in staging,
        or when a production identity provider is explicitly configured.

        Security Invariants:
        1. Fails closed: Disabled in production, staging, or unknown environments.
        2. Never grants administrator privileges solely because caller requested role="administrator".
        3. Administrator tokens strictly require caller email to match the server-side admin_emails allowlist.
        4. Unapproved emails requesting administrator role are rejected with PermissionError.
        """
        is_prod = getattr(self.config, "is_production", False) is True
        is_staging = getattr(self.config, "is_staging", False) is True
        allow_dev = getattr(self.config, "allow_dev_auth", False) is True
        auth_provider = getattr(self.config, "auth_provider", "")
        dev_token_allowed = getattr(self.config, "is_dev_token_allowed", None)

        if is_prod or (dev_token_allowed is False and not is_staging and auth_provider not in ("firebase", "oidc")):
            raise PermissionError("Development token issuance is strictly prohibited in production environments.")

        if is_staging:
            raise PermissionError("Development token issuance is strictly prohibited in staging environments.")

        if auth_provider in ("firebase", "oidc"):
            raise PermissionError(
                f"Development tokens cannot be issued when a production identity provider ('{auth_provider}') is configured."
            )

        if not allow_dev or not getattr(self.config, "is_dev_environment", True):
            raise PermissionError("Development token issuance is strictly prohibited in production and staging environments.")

        email_clean = (email or "").strip().lower()
        if not email_clean:
            raise ValueError("A valid email address is required for development token issuance.")

        # Enforce strict server-side check on administrator privileges
        requested_admin = (role == UserRole.ADMINISTRATOR)
        is_approved_admin_email = bool(email_clean in self.config.admin_emails)

        if requested_admin:
            if not is_approved_admin_email:
                logger.warning(
                    f"Unauthorized admin token issuance attempt rejected for email '{email_clean}'. "
                    "Caller email is not in server-side admin_emails allowlist."
                )
                raise PermissionError(
                    f"Access Denied: Email '{email_clean}' is not authorized for administrator privileges. "
                    "Administrator tokens require explicit server-side allowlist approval."
                )
            is_admin = True
            resolved_role = UserRole.ADMINISTRATOR
        else:
            # Requested citizen role: citizen tokens NEVER have admin privileges
            is_admin = False
            resolved_role = UserRole.CITIZEN

        now = int(time.time())
        exp = now + expires_in_seconds
        sub = f"dev-uid-{email_clean.replace('@', '-at-').replace('.', '-')}"

        payload = {
            "sub": sub,
            "iss": self.DEV_ISSUER,
            "aud": self.DEV_AUDIENCE,
            "iat": now,
            "exp": exp,
            "auth_time": now,
            "email": email_clean,
            "name": name,
            "role": resolved_role,
            "admin": is_admin
        }

        token = jwt.encode(payload, self.config.dev_secret, algorithm="HS256")
        user = AuthenticatedUser(
            uid=sub,
            email=email_clean,
            role=resolved_role,
            is_admin=is_admin,
            auth_time=now,
            token_issuer=self.DEV_ISSUER,
            claims=payload
        )
        return token, user

    def get_security_status(self) -> Dict[str, Any]:
        """Returns safe public operational security metadata."""
        return {
            "environment": self.config.environment,
            "is_production": self.config.is_production,
            "is_staging": getattr(self.config, "is_staging", False),
            "auth_provider": "firebase_admin" if self._firebase_available else "development_signed_tokens",
            "firebase_admin_connected": self._firebase_available,
            "allow_dev_auth": self.config.allow_dev_auth,
            "server_side_verification_active": True,
            "rbac_enforced": True,
            "trusted_admin_domains_configured": bool(self.config.admin_emails),
            "token_algorithms_supported": ["RS256"] if (self.config.is_production or self.config.auth_provider in ("firebase", "oidc")) else ["RS256", "HS256 (Dev)"]
        }


# Global singleton verifier
token_verifier = TokenVerifier()
