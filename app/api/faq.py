import logging
import re
from typing import List, Optional, Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.schemas.general import Message
from app.core.config import settings
from app.logic.faq_store import faq_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/faq", tags=["FAQ Q&A Strategy"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class FAQItem(BaseModel):
    id: Optional[Any] = None
    question: str
    answer: str
    category: Optional[str] = Field(
        default=None,
        description="conversation_subject — fine-grained topic (e.g. 'سیکل پایا')",
    )
    subject_category: Optional[str] = Field(
        default=None,
        description=(
            "Parent taxonomy category (e.g. 'برداشت و واریز'). "
            "Auto-resolved from category if not provided."
        ),
    )

    class Config:
        extra = "allow"


class FAQBatchRequest(BaseModel):
    items: List[FAQItem]
    source: str = Field(default="faq")
    collection: Optional[str] = None


class FAQIngestResponse(BaseModel):
    status: str
    ingested: int
    collection: str
    message: str


class FAQSearchRequest(BaseModel):
    query: str
    limit: int = Field(default=3, ge=1, le=20)
    score_threshold: Optional[float] = None
    category: Optional[str] = Field(default=None, description="Filter by conversation_subject")
    subject_category: Optional[str] = Field(default=None, description="Filter by parent category")
    collection: Optional[str] = None


@router.post("/search", summary="Find matching FAQ questions")
async def faq_search(request: FAQSearchRequest):
    col = request.collection or settings.FAQ_COLLECTION_NAME
    matches = await faq_store.search(
        query=request.query,
        limit=request.limit,
        score_threshold=request.score_threshold,
        collection=col,
    )
    return {
        "query": request.query,
        "collection": col,
        "score_type": "cross-encoder (0–1)",
        "threshold": request.score_threshold,
        "total": len(matches),
        "results": [m.to_dict() for m in matches],
    }