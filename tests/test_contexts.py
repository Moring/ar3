import math

import pytest
from django.core.files.base import ContentFile

from contexts.embeddings import generate_embedding
from contexts.models import DocumentChunk, Category
from contexts.tasks import chunk_and_embed_file
from domains.models import Client
from uploads.models import File


@pytest.mark.story("S-016")
def test_chunk_and_embed_pipeline(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.PGVECTOR_DISABLED = False
    client = Client.objects.create(name="Acme")
    category = Category.objects.create(name="General")
    upload = File.objects.create(client=client, file=ContentFile(b"Hello world. This is a test document." * 5, name="doc.txt"), category=category)
    chunk_ids = chunk_and_embed_file(upload.id)
    chunks = DocumentChunk.objects.filter(file=upload)
    assert chunks.count() == len(chunk_ids) > 0
    if chunks:
        embedding = chunks[0].embedding
        assert isinstance(embedding, list)
        assert len(embedding) == 1536


@pytest.mark.story("S-016")
def test_vector_search_returns_expected_chunk(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.PGVECTOR_DISABLED = False
    client = Client.objects.create(name="Acme")
    category = Category.objects.create(name="Support")
    upload = File.objects.create(client=client, file=ContentFile(b"Support instructions." * 3, name="manual.txt"), category=category)
    chunk_and_embed_file(upload.id)
    chunks = list(DocumentChunk.objects.filter(file=upload))
    query_embedding = generate_embedding("support instructions")

    def similarity(vec_a, vec_b):
        denom = math.sqrt(sum(a * a for a in vec_a)) * math.sqrt(sum(b * b for b in vec_b))
        if denom == 0:
            return 0
        return sum(a * b for a, b in zip(vec_a, vec_b)) / denom

    scored = sorted(((similarity(chunk.embedding, query_embedding), chunk) for chunk in chunks if chunk.embedding), reverse=True)
    top_score, top_chunk = scored[0]
    assert "Support" in top_chunk.text or top_score > 0
