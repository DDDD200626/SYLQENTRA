import httpx


class SlackConnector:
    def __init__(self, token: str, transport: httpx.BaseTransport | None = None) -> None:
        self._client = httpx.Client(
            base_url="https://slack.com/api",
            headers={"Authorization": f"Bearer {token}"},
            transport=transport,
        )

    def post_message(self, channel: str, text: str) -> dict:
        response = self._client.post("/chat.postMessage", json={"channel": channel, "text": text})
        response.raise_for_status()
        body = response.json()
        if not body.get("ok"):
            raise RuntimeError(body.get("error", "Slack request failed"))
        return {"channel": body.get("channel", channel), "ts": body.get("ts", "")}

    def close(self) -> None:
        self._client.close()
