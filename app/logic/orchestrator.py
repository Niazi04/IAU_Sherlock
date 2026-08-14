from typing import (
    Any,
    List,
    Dict,
    Optional
)

from app.logic.llm_wrapper import async_generate
from app.utils.message_cleanup import sanitize_history
from app.schemas.general import Message
from app.core.prompts import TEST_PROMPT

__all__ = [
    "pipeline"
]

# Types
# Custome typse are prefixed by `T_`
T_History = List[Dict[str, str]]
T_Conv    = List[Dict[str, str]]


# Function Signitures
# Only helper functions go here
def _build_conv(query: str, prompt: str = TEST_PROMPT, history: Optional[T_History] = None)-> T_Conv: ...

async def pipeline(
    query:     str,
    history:   Optional[List[Message]] = None,
    user_name: Optional[str] = None
):
    clean_history = sanitize_history(history)
    conversation  = _build_conv(
        query=query,
        history=clean_history)

    res = await async_generate(conversation)

    return res.strip()


# Function definition
def _build_conv(
        query:   str, 
        prompt:  str                 = TEST_PROMPT,
        history: Optional[T_History] = None
) -> T_Conv:
    conversation = [
        {
            "role":    "system",
            "content": prompt
        }
    ]

    if history: conversation = conversation + history

    conversation.append(
        {
            "role":    "user",
            "content": query
        }
    )
    return conversation