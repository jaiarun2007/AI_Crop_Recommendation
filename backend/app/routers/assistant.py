from fastapi import APIRouter

from app.schemas import AssistantQueryRequest, AssistantQueryResponse
from app.services import rag_service

router = APIRouter(prefix="/api/assistant", tags=["ai-assistant"])


@router.post(
    "/query",
    response_model=AssistantQueryResponse,
    summary="RAG Q&A over the project's own documents (TF-IDF retrieval + optional LLM synthesis)",
)
def query_assistant(payload: AssistantQueryRequest):
    return rag_service.query(payload.question, top_k=payload.top_k)


@router.get("/documents", summary="List indexed source documents")
def list_documents():
    return {"documents": rag_service.get_index().list_documents()}
