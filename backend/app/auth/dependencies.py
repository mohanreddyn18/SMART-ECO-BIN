"""
SMART ECO BIN — FastAPI Security Dependencies & RBAC Guards
===========================================================
Provides reusable dependency injection functions for endpoint protection:
- get_current_user: Enforces valid bearer token (401 if missing/invalid/expired).
- get_optional_current_user: Extracts identity if bearer token provided (None if anonymous).
- require_admin: Enforces verified administrator role (403 if authenticated non-admin).
- require_citizen_or_admin: Enforces valid authenticated role.
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.models import AuthenticatedUser, UserRole
from app.auth.security import token_verifier, AuthenticationError

logger = logging.getLogger("ecosort.auth.deps")

# FastAPI standard Bearer schema
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> AuthenticatedUser:
    """
    Enforces valid bearer token authentication.
    Returns the authenticated user.
    Raises HTTP 401 Unauthorized if missing, malformed, invalid, or expired.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        user = token_verifier.verify_token(credentials.credentials)
        return user
    except AuthenticationError as e:
        logger.warning(f"Authentication failure: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""}
        )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[AuthenticatedUser]:
    """
    Optional authentication for endpoints that support both anonymous citizen
    intake and authenticated citizen interactions (e.g., /api/predict, /api/wasteai).
    """
    if not credentials or not credentials.credentials:
        return None

    try:
        return token_verifier.verify_token(credentials.credentials)
    except AuthenticationError as e:
        # If a token was explicitly supplied but is invalid or expired, reject with 401
        logger.warning(f"Optional token validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {e.message}",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""}
        )


async def require_admin(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """
    Enforces Role-Based Access Control: Administrator only.
    Returns authenticated user if verified as administrator.
    Raises HTTP 403 Forbidden if user lacks administrator privileges.
    """
    if not current_user.is_admin or current_user.role != UserRole.ADMINISTRATOR:
        logger.warning(f"Access denied: User '{current_user.uid}' ({current_user.email}) attempted to access admin endpoint.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: This operational console requires verified administrator privileges."
        )
    return current_user


async def require_citizen_or_admin(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """
    Ensures user is an authenticated citizen or administrator.
    """
    if current_user.role not in UserRole.ALL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Unrecognized user role."
        )
    return current_user
