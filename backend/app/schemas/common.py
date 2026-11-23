import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserRead(ORMModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    is_platform_admin: bool
    created_at: datetime


class OrganizationRead(ORMModel):
    id: uuid.UUID
    name: str
    slug: str
    plan: str = "free"
    is_active: bool


class OrganizationMembershipRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    role: str


class MeResponse(BaseModel):
    user: UserRead
    organizations: list[OrganizationMembershipRead]


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead
    organizations: list[OrganizationMembershipRead]


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    database: str
    redis: str


class DashboardTaskCounts(BaseModel):
    total: int
    pending: int = 0
    planning: int = 0
    running: int = 0
    reviewing: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0
    awaiting_approval: int = 0


class DashboardResponse(BaseModel):
    organization_id: uuid.UUID
    agent_count: int
    pending_approvals: int
    total_tokens: int
    estimated_cost: Decimal
    tasks: DashboardTaskCounts


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=20000)


class TaskRead(ORMModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_by: uuid.UUID | None
    title: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    items: list[TaskRead]
    total: int


class AgentRead(ORMModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    role: str
    description: str
    model_provider: str | None
    model_name: str | None
    is_active: bool


class MemberRead(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool


class MemberCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)
    password: str | None = None
    role: str


class MemberUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class OrganizationUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
