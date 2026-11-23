import re

SPECIALISTS = ("research", "data", "developer", "document", "automation")


def parse_plan(text: str) -> list[str]:
    found: list[str] = []
    for token in re.findall(r"[a-z_]+", text.lower()):
        if token in SPECIALISTS and token not in found:
            found.append(token)
    return found or ["research", "document"]
