import logging
import hashlib
import time
from typing import List, Optional

import httpx

from app.core.config import settings
# from app.utils.cutome_exceptions import EmbeddingTimeout

logger = logging.getLogger(__name__)

_embed_cache: dict = {}
_CACHE_MAX         = 2048

_http_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            base_url = settings.EMBEDDING_SERVICE_URL,
            timeout  = httpx.Timeout(
                connect = 5.0,
                read    = settings.EMBED_TIMEOUT,
                write   = 10.0,
                pool    = 5.0,
            ),
            limits = httpx.Limits(
                max_connections      = 20,
                max_keepalive_connections = 10,
            ),
        )
    return _http_client

async def _call_embed(texts: List[str]) -> List[List[float]]:
    client  = _get_client()
    payload = {"texts": texts}

    for attempt in range(2):
        try:
            resp = await client.post("/embed", json=payload)
            resp.raise_for_status()
            data = resp.json()
            embeddings = data["embeddings"]
            if len(embeddings) != len(texts):
                raise ValueError(
                    f"Microservice returned {len(embeddings)} embeddings "
                    f"for {len(texts)} texts"
                )
            return embeddings
        # except httpx.ReadTimeout as e:
            # raise EmbeddingTimeout() from e
        except httpx.HTTPStatusError as e:
            logger.error(f"[Embedding] HTTP {e.response.status_code}: {e.response.text[:200]}")
            raise RuntimeError(f"Embedding microservice error: {e.response.status_code}")
        except Exception as e:
            if attempt == 0:
                logger.warning(f"[Embedding] Attempt 1 failed: {e} — retrying…")
                time.sleep(0.3)
                continue
            logger.error(f"[Embedding] Both attempts failed: {e}")
            raise RuntimeError(f"Embedding microservice unreachable: {e}")

    raise RuntimeError("Embedding microservice unreachable")

async def _embed_batched(texts: List[str]) -> List[List[float]]:
    batch_size = settings.EMBED_BATCH_SIZE
    if len(texts) <= batch_size:
        return await _call_embed(texts)

    results: List[List[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start: start + batch_size]
        logger.debug(f"[Embedding] Batch {start}–{start + len(batch)} of {len(texts)}")
        batch_results = await _call_embed(batch)
        results.extend(batch_results)
    return results

async def embed_text(texts: List[str]) -> List[List[float]]:
    results: List[Optional[List[float]]] = [None] * len(texts)
    miss_idx:   List[int] = []
    miss_texts: List[str] = []

    for i, text in enumerate(texts):
        key = hashlib.md5(text.encode()).hexdigest()
        if key in _embed_cache:
            results[i] = _embed_cache[key]
        else:
            miss_idx.append(i)
            miss_texts.append(text)

    if miss_texts:
        embeddings = await _embed_batched(miss_texts)
        for idx, emb, text in zip(miss_idx, embeddings, miss_texts):
            results[idx] = emb
            key = hashlib.md5(text.encode()).hexdigest()
            if len(_embed_cache) >= _CACHE_MAX:
                _embed_cache.pop(next(iter(_embed_cache)))
            _embed_cache[key] = emb

    return results

async def embed_query(query: str) -> List[float]:
    return (await embed_text([query]))[0]


async def embed_passages(passages: List[str]) -> List[List[float]]:
    return await embed_text(passages)

async def check_embedding_health() -> bool:
    try:
        client = _get_client()
        resp   = await client.get("/health", timeout=5.0)
        data   = resp.json()
        if data.get("status") == "healthy" and data.get("models_loaded"):
            logger.info(
                f"[Embedding] ✓ AI microservice healthy "
                f"(model: BAAI/bge-m3, dim: 1024)"
            )
            return True
        else:
            logger.warning(f"[Embedding] AI microservice not ready: {data}")
            return False
    except Exception as e:
        logger.warning(f"[Embedding] AI microservice health check failed: {e}")
        return False
