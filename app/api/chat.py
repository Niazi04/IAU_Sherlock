from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    responses
)
from typing import Optional, List

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
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
