from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai_models.model_manager import ModelManager, get_model_manager
from app.api.deps import require_permissions
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.rag.pipeline import KnowledgeService, documents_for_org
from app.services.tenant import TenantContext

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    filename: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=1)


class Question(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    provider: str
    model: str


@router.get("/documents")
def list_documents(
    ctx: TenantContext = Depends(require_permissions(PermissionCode.TASKS_READ)),
    db: Session = Depends(get_db),
) -> list[dict]:
    return [{"id": str(item.id), "title": item.title, "filename": item.filename} for item in documents_for_org(db, ctx.organization_id)]


@router.post("/documents", status_code=201)
def create_document(
    payload: DocumentCreate,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.TASKS_WRITE)),
    db: Session = Depends(get_db),
) -> dict:
    document = KnowledgeService(db).add_document(ctx, title=payload.title, filename=payload.filename, content=payload.content)
    return {"id": str(document.id), "title": document.title}


@router.post("/ask")
def ask(
    payload: Question,
    ctx: TenantContext = Depends(require_permissions(PermissionCode.TASKS_WRITE)),
    db: Session = Depends(get_db),
    model_manager: ModelManager = Depends(get_model_manager),
) -> dict:
    return KnowledgeService(db, model_manager).ask(ctx, query=payload.query, provider=payload.provider, model=payload.model)
