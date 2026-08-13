from os import getenv
from pydantic_settings import BaseSettings
from  typing import Optional

class Settings(BaseSettings):
    
    LLM_API_URL:     str   = getenv("LLM_API_URL",    "")
    LLM_MODEL_NAAME: str   = getenv("LLM_MODEL_NAAME", "")
    VLLM_TEMP:       float = getenv("VLLM_TEMP",      0.0)
    VLLM_TOP_K:      int   = getenv("VLLM_TOP_K",     4)
    CONTEXT_WINDOW:  int   = getenv("CONTEXT_WINDOW", 4096)


    QDRNAT_URL:      str = getenv("QDRNAT_URL",       "")
    COLLECTION_NAME: str = getenv("COLLECTION_NAME",  "")

    VERSION: str = "1.0.0"

settings = Settings()
