from pydantic import BaseModel, Field
from typing import (
    List,
    Dict,
    Any
)


class ChatReq(BaseModel):
    query: str

class ChatStreamReq(BaseModel):
    query: str