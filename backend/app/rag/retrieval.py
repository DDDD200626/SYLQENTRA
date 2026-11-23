import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DocumentChunk
from app.rag.embeddings import cosine_similarity, embed_text


def search_chunks(db: Session, organization_id: uuid.UUID, query: str, limit: int = 3) -> list[DocumentChunk]:
    query_vector = embed_text(query)
    rows = list(db.scalars(select(DocumentChunk).where(DocumentChunk.organization_id == organization_id)).all())
    ranked = sorted(
        rows,
        key=lambda row: cosine_similarity(query_vector, list(row.embedding or [])),
        reverse=True,
    )
    return [row for row in ranked if row.embedding][:limit]
