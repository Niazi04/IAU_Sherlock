import openai
from typing import Optional, List, Dict
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

__all__ = [
    "async_generate",
    "async_generate_stream",
    "_get_client",
]

_client = None

async def _get_client() -> bool:
    global _client

    if not settings.LLM_API_KEY:
        raise ValueError(
            "LLM_API_KEY not set. Set it in .env file."
        )

    try:
        _client = openai.AsyncOpenAI(
            base_url = settings.LLM_API_URL,
            api_key  = settings.LLM_API_KEY
        )
        logger.info("[LLM] Connected to llm successfully")
        return True
    except Exception as e:
        logger.critical("[LLM] An error happended while connecting to the llm client:")
        logger.critical(f"[LLM] {str(e)}")

        exit(-1)

def _build_params(
        temp:             Optional[float] = None,
        max_tokens:       Optional[int]   = None,
        llm_model_name:   Optional[str]   = None,
        reasoning_effort: Optional[str]   = None,
        ):
    return dict(
        model            = llm_model_name if llm_model_name is not None else settings.LLM_MODEL_NAME,
        temperature      = temp if temp is not None else settings.LLM_TEMP,
        top_p            = settings.LLM_TOP_P,
        max_tokens       = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKEN,
        reasoning_effort = reasoning_effort if reasoning_effort is not None else settings.LLM_REASONING_EFFORT 
        # seed        = settings.LLM_SEED, -> for some reason google gemeni does not support seed
    )

async def async_generate(
    msg:            List[Dict[str, str]],
    temp:           Optional[float]       = None,
    max_tokens:     Optional[int]         = None,
    llm_model_name: Optional[str]         = None,

):
    if _client is None: await _get_client()

    params = _build_params()
    try:
        res = await _client.chat.completions.create(
            messages=msg,
            stream=False,
            **params
        )

        logger.debug("[LLM] respone was generated:")
        logger.debug(f"[LLM] {res.choices[0].message.content}")
        return res.choices[0].message.content
        
    
    except Exception as e:
        logger.warning("[LLM] Something went wrong while generating an answer:")
        logger.warning(f"[LLM] {str(e)}")
        raise

async def async_generate_stream():
    #TODO
    pass