from tests.conftest import auth_header, register


def test_new_organization_starts_on_the_free_plan_and_can_upgrade(client):
    owner = register(client, "plan@example.com", "Plan Co")
    headers = auth_header(owner["access_token"])
    plans = client.get("/api/v1/plans")
    assert plans.status_code == 200
    assert {item["name"] for item in plans.json()} >= {"free", "starter", "team", "business", "enterprise"}

    current = client.get("/api/v1/organizations/current", headers=headers)
    assert current.json()["plan"] == "free"
    usage = client.get("/api/v1/ai/usage", headers=headers)
    assert usage.json()["monthly_token_limit"] == 100000

    upgraded = client.put("/api/v1/organizations/current/plan", headers=headers, json={"plan": "team"})
    assert upgraded.status_code == 200, upgraded.text
    assert upgraded.json()["plan"] == "team"
    assert client.get("/api/v1/ai/usage", headers=headers).json()["monthly_token_limit"] == 2_000_000
