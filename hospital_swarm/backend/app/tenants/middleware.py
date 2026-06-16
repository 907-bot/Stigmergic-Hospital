"""
Tenant isolation middleware.

Every request to a scoped endpoint extracts the tenant_id from the
authenticated user's JWT and attaches it to request.state.tenant_id.

Services use this to filter queries by tenant_id, ensuring complete
data isolation between hospital customers.
"""

from fastapi import Request, HTTPException, status
from app.auth.dependencies import get_current_user
from app.auth.models import TokenData
from app.core.config import settings


async def resolve_tenant(request: Request) -> str | None:
    """
    Extract tenant_id from the request.
    Priority: 1. JWT token  2. Header  3. Default tenant
    """
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]

    api_key = request.headers.get("X-Tenant-ID")

    if token:
        from app.auth.auth import decode_token

        payload = decode_token(token)
        if payload and payload.get("tenant_id"):
            return payload["tenant_id"]

    if api_key:
        return api_key

    # Single-tenant mode: return default
    if not settings.ENABLE_MULTI_TENANT:
        return "default"

    return None


async def tenant_dependency(request: Request) -> str:
    """FastAPI dependency that ensures a tenant context exists."""
    tenant_id = await resolve_tenant(request)
    if not tenant_id and settings.ENABLE_MULTI_TENANT:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Multi-tenant mode requires authentication",
        )
    return tenant_id or "default"
