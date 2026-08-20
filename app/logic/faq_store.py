"""
faq_store.py
============

FAQ Question-Answer Embedding Strategy with Cross-Encoder Reranking
====================================================================

Storage:  bi-encoder (multilingual-e5) for fast ANN candidate retrieval
Scoring:  cross-encoder (mmarco-mMiniLMv2) for calibrated relevance scoring

Two-stage pipeline per query (BGE-M3 — no query/passage prefixes):
  Stage 1 → bi-encoder search   : fetch top-K candidates fast from Qdrant
  Stage 2 → cross-encoder rerank: score each (query, candidate_question) pair
                                  and use that score for tier decision

Payload schema per Qdrant point:
  {
    "faq_id":     int | str,
    "question":   str,
    "answer":     str,
    "category":   str | None,
    "source":     str,
    "created_at": str   (ISO UTC)
  }
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple

from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import settings
from app.logic.embedding import embed_query, embed_text
from app.utils.text_preprocessor import normalise_farsi_chars
import re  # Add this to existing imports

logger = logging.getLogger(__name__)







# Add this function to faq_store.py after the imports and before the FAQMatch class

def split_questions(text: str, delimiter: str = "\n") -> List[str]:
    """
    Split a text containing multiple questions into individual questions.
    
    Args:
        text: The raw text containing questions (one per line or delimiter-separated)
        delimiter: The delimiter to split on (default: newline)
    
    Returns:
        List of cleaned, non-empty question strings
    """
    if not text or not text.strip():
        return []
    
    # Split by delimiter
    raw_questions = text.split(delimiter)
    
    # Clean each question
    questions = []
    for q in raw_questions:
        cleaned = q.strip()
        # Remove common numbering/bullet prefixes
        if cleaned:
            # Remove patterns like "1.", "2.", "-", "*", etc.
            cleaned = re.sub(r'^\d+[\.\)]\s*', '', cleaned)
            cleaned = re.sub(r'^[\-\*\•]\s*', '', cleaned)
            questions.append(cleaned)
    
    # Filter out empty strings and very short ones (less than 3 chars)
    questions = [q for q in questions if len(q) >= 3]
    
    return questions


# ─── FAQ result type ──────────────────────────────────────────────────────────

class FAQMatch:
    """A matched FAQ entry with cross-encoder relevance score."""

    def __init__(
        self,
        faq_id: Any,
        question: str,
        answer: str,
        score: float = 0.0,         # cross-encoder score (0–1), NOT bi-encoder
        bi_score: float = 0.0,      # original bi-encoder score (for debug)
        category: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.faq_id = faq_id
        self.question = question
        self.answer = answer
        self.score = score
        self.bi_score = bi_score
        self.category = category
        self.metadata = metadata or {}

    def is_confident(self, threshold: float) -> bool:
        return self.score >= threshold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "faq_id":   self.faq_id,
            "question": self.question,
            "answer":   self.answer,
            "score":    round(self.score, 4),
            "bi_score": round(self.bi_score, 4),
            "category": self.category,
        }



class FAQStore:
    """
    Qdrant-backed FAQ store with two-stage retrieval:
    1. Bi-encoder ANN (fast, approximate)
    2. Cross-encoder reranking (slow but calibrated)
    """

    def __init__(self):
        self._async_client: Optional[AsyncQdrantClient] = None
        self._sync_client: Optional[QdrantClient] = None
        self.collection_name = settings.FAQ_COLLECTION_NAME


    def _get_sync_client(self) -> QdrantClient:
        if self._sync_client is None:
            self._sync_client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY or None,
                timeout=60,
            )
            self._ensure_collection(self._sync_client, self.collection_name)
        return self._sync_client

    async def _get_async_client(self) -> AsyncQdrantClient:
        if self._async_client is None:
            self._async_client = AsyncQdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY or None,
                timeout=60,
            )
        return self._async_client

    def _ensure_collection(self, client: QdrantClient, name: str):
        existing = [c.name for c in client.get_collections().collections]
        if name not in existing:
            logger.info(f"[FAQ] Creating collection '{name}' ({settings.EMBEDDING_DIM} dims)")
            client.create_collection(
                collection_name=name,
                vectors_config=qmodels.VectorParams(
                    size=settings.EMBEDDING_DIM,
                    distance=qmodels.Distance.COSINE,
                ),
                hnsw_config=qmodels.HnswConfigDiff(m=16, ef_construct=100),
            )
            for field, schema in [
                ("category", qmodels.PayloadSchemaType.KEYWORD),
                ("source",   qmodels.PayloadSchemaType.KEYWORD),
            ]:
                try:
                    client.create_payload_index(
                        collection_name=name, field_name=field, field_schema=schema,
                    )
                except Exception:
                    pass
            logger.info(f"[FAQ] Collection '{name}' created.")

    async def _ensure_async(self, collection: Optional[str] = None):
        name = collection or self.collection_name
        sync = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
            timeout=30,
        )
        self._ensure_collection(sync, name)


    async def upsert_faq(
        self,
        faq_id: Any,
        question: str,
        answer: str,
        category: Optional[str] = None,
        source: str = "faq",
        extra_metadata: Optional[Dict[str, Any]] = None,
        collection: Optional[str] = None,
    ) -> str:
        col = collection or self.collection_name
        await self._ensure_async(col)
        client = await self._get_async_client()

        q_norm = normalise_farsi_chars(question.strip())
        a_norm = normalise_farsi_chars(answer.strip())

        # BGE-M3: no prefix needed
        vector = await embed_query(q_norm)

        point_id = str(uuid.uuid4())
        payload: Dict[str, Any] = {
            "faq_id":     faq_id,
            "question":   q_norm,
            "answer":     a_norm,
            "source":     source,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if category:
            payload["category"] = category
        if extra_metadata:
            payload.update(extra_metadata)

        await client.upsert(
            collection_name=col,
            points=[qmodels.PointStruct(id=point_id, vector=vector, payload=payload)],
        )
        return point_id


    async def upsert_faq_batch(
        self,
        items: List[Dict[str, Any]],
        source: str = "faq",
        collection: Optional[str] = None,
    ) -> int:
        if not items:
            return 0

        col = collection or self.collection_name
        client = await self._get_async_client()
        await self._ensure_async(col)

        BATCH = 64
        total = 0

        for start in range(0, len(items), BATCH):
            batch = items[start: start + BATCH]

            questions = [normalise_farsi_chars(it["question"].strip()) for it in batch]
            answers   = [normalise_farsi_chars(it["answer"].strip())   for it in batch]

            vectors   = await embed_text(questions)

            points = []
            for it, q_norm, a_norm, vec in zip(batch, questions, answers, vectors):
                faq_id = it.get("id", str(uuid.uuid4()))
                payload: Dict[str, Any] = {
                    "faq_id":     faq_id,
                    "question":   q_norm,
                    "answer":     a_norm,
                    "source":     source,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                if "category" in it and it["category"] is not None:
                    payload["category"] = it["category"]
                for k, v in it.items():
                    if k not in ("id", "question", "answer", "embedding_text", "category"):
                        payload[k] = v

                points.append(
                    qmodels.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vec,
                        payload=payload,
                    )
                )

            await client.upsert(collection_name=col, points=points)
            total += len(points)
            logger.info(f"[FAQ] Batch upserted [{start}–{start+len(batch)}]: {total} total")

        return total


    async def search(
        self,
        query: str,
        limit: int = 3,
        score_threshold: Optional[float] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        collection: Optional[str] = None,
    ) -> List[FAQMatch]:
        """
        FAQ search using bi-encoder ANN only (no reranking).
        
        Returns top `limit` results with their bi-encoder scores.
        The `score_threshold` applies to the bi-encoder cosine score.
        """
        col = collection or self.collection_name
        await self._ensure_async(col)
        client = await self._get_async_client()

        q_norm = normalise_farsi_chars(query.strip())
        query_vector = await embed_query(q_norm)

        info = await client.get_collection(col)
        if (info.points_count or 0) == 0:
            return []

        # Remove reranking, just fetch exactly what we need
        # (or slightly more if you want, but since no reranking, just use limit)
        fetch_k = limit  # Or keep some buffer if you want: max(limit * 2, limit)

        qdrant_filter = None
        if filter_dict:
            qdrant_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(key=k, match=qmodels.MatchValue(value=v))
                    for k, v in filter_dict.items()
                    if v is not None and v != ""
                ]
            )

        result = await client.query_points(
            collection_name=col,
            query=query_vector,
            limit=fetch_k,
            query_filter=qdrant_filter,
            with_payload=True,
            score_threshold=score_threshold,  # This now applies to bi-encoder scores
        )

        if not result.points:
            return []

        # Extract payload and build FAQMatch objects
        matches: List[FAQMatch] = []
        for hit in result.points:
            if not hit.payload:
                continue
            p = hit.payload
            
            matches.append(FAQMatch(
                faq_id=p.get("faq_id"),
                question=p.get("question", ""),
                answer=p.get("answer", ""),
                score=hit.score,  # Use bi-encoder score as the main score
                bi_score=hit.score,  # Store bi-encoder score separately if needed
                category=p.get("category"),
                metadata={k: v for k, v in p.items()
                        if k not in ("faq_id", "question", "answer", "category")},
            ))

        return matches


    async def delete_by_faq_id(self, faq_id: Any, collection: Optional[str] = None) -> bool:
        col    = collection or self.collection_name
        await self._ensure_async(col)
        client = await self._get_async_client()
        result = await client.delete(
            collection_name=col,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(must=[
                    qmodels.FieldCondition(key="faq_id", match=qmodels.MatchValue(value=faq_id))
                ])
            ),
        )
        return result.status == qmodels.UpdateStatus.COMPLETED

    async def delete_by_filter(self, filter_dict: Dict[str, Any], collection: Optional[str] = None) -> bool:
        col    = collection or self.collection_name
        await self._ensure_async(col)
        client = await self._get_async_client()
        must = [
            qmodels.FieldCondition(key=k, match=qmodels.MatchValue(value=v))
            for k, v in filter_dict.items()
        ]
        result = await client.delete(
            collection_name=col,
            points_selector=qmodels.FilterSelector(filter=qmodels.Filter(must=must)),
        )
        return result.status == qmodels.UpdateStatus.COMPLETED


    async def collection_info(self, collection: Optional[str] = None) -> Dict[str, Any]:
        col    = collection or self.collection_name
        await self._ensure_async(col)
        client = await self._get_async_client()
        info   = await client.get_collection(col)
        return {
            "name":          col,
            "points_count":  info.points_count,
            "vectors_count": info.vectors_count,
            "status":        str(info.status),
        }

    async def scroll(self, limit: int = 50, collection: Optional[str] = None) -> List[Dict[str, Any]]:
        col    = collection or self.collection_name
        await self._ensure_async(col)
        client = await self._get_async_client()
        info = await client.get_collection(col)
        if (info.points_count or 0) == 0:
            return []
        result, _ = await client.scroll(collection_name=col, limit=limit, with_payload=True)
        return [p.payload for p in result if p.payload]


# ─── Singleton ────────────────────────────────────────────────────────────────
faq_store = FAQStore()