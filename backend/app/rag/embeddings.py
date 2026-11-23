import hashlib
import math
import re

DIMENSIONS = 32


def embed_text(text: str) -> list[float]:
    vector = [0.0] * DIMENSIONS
    for token in re.findall(r"\w+", text.lower()):
        vector[hashlib.sha256(token.encode("utf-8")).digest()[0] % DIMENSIONS] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=False))
