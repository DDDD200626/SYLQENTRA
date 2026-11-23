from tests.conftest import PLATFORM_EMAIL, PLATFORM_PASSWORD, auth_header, register


def test_tasks_dashboard_agents_and_tenant_isolation(client):
    owner = register(client, "owner@example.com", "Acme")
    other = register(client, "other@example.com", "Beta")
    owner_headers = auth_header(owner["access_token"])
    other_headers = auth_header(other["access_token"])

    agents = client.get("/api/v1/agents", headers=owner_headers)
    assert agents.status_code == 200
    roles = [item["role"] for item in agents.json()]
    assert roles == ["manager", "research", "data", "developer", "document", "review", "automation"]
    assert all(item["organization_id"] == owner["organizations"][0]["id"] for item in agents.json())

    created = client.post(
        "/api/v1/tasks",
        headers=owner_headers,
        json={"title": "월간 매출 보고서", "description": "CSV를 분석한다."},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]
    assert created.json()["status"] == "pending"

    listed = client.get("/api/v1/tasks", headers=owner_headers)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    hidden = client.get(f"/api/v1/tasks/{task_id}", headers=other_headers)
    assert hidden.status_code == 404
    other_list = client.get("/api/v1/tasks", headers=other_headers)
    assert other_list.json()["total"] == 0

    dashboard = client.get("/api/v1/dashboard", headers=owner_headers)
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["agent_count"] == 7
    assert body["tasks"]["pending"] == 1
    assert body["tasks"]["total"] == 1
    assert body["total_tokens"] == 0

    other_agents = client.get("/api/v1/agents", headers=other_headers)
    assert len(other_agents.json()) == 7
    assert other_agents.json()[0]["id"] != agents.json()[0]["id"]


def test_role_permissions_membership_and_org_admin_guard(client):
    owner = register(client, "owner@example.com", "Acme")
    headers = auth_header(owner["access_token"])

    invited = client.post(
        "/api/v1/organizations/members",
        headers=headers,
        json={
            "email": "viewer@example.com",
            "full_name": "Viewer",
            "password": "Viewer1234",
            "role": "viewer",
        },
    )
    assert invited.status_code == 201

    viewer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "viewer@example.com", "password": "Viewer1234"},
    )
    assert viewer_login.status_code == 200
    viewer_headers = auth_header(viewer_login.json()["access_token"])
    denied = client.post("/api/v1/tasks", headers=viewer_headers, json={"title": "금지된 업무"})
    assert denied.status_code == 403
    allowed_read = client.get("/api/v1/tasks", headers=viewer_headers)
    assert allowed_read.status_code == 200
    cannot_invite = client.post(
        "/api/v1/organizations/members",
        headers=viewer_headers,
        json={"email": "extra@example.com", "full_name": "Extra", "password": "Extra1234", "role": "employee"},
    )
    assert cannot_invite.status_code == 403

    promoted = client.patch(
        f"/api/v1/organizations/members/{viewer_login.json()['user']['id']}",
        headers=headers,
        json={"role": "manager"},
    )
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "manager"

    remove_last_admin = client.patch(
        f"/api/v1/organizations/members/{owner['user']['id']}",
        headers=headers,
        json={"role": "employee"},
    )
    assert remove_last_admin.status_code == 400

    current = client.get("/api/v1/organizations/current", headers=headers)
    assert current.status_code == 200
    renamed = client.patch("/api/v1/organizations/current", headers=headers, json={"name": "Acme Korea"})
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Acme Korea"
    assert renamed.json()["slug"] == current.json()["slug"]


def test_platform_admin_can_open_another_organization_without_mixing_data(client):
    owner = register(client, "owner@example.com", "Acme")
    owner_headers = auth_header(owner["access_token"])
    created_task = client.post("/api/v1/tasks", headers=owner_headers, json={"title": "Acme only"})
    assert created_task.status_code == 201

    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": PLATFORM_EMAIL, "password": PLATFORM_PASSWORD},
    )
    admin_headers = auth_header(admin_login.json()["access_token"])
    created_org = client.post("/api/v1/organizations", headers=admin_headers, json={"name": "Gamma"})
    assert created_org.status_code == 201
    denied = client.post("/api/v1/organizations", headers=owner_headers, json={"name": "Should Fail"})
    assert denied.status_code == 403

    gamma_headers = {**admin_headers, "X-Organization-Id": created_org.json()["id"]}
    agents = client.get("/api/v1/agents", headers=gamma_headers)
    assert agents.status_code == 200
    assert len(agents.json()) == 7
    tasks = client.get("/api/v1/tasks", headers=gamma_headers)
    assert tasks.json()["total"] == 0

    missing_header = client.get("/api/v1/dashboard", headers=admin_headers)
    assert missing_header.status_code == 400
