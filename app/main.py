from fastapi import FastAPI
import logging
from contextlib import asynccontextmanager

from app.api import chat
from app.core.config import settings
from app.logic.llm_wrapper import _get_client

logging.basicConfig(
    level   = settings.LOG_LVL,
    format  = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info(f"  v{settings.VERSION}")
    logger.info(f"  RAG Collection  : {settings.COLLECTION_NAME}")
    logger.info(f"  LLM             : {settings.LLM_MODEL_NAME}")
    logger.info("=" * 60)

    # ── AI Models Microservice (embedding + reranker) ────────────────────────
    logger.info("[Start Up] Establishing connection to LLM")
    await _get_client()

    yield

    # ── RAG Qdrant collection ─────────────────────────────────────────────────
    # try:
    #     from app.services.vector_store import vector_store_client
    #     vector_store_client._get_sync_client()
    #     logger.info("✓ RAG Qdrant collection ready")
    # except Exception as e:
    #     logger.warning(f"⚠ RAG Qdrant init failed: {e}")



app = FastAPI(
    title    = "A retrieval augmented generator made for my uni",
    version  = settings.VERSION,
    lifespan = lifespan,
    docs_url = "/docs",
)

app.include_router(chat.router)

@app.get("/health")
def  health():
    return {
        "status": "OK",
        "version": settings.VERSION,
        "llm_model": settings.LLM_MODEL_NAME
    }