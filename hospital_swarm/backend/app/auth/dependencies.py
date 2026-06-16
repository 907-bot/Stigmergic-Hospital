from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.auth.auth import decode_token
from app.auth.models import TokenData, TenantRole

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> TokenData:
    """Dependency that extracts and validates JWT. Returns TokenData or raises 401."""
    token = None
    if credentials:
        token = credentials.credentials
    if not token:
        token = request.headers.get("X-API-Key")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Provide Bearer token or X-API-Key header.",
        )

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return TokenData(
        user_id=payload.get("sub"),
        tenant_id=payload.get("tenant_id"),
        role=payload.get("role"),
        scopes=payload.get("scopes", []),
    )


async def optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[TokenData]:
    """Like get_current_user but returns None instead of 401."""
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if payload is None:
        return None
    return TokenData(
        user_id=payload.get("sub"),
        tenant_id=payload.get("tenant_id"),
        role=payload.get("role"),
    )


def require_role(allowed_roles: list[TenantRole]):
    """Dependency factory: requires the user to have one of the allowed roles."""

    async def role_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized. Required: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker


ROLE_HIERARCHY = {
    TenantRole.admin: 100,
    TenantRole.doctor: 80,
    TenantRole.clinician: 70,
    TenantRole.nurse: 60,
    TenantRole.lab: 50,
    TenantRole.pharmacy: 50,
    TenantRole.icu: 50,
    TenantRole.ambulance: 50,
    TenantRole.viewer: 10,
}


def role_ge(required: TenantRole):
    """Allows users whose role level >= required level."""

    async def checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        user_level = ROLE_HIERARCHY.get(current_user.role, 0)
        req_level = ROLE_HIERARCHY.get(required, 0)
        if user_level < req_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges. Need at least {required.value}.",
            )
        return current_user

    return checker
