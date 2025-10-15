from pathlib import Path

import pytest
from pgvector.django import VectorField

from contexts.models import DocumentChunk


@pytest.mark.story("S-002")
def test_pgvector_extension_enabled():
    field = DocumentChunk._meta.get_field("embedding")
    assert isinstance(field, VectorField)
    init_sql = Path("docker/db/init/01-pgvector.sql").read_text().strip()
    assert "CREATE EXTENSION IF NOT EXISTS vector" in init_sql
