class PermissionCode:
    DASHBOARD_READ = "dashboard:read"
    TASKS_READ = "tasks:read"
    TASKS_WRITE = "tasks:write"
    AGENTS_READ = "agents:read"
    AGENTS_WRITE = "agents:write"
    USERS_READ = "users:read"
    USERS_MANAGE = "users:manage"
    ORGANIZATIONS_MANAGE = "organizations:manage"
    APPROVALS_READ = "approvals:read"
    APPROVALS_MANAGE = "approvals:manage"


ALL_PERMISSIONS: list[tuple[str, str]] = [
    (PermissionCode.DASHBOARD_READ, "대시보드 조회"),
    (PermissionCode.TASKS_READ, "업무 조회"),
    (PermissionCode.TASKS_WRITE, "업무 생성"),
    (PermissionCode.AGENTS_READ, "Agent 조회"),
    (PermissionCode.AGENTS_WRITE, "Agent 관리"),
    (PermissionCode.USERS_READ, "구성원 조회"),
    (PermissionCode.USERS_MANAGE, "구성원 관리"),
    (PermissionCode.ORGANIZATIONS_MANAGE, "조직 설정 변경"),
    (PermissionCode.APPROVALS_READ, "승인 조회"),
    (PermissionCode.APPROVALS_MANAGE, "승인 처리"),
]

VIEWER = [
    PermissionCode.DASHBOARD_READ,
    PermissionCode.TASKS_READ,
    PermissionCode.AGENTS_READ,
    PermissionCode.APPROVALS_READ,
]
EMPLOYEE = VIEWER + [PermissionCode.TASKS_WRITE]
MANAGER = EMPLOYEE + [PermissionCode.AGENTS_WRITE, PermissionCode.USERS_READ]
ORGANIZATION_ADMIN = MANAGER + [
    PermissionCode.USERS_MANAGE,
    PermissionCode.ORGANIZATIONS_MANAGE,
    PermissionCode.APPROVALS_MANAGE,
]
SUPER_ADMIN = [code for code, _description in ALL_PERMISSIONS]

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "viewer": VIEWER,
    "employee": EMPLOYEE,
    "manager": MANAGER,
    "organization_admin": ORGANIZATION_ADMIN,
    "super_admin": SUPER_ADMIN,
}

ROLE_DESCRIPTIONS = {
    "super_admin": "전체 시스템 관리",
    "organization_admin": "기업 내부 관리",
    "manager": "업무 및 Agent 관리",
    "employee": "업무 요청 및 조회",
    "viewer": "읽기 전용",
}

ASSIGNABLE_ROLES = ("organization_admin", "manager", "employee", "viewer")
