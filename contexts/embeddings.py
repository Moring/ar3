from __future__ import annotations

import hashlib
from typing import Iterable, List

from django.conf import settings


def chunk_text(text: str, chunk_size: int = 600) -> Iterable[str]:
    """
    Yield chunks of text roughly `chunk_size` characters long, splitting on sentence boundaries
    when available to preserve readability.
    """
    if not text:
        return []

    segments: List[str] = []
    buffer = []
    current_length = 0

    for sentence in text.split("."):
        sentence = sentence.strip()
        if not sentence:
            continue
        sentence += "."
        sentence_len = len(sentence)
        if current_length + sentence_len > chunk_size and buffer:
            segments.append(" ".join(buffer).strip())
            buffer = [sentence]
            current_length = sentence_len
        else:
            buffer.append(sentence)
            current_length += sentence_len

    if buffer:
        segments.append(" ".join(buffer).strip())
    return segments


def generate_embedding(text: str, dimensions: int = 1536):
    """
    Deterministic pseudo-embedding suitable for tests. Returns None when PGVECTOR is disabled.
    """
    if getattr(settings, "PGVECTOR_DISABLED", False):
        return None

    seed = hashlib.sha256(text.encode("utf-8")).digest()
    values: List[float] = []
    current = seed
    while len(values) < dimensions:
        current = hashlib.sha256(current).digest()
        values.extend(((byte / 255.0) - 0.5) for byte in current)
    return values[:dimensions]
