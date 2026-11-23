from app.database.base import Base

EXPECTED_TABLES = {
    "organizations",
    "users",
    "roles",
    "permissions",
    "role_permissions",
    "memberships",
    "refresh_tokens",
    "ai_providers",
    "ai_models",
    "model_usage",
    "usage_limits",
    "agents",
    "agent_configs",
    "agent_tools",
    "tasks",
    "task_steps",
    "agent_runs",
    "workflows",
    "workflow_nodes",
    "workflow_edges",
    "workflow_runs",
    "approvals",
    "integrations",
    "documents",
    "document_chunks",
    "audit_logs",
}


def test_phase3_tables_are_registered():
    assert EXPECTED_TABLES <= set(Base.metadata.tables)


def test_tenant_tables_have_organization_id():
    tenant_tables = {
        "memberships",
        "model_usage",
        "usage_limits",
        "agents",
        "agent_configs",
        "agent_tools",
        "tasks",
        "task_steps",
        "agent_runs",
        "workflows",
        "workflow_nodes",
        "workflow_edges",
        "workflow_runs",
        "approvals",
        "integrations",
        "documents",
        "document_chunks",
    }
    for name in tenant_tables:
        assert "organization_id" in Base.metadata.tables[name].c


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["redis"] == "disabled"
    assert body["service"] == "SYLQENTRA"
