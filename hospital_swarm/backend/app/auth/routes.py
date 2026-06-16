from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.models import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    TenantCreate,
    TenantResponse,
    TenantRole,
)
from app.auth.auth import hash_password, verify_password, create_access_token
from app.auth.dependencies import get_current_user, require_role
from app.db.neo4j import run_query
from typing import List
from datetime import datetime
import uuid

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(req: UserCreate):
    existing = await run_query(
        "MATCH (u:User {email: $email}) RETURN u", {"email": req.email}
    )
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    tenant = await run_query(
        "MATCH (t:Tenant {tenant_id: $tenant_id}) RETURN t",
        {"tenant_id": req.tenant_id},
    )
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    user_id = f"U{uuid.uuid4().hex[:10]}"
    now = datetime.utcnow().isoformat()

    await run_query(
        """
        CREATE (u:User {
            user_id: $user_id,
            email: $email,
            password: $password,
            name: $name,
            tenant_id: $tenant_id,
            role: $role,
            is_active: true,
            created_at: $created_at
        })
        RETURN u
        """,
        {
            "user_id": user_id,
            "email": req.email,
            "password": hash_password(req.password),
            "name": req.name,
            "tenant_id": req.tenant_id,
            "role": req.role.value,
            "created_at": now,
        },
    )

    token = create_access_token(
        user_id=user_id,
        tenant_id=req.tenant_id,
        role=req.role.value,
    )

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            user_id=user_id,
            email=req.email,
            name=req.name,
            tenant_id=req.tenant_id,
            role=req.role,
            is_active=True,
            created_at=datetime.fromisoformat(now),
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: UserLogin):
    results = await run_query(
        "MATCH (u:User {email: $email}) RETURN u", {"email": req.email}
    )
    if not results:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_data = results[0]["u"]
    if not verify_password(req.password, user_data.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user_data.get("is_active", False):
        raise HTTPException(status_code=403, detail="Account deactivated")

    token = create_access_token(
        user_id=user_data["user_id"],
        tenant_id=user_data["tenant_id"],
        role=user_data["role"],
    )

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            user_id=user_data["user_id"],
            email=user_data["email"],
            name=user_data["name"],
            tenant_id=user_data["tenant_id"],
            role=TenantRole(user_data["role"]),
            is_active=user_data.get("is_active", True),
            created_at=(
                datetime.fromisoformat(user_data["created_at"])
                if user_data.get("created_at")
                else None
            ),
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    results = await run_query(
        "MATCH (u:User {user_id: $uid}) RETURN u",
        {"uid": current_user.user_id},
    )
    if not results:
        raise HTTPException(status_code=404, detail="User not found")
    u = results[0]["u"]
    return UserResponse(
        user_id=u["user_id"],
        email=u["email"],
        name=u["name"],
        tenant_id=u["tenant_id"],
        role=TenantRole(u["role"]),
        is_active=u.get("is_active", True),
        created_at=(
            datetime.fromisoformat(u["created_at"]) if u.get("created_at") else None
        ),
    )


# --- Tenant Management (admin only) ---


@router.post("/tenants", response_model=TenantResponse)
async def create_tenant(
    req: TenantCreate,
    current_user=Depends(require_role([TenantRole.admin])),
):
    existing = await run_query(
        "MATCH (t:Tenant {tenant_id: $tid}) RETURN t",
        {"tid": req.tenant_id},
    )
    if existing:
        raise HTTPException(status_code=409, detail="Tenant already exists")

    now = datetime.utcnow().isoformat()
    await run_query(
        """
        CREATE (t:Tenant {
            tenant_id: $tenant_id,
            name: $name,
            domain: $domain,
            plan: $plan,
            is_active: true,
            created_at: $created_at
        })
        RETURN t
        """,
        {
            "tenant_id": req.tenant_id,
            "name": req.name,
            "domain": req.domain,
            "plan": req.plan,
            "created_at": now,
        },
    )

    return TenantResponse(
        tenant_id=req.tenant_id,
        name=req.name,
        domain=req.domain,
        plan=req.plan,
        is_active=True,
        created_at=datetime.fromisoformat(now),
    )


@router.get("/tenants", response_model=List[TenantResponse])
async def list_tenants(
    current_user=Depends(require_role([TenantRole.admin])),
):
    results = await run_query("MATCH (t:Tenant) RETURN t ORDER BY t.created_at DESC")
    tenants = []
    for r in results:
        t = r["t"]
        user_count_result = await run_query(
            "MATCH (u:User {tenant_id: $tid}) RETURN count(u) as cnt",
            {"tid": t["tenant_id"]},
        )
        tenants.append(
            TenantResponse(
                tenant_id=t["tenant_id"],
                name=t["name"],
                domain=t.get("domain", ""),
                plan=t.get("plan", "enterprise"),
                is_active=t.get("is_active", True),
                created_at=(
                    datetime.fromisoformat(t["created_at"])
                    if t.get("created_at")
                    else None
                ),
                user_count=user_count_result[0]["cnt"] if user_count_result else 0,
            )
        )
    return tenants
