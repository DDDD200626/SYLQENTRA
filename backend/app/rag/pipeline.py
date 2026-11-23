import uuid

from sqlalchemy.orm import Session

from app.ai_models.model_manager import ModelManager
from app.database.base import utcnow
from app.models import Document, DocumentChunk
from app.rag.embeddings import embed_text
from app.rag.ingestion import chunk_text
from app.rag.retrieval import search_chunks
from app.services.tenant import TenantContext

SUPPORTED_EXTENSIONS = (".txt", ".md", ".csv")


class KnowledgeService:
    def __init__(self, db: Session, model_manager: ModelManager | None = None) -> None:
        self.db = db
        self.model_manager = model_manager

    def add_document(self, ctx: TenantContext, *, title: str, filename: str, content: str) -> Document:
        if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
            from app.core.exceptions import BadRequestError

            raise BadRequestError("Only txt, md, and csv documents can be ingested")
        document = Document(
            organization_id=ctx.organization_id,
            uploaded_by=ctx.user.id,
            title=title,
            filename=filename,
            content_type="text/plain",
            storage_path=f"db://{filename}",
            size_bytes=len(content.encode("utf-8")),
            status="ready",
        )
        self.db.add(document)
        self.db.flush()
        for index, chunk in enumerate(chunk_text(content)):
            self.db.add(
                DocumentChunk(
                    organization_id=ctx.organization_id,
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk,
                    embedding=embed_text(chunk),
                    created_at=utcnow(),
                )
            )
        self.db.commit()
        self.db.refresh(document)
        return document

    def ask(self, ctx: TenantContext, *, query: str, provider: str, model: str) -> dict:
        if self.model_manager is None:
            from app.core.exceptions import BadRequestError

            raise BadRequestError("Knowledge answers require a model manager")
        matches = search_chunks(self.db, ctx.organization_id, query)
        context = "\n\n".join(f"[{match.chunk_index}] {match.content}" for match in matches)
        response = self.model_manager.generate(
            provider=provider,
            model=model,
            prompt=f"Question: {query}\n\nCompany documents:\n{context}",
            system_prompt="Answer only from the company documents. Cite the chunk numbers you used.",
        )
        return {
            "answer": response.text,
            "sources": [{"document_id": str(match.document_id), "chunk_index": match.chunk_index} for match in matches],
        }


def documents_for_org(db: Session, organization_id: uuid.UUID) -> list[Document]:
    from sqlalchemy import select

    return list(db.scalars(select(Document).where(Document.organization_id == organization_id)).all())
