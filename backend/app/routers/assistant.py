from fastapi import APIRouter

from app.schemas import AssistantQueryRequest, AssistantQueryResponse
from app.services import rag_service

router = APIRouter(prefix="/api/assistant", tags=["ai-assistant"])


@router.post("/query", response_model=AssistantQueryResponse)
def query_assistant(payload: AssistantQueryRequest):
    return rag_service.query(payload.question, top_k=payload.top_k)


@router.get("/documents")
def list_documents():
    return {"documents": rag_service.get_index().list_documents()}
