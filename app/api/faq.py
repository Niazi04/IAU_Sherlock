import logging
import re
from typing import List, Optional, Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.schemas.general import Message
from app.core.config import settings
from app.logic.faq_store import faq_store

import logging
import re
from typing import List, Optional, Any, Dict, AsyncGenerator
from fastapi import APIRouter, HTTPException, Query, Body, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field



logger = logging.getLogger(__name__)
router = APIRouter(prefix="/faq", tags=["FAQ Q&A Strategy"])



class FAQItem(BaseModel):
    id: Optional[Any] = None
    question: str
    answer: str

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



@router.post(
    "/mine/file",
    summary="Extract FAQ Q&A pairs from an uploaded file",
)
async def mine_faqs_from_file(
    file: UploadFile = File(...),
    source: str = Form(default="mined"),
    collection: Optional[str] = Form(default=None)
):
    import io as _io
    import chardet
    from app.utils.text_preprocessor import strip_bidi
    import json

    col = collection or settings.FAQ_COLLECTION_NAME
    content_bytes = await file.read()
    filename = (file.filename or "").lower()

    detected = chardet.detect(content_bytes)
    encoding = detected.get("encoding", "utf-8") if detected else "utf-8"
    
    try:
        content = content_bytes.decode(encoding)
    except UnicodeDecodeError:
        content = content_bytes.decode("utf-8", errors="replace")
    
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON file: {str(e)}"
        )
    
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400,
            detail="Expected JSON object with FAQ entries"
        )
    
    faq_items = []
    for key, value in data.items():
        if not isinstance(value, dict):
            continue
            
        questions = value.get("questions", [])
        answer = value.get("answer", "")
        
        if not questions or not answer or not answer.strip():
            continue
            
        answer_norm = strip_bidi(answer.strip())
        
        for question in questions:
            if question and question.strip():
                question_norm = strip_bidi(question.strip())
                faq_items.append({
                    "id": f"{key}_{len(faq_items)}",
                    "question": question_norm,
                    "answer": answer_norm,
                    "faq_key": key,
                })
    
    if not faq_items:
        raise HTTPException(
            status_code=400,
            detail="No valid FAQ entries found in the file. Expected format: {'1': {'questions': ['Q1', 'Q2'], 'answer': 'A'}}"
        )
    
    try:
        total_upserted = await faq_store.upsert_faq_batch(
            items=faq_items,
            source=source,
            collection=col
        )
    except Exception as e:
        logger.error(f"Failed to upsert FAQ items: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store FAQ items: {str(e)}"
        )
    
    return {
        "status": "success",
        "message": f"Successfully processed {len(faq_items)} FAQ items from {len(data)} entries",
        "total_items": len(faq_items),
        "total_entries": len(data),
        "upserted": total_upserted,
        "collection": col,
        "source": source
    }

