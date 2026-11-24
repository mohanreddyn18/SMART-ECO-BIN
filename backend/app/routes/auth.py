"""
SMART ECO BIN — Authentication & Verification API Routes
========================================================
Provides token validation, session resolution, and controlled development token issuance.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.auth.models import (
    AuthenticatedUser,
    TokenVerificationResponse,
    DemoTokenRequest,
    DemoTokenResponse,
    UserRole
)
from app.auth.security import token_verifier, AuthenticationError
from app.auth.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/users")
async def list_registered_users(
    page_token: str | None = Query(None),
    _current_user: AuthenticatedUser = Depends(require_admin),
):
    """Lists real Firebase users for the administrator directory."""
    try:
        import firebase_admin
        from firebase_admin import auth

        if not firebase_admin._apps:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Firebase Authentication is not connected on this backend.",
            )

        page = auth.list_users(max_results=1000, page_token=page_token)
        admin_emails = token_verifier.config.admin_emails
        users = []
        for user in page.users:
            claims = user.custom_claims or {}
            is_admin = bool(
                user.email_verified
                and (
                    user.email.lower() in admin_emails
                    if admin_emails
                    else claims.get("admin") is True
                    or claims.get("role") == UserRole.ADMINISTRATOR
                )
            )
            users.append({
                "id": user.uid,
                "name": user.display_name or user.email or user.uid,
                "email": user.email or "",
                "role": "administrator" if is_admin else "citizen",
                "emailVerified": user.email_verified,
                "createdAt": user.user_metadata.creation_timestamp,
            })

        return {"users": users, "nextPageToken": page.next_page_token}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase Authentication could not list registered users.",
        ) from error


@router.get("/me", response_model=AuthenticatedUser)
async def get_my_profile(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Returns the server-verified identity, role, and claims for the active session.
    """
    return current_user


@router.post("/verify", response_model=TokenVerificationResponse)
async def verify_token_endpoint(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Validates a supplied Bearer token against server-side signing keys and claims.
    Returns 200 with validated profile, or 401 if invalid/expired.
    """
    return TokenVerificationResponse(
        valid=True,
        user=current_user,
        role=current_user.role,
        is_admin=current_user.is_admin,
        message="Token cryptographically verified by server."
    )


@router.post("/demo-token", response_model=DemoTokenResponse)
async def issue_development_token(payload: DemoTokenRequest):
    """
    Issues a cryptographically signed HMAC-SHA256 token for development and local testing.
    Strictly disabled whenever the environment is production, staging, or cannot be safely determined.
    """
    cfg = token_verifier.config
    is_prod = getattr(cfg, "is_production", False)
    is_staging = getattr(cfg, "is_staging", False)
    is_dev = getattr(cfg, "is_dev_environment", True)
    allow_dev = getattr(cfg, "allow_dev_auth", False)
    auth_provider = getattr(cfg, "auth_provider", "")
    dev_allowed = getattr(cfg, "is_dev_token_allowed", True)

    if (
        is_prod
        or is_staging
        or not is_dev
        or not allow_dev
        or auth_provider in ("firebase", "oidc")
        or dev_allowed is False
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development token endpoint (/api/auth/demo-token) is disabled in production, staging, and non-development environments."
        )

    try:
        token, user = token_verifier.issue_dev_token(
            email=payload.email,
            role=payload.role,
            name=payload.name or "Authorized User"
        )
        return DemoTokenResponse(
            token=token,
            token_type="Bearer",
            expires_in=3600,
            user=user,
            mode="development_signed_token"
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Token issuance error: {e}")
