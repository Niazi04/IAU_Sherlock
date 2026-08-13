from pydantic import BaseModel, Field
from typing import List, Dict

class Message(BaseModel):
    role:    str = Field(...,
                      description="The role rotation in llm history",
                      pattern='^(system|user|assistant)')
    content: str

    def __repr__(self):
        return f"Message:\n\trole -> {self.role!r}\n\tcontent -> {self.content[:65]!r}"