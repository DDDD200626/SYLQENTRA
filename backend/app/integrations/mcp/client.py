import httpx


class MCPClient:
    def __init__(self, base_url: str, api_key: str = "", transport: httpx.BaseTransport | None = None) -> None:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = httpx.Client(base_url=base_url, headers=headers, transport=transport)

    def list_tools(self) -> list[dict]:
        response = self._client.get("/tools")
        response.raise_for_status()
        return list(response.json()["tools"])

    def call_tool(self, name: str, arguments: dict, allowed: set[str]) -> dict:
        if name not in allowed:
            raise PermissionError(f"Tool '{name}' is not allowed")
        response = self._client.post("/tools/call", json={"name": name, "arguments": arguments})
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()
