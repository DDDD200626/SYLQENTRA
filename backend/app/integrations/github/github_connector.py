import httpx


class GitHubConnector:
    def __init__(self, token: str, transport: httpx.BaseTransport | None = None) -> None:
        self._client = httpx.Client(
            base_url="https://api.github.com",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            transport=transport,
        )

    def list_issues(self, owner: str, repo: str) -> list[dict]:
        response = self._client.get(f"/repos/{owner}/{repo}/issues")
        response.raise_for_status()
        return [
            {"number": item["number"], "title": item["title"], "state": item["state"]}
            for item in response.json()
            if "pull_request" not in item
        ]

    def close(self) -> None:
        self._client.close()
