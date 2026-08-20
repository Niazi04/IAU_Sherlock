from os import getenv
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from  typing import Optional

class Settings(BaseSettings):
    
    
    LLM_API_URL:          str   = ""
    LLM_MODEL_NAME:       str   = ""
    LLM_API_KEY:          str   = ""
    LLM_REASONING_EFFORT: str = ""
    LLM_TEMP:             float = 0.0
    LLM_TOP_P:            float = 0
    LLM_MAX_TOKEN:        int   = 0
    LLM_SEED:             int   = 0
    CONTEXT_WINDOW:       int   = 0

    EMBEDDING_SERVICE_URL: str = "http://192.168.91.17:8010"
    EMBEDDING_DIM:         str = ""
    EMBED_BATCH_SIZE:      int = 0
    EMBED_TIMEOUT:         float = 30.0

    QDRANT_URL:          str = ""
    QDRANT_API_KEY:      str = ""
    COLLECTION_NAME:     str = ""
    FAQ_COLLECTION_NAME: str = ""
    FAQ_RERANK_FETCH_K:  int = 3

    VERSION: str = "1.0.0"
    LOG_LVL: str = ""


    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()


# LLM_API_URL:     str   = getenv("LLM_API_URL",    "")
    # LLM_MODEL_NAME:  str   = getenv("LLM_MODEL_NAME", "")
    # LLM_API_KEY:     str   = getenv("LLM_API_KEY",    "")
    # LLM_TEMP:        float = getenv("LLM_TEMP",       0.0)
    # LLM_TOP_K:       int   = getenv("LLM_TOP_K",      4)
    # LLM_MAX_TOKEN:   int   = getenv("LLM_MAX_TOKEN",  4)
    # LLM_SEED:        int   = getenv("LLM_SEED",       67)
    # CONTEXT_WINDOW:  int   = getenv("CONTEXT_WINDOW", 4096)


    # QDRNAT_URL:      str = getenv("QDRNAT_URL",       "")
    # COLLECTION_NAME: str = getenv("COLLECTION_NAME",  "")