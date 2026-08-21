from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Message(BaseModel):
    role:    str = Field(...,
                      description="The role rotation in llm history",
                      pattern='^(system|user|assistant)')
    content: str

    def __repr__(self):
        return f"Message:\n\trole -> {self.role!r}\n\tcontent -> {self.content[:65]!r}"

class RetrievalResult(BaseModel):
    text: str
    score: float
    metadata: Dict[str, Any] = {}


class IngestTextRequest(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    collection: Optional[str] = None
    chunk_size: Optional[int] = Field(default=800)
    chunk_overlap: Optional[int] = Field(default=150)


class IngestResponse(BaseModel):
    status: str
    chunks_processed: int
    message: str
    collection: Optional[str] = None