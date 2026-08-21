from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    responses
)
import httpx
from typing import Optional, List
from fastapi.responses import StreamingResponse

from app.logic.orchestrator import pipeline, pipeline_stream
from app.schemas.api_schema.chat_schema import (
    ChatReq,
    ChatStreamReq
)
from app.utils.cutom_exceptions import (
    APIKeyInvalid,
    RateLimit,
)
from app.core.dependencies import get_api_key

router = APIRouter(
    prefix="/sherlock",
    tags=["Chat"],
    dependencies=[Depends(get_api_key)]
)


@router.post(
        "/chat",
        status_code=200,
        summary="Generated the entire respoonse and then return them (Non-streaming)",
)
async def chat(
    request: ChatReq
):
    try:
        generated_answer = await pipeline(
            query=request.query,
            history=request.history
        )
        return responses.JSONResponse({"answer": generated_answer})
    except RateLimit as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except APIKeyInvalid as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
@router.post("/stream")
async def chat(request: ChatReq):
    try:
        return StreamingResponse(
            pipeline_stream(
                query=request.query,
                history=request.history
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                # "X-Accel-Buffering": "no"  # Disable nginx buffering if you use nginx
            }
        )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
