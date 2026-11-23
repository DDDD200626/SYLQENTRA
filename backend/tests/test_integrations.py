import json

import httpx

from app.integrations.github.github_connector import GitHubConnector
from app.integrations.mcp.client import MCPClient
from app.integrations.slack.slack_connector import SlackConnector


def test_mcp_client_rejects_a_tool_outside_the_allow_list():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/tools":
            return httpx.Response(200, json={"tools": [{"name": "list_issues"}]})
        return httpx.Response(200, json={"ok": True})

    client = MCPClient("https://mcp.example", transport=httpx.MockTransport(handler))
    assert client.list_tools() == [{"name": "list_issues"}]
    try:
        client.call_tool("delete_repo", {}, allowed={"list_issues"})
        raise AssertionError("disallowed tool should fail")
    except PermissionError:
        pass
    assert client.call_tool("list_issues", {"repo": "SYLQENTRA"}, allowed={"list_issues"}) == {"ok": True}
    client.close()


def test_github_and_slack_connectors_parse_provider_payloads():
    def github_handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer github-token"
        return httpx.Response(
            200,
            json=[
                {"number": 7, "title": "Fix report", "state": "open"},
                {"number": 8, "title": "Ignore me", "state": "open", "pull_request": {"url": "x"}},
            ],
        )

    github = GitHubConnector("github-token", transport=httpx.MockTransport(github_handler))
    assert github.list_issues("DDDD200626", "SYLQENTRA") == [{"number": 7, "title": "Fix report", "state": "open"}]
    github.close()

    def slack_handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["channel"] == "#reports"
        return httpx.Response(200, json={"ok": True, "channel": "C1", "ts": "1.2"})

    slack = SlackConnector("slack-token", transport=httpx.MockTransport(slack_handler))
    assert slack.post_message("#reports", "보고서가 준비되었습니다.")["ts"] == "1.2"
    slack.close()
