def chunk_text(text: str, size: int = 500) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    return [cleaned[index : index + size] for index in range(0, len(cleaned), size)]
