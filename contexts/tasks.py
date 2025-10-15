from __future__ import annotations

from typing import Iterable

from django.db import transaction
from huey.contrib.djhuey import task

from uploads.models import File
from .embeddings import chunk_text, generate_embedding
from .models import DocumentChunk


def _chunk_and_embed(file_id: int, *, chunk_size: int = 600):
    file = File.objects.get(pk=file_id)
    file.file.open("r")
    try:
        content = file.file.read()
    finally:
        file.file.close()
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="ignore")

    if not content:
        return []

    DocumentChunk.objects.filter(file=file).delete()

    created_ids = []
    for segment in chunk_text(content, chunk_size=chunk_size):
        embedding = generate_embedding(segment)
        chunk = DocumentChunk.objects.create(file=file, text=segment, embedding=embedding)
        created_ids.append(chunk.id)
    return created_ids


@task()
def chunk_and_embed_file_task(file_id: int, *, chunk_size: int = 600):
    return _chunk_and_embed(file_id, chunk_size=chunk_size)


def chunk_and_embed_file(file_id: int, *, chunk_size: int = 600):
    return _chunk_and_embed(file_id, chunk_size=chunk_size)
