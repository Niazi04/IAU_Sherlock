from typing import (
    List,
    Dict,
    Optional,
    Any
)

from app.schemas.general import Message

__all__ = [
    "sanitize_history"
]

def sanitize_history(history: List[Message]) -> List[Dict[str, str]]:
    if not history:
        return []
    
    sanitized: List[Dict]    = []
    last_role: Optional[str] = None
    
    for i, msg in enumerate(history):
        role = msg.role
        content = msg.content.strip()
        
        if role == 'system':
            if i != 0:
                raise ValueError(f"System message found at index {i}. System messages are only allowed at the beginning")

            sanitized.append({"role": "system", "content": content})
            last_role = "system"
            continue
        
        if role not in ['user', 'assistant']:
            raise ValueError(f"Invalid role '{role}' at index {i}")
        
        if last_role == 'system' and  role != 'user':
            raise ValueError(f"First non-system message must be from 'user', got '{role}' at index {i}")
        if role == last_role:
            raise ValueError(f"Consecutive '{role}' messages at index {i-1} and {i}. Messages must alternate between 'user' and 'assistant'")
        
        sanitized.append({"role": role, "content": content})
        last_role = role
    
    # Optional: Ensure the last message is from 'user' (OpenAI's recommendation)
    # Some OpenAI models work better with user as the last message
    # if sanitized and sanitized[-1]['role'] == 'assistant':
        # This is allowed but we could issue a warning
        # pass
    
    return sanitized