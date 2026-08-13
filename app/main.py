from fastapi import FastAPI

from app.api import chat
from app.core.config import settings

app = FastAPI(
    title    = "A retrieval augmented generator made for my uni",
    version  = settings.VERSION,
    docs_url = "/docs",
)

app.include_router(chat.router)

@app.get("/health")
def  health():
    return {
        "status": "OK",
        "version": settings.VERSION,
        "llm_model": settings.LLM_MODEL_NAAME
    }