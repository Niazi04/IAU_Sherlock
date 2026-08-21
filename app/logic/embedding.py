import asyncio
import hashlib
import logging
from typing import Dict, List, Optional, Tuple

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "nvidia/nemotron-3-embed-1b"
EMBEDDING_DIMENSION = 2048


_embed_cache: Dict[Tuple[str, str], List[float]] = {}
_CACHE_MAX = 2048

_http_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _http_client

    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            base_url=settings.EMBEDDING_SERVICE_URL.rstrip("/"),
            headers={
                "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(
                connect=5.0,
                read=settings.EMBED_TIMEOUT,
                write=10.0,
                pool=5.0,
            ),
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10,
            ),
        )

    return _http_client


async def close_embedding_client() -> None:
    global _http_client

    if _http_client is not None and not _http_client.is_closed:
        await _http_client.aclose()

    _http_client = None

def _cache_key(text: str, input_type: str) -> Tuple[str, str]:
    """
    Cache embeddings by both text and input_type.

    This is important because NVIDIA's model supports different embedding
    contexts for queries and passages.
    """
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()
    return input_type, digest


def _cache_get(
    text: str,
    input_type: str,
) -> Optional[List[float]]:
    return _embed_cache.get(_cache_key(text, input_type))


def _cache_set(
    text: str,
    input_type: str,
    embedding: List[float],
) -> None:
    key = _cache_key(text, input_type)

    if len(_embed_cache) >= _CACHE_MAX:
        _embed_cache.pop(next(iter(_embed_cache)))

    _embed_cache[key] = embedding

async def _call_embed(
    texts: List[str],
    input_type: str,
) -> List[List[float]]:
    """
    Call NVIDIA's OpenAI-compatible embeddings endpoint.

    NVIDIA request:

        POST /v1/embeddings

        {
            "model": "nvidia/nemotron-3-embed-1b",
            "input": [...],
            "input_type": "query" | "passage",
            "encoding_format": "float",
            "embedding_type": "float"
        }

    NVIDIA response:

        {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "index": 0,
                    "embedding": [...]
                }
            ],
            "model": "...",
            "usage": {...}
        }
    """
    if not texts:
        return []

    if input_type not in {"query", "passage"}:
        raise ValueError(
            f"Invalid embedding input_type: {input_type!r}. "
            "Expected 'query' or 'passage'."
        )

    client = _get_client()

    payload = {
        "model": EMBEDDING_MODEL,
        "input": texts,
        "input_type": input_type,
        "encoding_format": "float",
        "embedding_type": "float",
    }

    last_error: Optional[Exception] = None

    for attempt in range(2):
        try:
            response = await client.post(
                "/v1/embeddings",
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            if data.get("object") != "list":
                raise ValueError(
                    f"Unexpected NVIDIA embedding response object: "
                    f"{data.get('object')!r}"
                )

            raw_embeddings = data.get("data")

            if not isinstance(raw_embeddings, list):
                raise ValueError(
                    "NVIDIA embedding response is missing a valid "
                    "'data' list"
                )

            if len(raw_embeddings) != len(texts):
                raise ValueError(
                    f"NVIDIA returned {len(raw_embeddings)} embeddings "
                    f"for {len(texts)} texts"
                )

            try:
                raw_embeddings = sorted(
                    raw_embeddings,
                    key=lambda item: item["index"],
                )
            except (KeyError, TypeError):
                # Some compatible servers may omit index. In that case,
                # preserve the response order.
                pass

            embeddings: List[List[float]] = []

            for i, item in enumerate(raw_embeddings):
                embedding = item.get("embedding")

                if not isinstance(embedding, list):
                    raise ValueError(
                        f"NVIDIA returned an invalid embedding at index {i}"
                    )

                if len(embedding) != EMBEDDING_DIMENSION:
                    raise ValueError(
                        f"NVIDIA returned embedding dimension "
                        f"{len(embedding)} at index {i}; "
                        f"expected {EMBEDDING_DIMENSION}"
                    )

                embeddings.append(embedding)

            return embeddings

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            try:
                error_body = exc.response.text[:500]
            except Exception:
                error_body = "<unable to read response body>"

            logger.error(
                "[Embedding] NVIDIA API HTTP %s: %s",
                status_code,
                error_body,
            )

            if status_code < 500:
                raise RuntimeError(
                    f"NVIDIA embedding API error: {status_code}"
                ) from exc

            last_error = exc

        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            last_error = exc

            logger.warning(
                "[Embedding] NVIDIA request attempt %d failed: %s",
                attempt + 1,
                exc,
            )

        except Exception as exc:
            last_error = exc

            logger.warning(
                "[Embedding] Embedding attempt %d failed: %s",
                attempt + 1,
                exc,
            )

        if attempt == 0:
            await asyncio.sleep(0.3)

    logger.error(
        "[Embedding] NVIDIA embedding API failed after retries: %s",
        last_error,
    )

    raise RuntimeError(
        f"NVIDIA embedding service unreachable: {last_error}"
    ) from last_error

async def _embed_batched(
    texts: List[str],
    input_type: str,
) -> List[List[float]]:
    """
    Embed texts in batches according to EMBED_BATCH_SIZE.
    """
    if not texts:
        return []

    batch_size = settings.EMBED_BATCH_SIZE

    if batch_size <= 0:
        raise ValueError(
            f"EMBED_BATCH_SIZE must be greater than 0, got {batch_size}"
        )

    if len(texts) <= batch_size:
        return await _call_embed(
            texts,
            input_type=input_type,
        )

    results: List[List[float]] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]

        logger.debug(
            "[Embedding] Batch %d-%d of %d (%s)",
            start,
            start + len(batch),
            len(texts),
            input_type,
        )

        batch_results = await _call_embed(
            batch,
            input_type=input_type,
        )

        results.extend(batch_results)

    return results

async def embed_text(
    texts: List[str],
    input_type: str = "passage",
) -> List[List[float]]:
    """
    Embed a list of texts.

    Args:
        texts:
            Texts to embed.

        input_type:
            NVIDIA embedding context:
                - "query"   for search/user queries
                - "passage" for documents/passages

    Returns:
        One 2048-dimensional embedding per input text.
    """
    if not texts:
        return []

    if input_type not in {"query", "passage"}:
        raise ValueError(
            f"Invalid input_type: {input_type!r}. "
            "Expected 'query' or 'passage'."
        )

    results: List[Optional[List[float]]] = [None] * len(texts)

    miss_indices: List[int] = []
    miss_texts: List[str] = []


    for i, text in enumerate(texts):
        if not isinstance(text, str):
            raise TypeError(
                f"Expected text at index {i} to be str, "
                f"got {type(text).__name__}"
            )

        if not text.strip():
            raise ValueError(
                f"Text at index {i} is empty or whitespace-only"
            )

        cached = _cache_get(
            text,
            input_type=input_type,
        )

        if cached is not None:
            results[i] = cached
        else:
            miss_indices.append(i)
            miss_texts.append(text)

    if miss_texts:
        embeddings = await _embed_batched(
            miss_texts,
            input_type=input_type,
        )

        if len(embeddings) != len(miss_texts):
            raise RuntimeError(
                f"Embedding service returned {len(embeddings)} embeddings "
                f"for {len(miss_texts)} texts"
            )

        for idx, text, embedding in zip(
            miss_indices,
            miss_texts,
            embeddings,
        ):
            results[idx] = embedding

            _cache_set(
                text,
                input_type=input_type,
                embedding=embedding,
            )

    return [embedding for embedding in results if embedding is not None]


async def embed_query(query: str) -> List[float]:
    """
    Generate a query embedding.

    NVIDIA Nemotron 3 Embed supports distinct query and passage
    embedding contexts, so queries use input_type="query".
    """
    embeddings = await embed_text(
        [query],
        input_type="query",
    )

    return embeddings[0]


async def embed_passages(
    passages: List[str],
) -> List[List[float]]:
    """
    Generate passage/document embeddings.

    NVIDIA Nemotron 3 Embed uses input_type="passage" for documents.
    """
    return await embed_text(
        passages,
        input_type="passage",
    )