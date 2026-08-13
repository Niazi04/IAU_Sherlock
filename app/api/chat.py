from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    responses
)
from typing import Optional, List

from app.logic.llm_wrapper import async_generate
from app.schemas.api_schema.chat_schema import (
    ChatReq,
    ChatStreamReq
)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post(
        "/chat",
        status_code=200,
        summary="Hello World to keep traditions alive",
        description=(
            "My first hello world was in C++ "
            "I guess no one forgets that "
        )
)
async def chat(
    request: ChatReq
):
    try:
        res = await async_generate(
            [
                {
                    "role": "system",
                    "content": "You are a helpful scientific assistant"
                },
                {
                    "role": "user",
                    "content": request.query}
            ]
        )

        return responses.JSONResponse({"res": res})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get(
    "/hello-world",
    status_code=200,
    summary="Hello World to keep traditions alive",
    description=(
        "My first hello world was in C++ "
        "I guess no one forgets that "
    )
)
def hello_world():
    return responses.JSONResponse({"res": "hello world"})
