"""
SMART ECO BIN — Authentication & Authorisation Models
=====================================================
Defines authoritative user identity structures, supported roles, and token claims.
Prevents privilege escalation and client-side impersonation.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class UserRole:
    CITIZEN = "citizen"
    ADMINISTRATOR = "administrator"
    ALL_ROLES = [CITIZEN, ADMINISTRATOR]


class AuthenticatedUser(BaseModel):
    """
    Authoritative server-side verified user session representation.
    Populated solely from cryptographically verified tokens and server-side role lists.
    """
    uid: str = Field(..., description="Unique immutable subject identifier (sub/uid)")
    email: Optional[str] = Field(None, description="Verified email address if available")
    role: str = Field(UserRole.CITIZEN, description="Assigned role ('citizen' or 'administrator')")
    is_admin: bool = Field(False, description="Flag indicating administrative access privileges")
    auth_time: Optional[int] = Field(None, description="Unix timestamp of authentication")
    token_issuer: Optional[str] = Field(None, description="Issuer of the validated token")
    claims: Dict[str, Any] = Field(default_factory=dict, description="Raw validated token claims")


class TokenVerificationResponse(BaseModel):
    valid: bool
    user: Optional[AuthenticatedUser] = None
    role: Optional[str] = None
    is_admin: bool = False
    message: Optional[str] = None


class DemoTokenRequest(BaseModel):
    email: str = Field(..., description="User email for development evaluation")
    role: str = Field(UserRole.CITIZEN, description="Requested role ('citizen' or 'administrator')")
    name: Optional[str] = Field("Authorized User", description="Display name")


class DemoTokenResponse(BaseModel):
    token: str
    token_type: str = "Bearer"
    expires_in: int
    user: AuthenticatedUser
    mode: str = "development_signed_token"
