from pydantic import BaseModel, Field
from typing import (
    List,
    Dict,
    Optional,
    Any
)

from app.schemas.general import Message

class ChatReq(BaseModel):
    query:     str                     = Field(..., description="User question that will be fed into the RAG pipeline")
    user_name: Optional[str]           = Field(default=None, description="Users username dah")
    history:   Optional[List[Message]] = Field(default=None, description="Previous message between user and agent")

class ChatStreamReq(BaseModel):
    query: str