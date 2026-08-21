from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    responses
)
from typing import Optional, List
from fastapi.responses import StreamingResponse

# from app.logic.llm_wrapper import async_generate
from app.logic.orchestrator import pipeline, pipeline_stream
from app.schemas.api_schema.chat_schema import (
    ChatReq,
    ChatStreamReq
)

router = APIRouter(
    prefix="/sherlock",
    tags=["Chat"]
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
        generated_answer = await  pipeline(
            query=request.query,
            history=request.history
        )

        return responses.JSONResponse({"answer": generated_answer})
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
