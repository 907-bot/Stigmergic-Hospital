from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
import enum


class TenantRole(str, enum.Enum):
    admin = "admin"
    clinician = "clinician"
    nurse = "nurse"
    doctor = "doctor"
    lab = "lab"
    pharmacy = "pharmacy"
    icu = "icu"
    ambulance = "ambulance"
    viewer = "viewer"


class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    tenant_id: str
    role: TenantRole = TenantRole.clinician


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    tenant_id: str
    role: TenantRole
    is_active: bool
    created_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: str | None = None
    tenant_id: str | None = None
    role: TenantRole | None = None
    scopes: List[str] = []


class TenantCreate(BaseModel):
    tenant_id: str
    name: str
    domain: str = ""
    plan: Literal["community", "enterprise", "white-label"] = "enterprise"


class TenantResponse(BaseModel):
    tenant_id: str
    name: str
    domain: str
    plan: str
    is_active: bool
    created_at: Optional[datetime] = None
    user_count: int = 0
