from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
)
from app.services.chat_service import create_chat_session


chat_router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
)


@chat_router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    request: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
) -> ChatSessionResponse:
    """创建聊天会话。"""

    chat_session = await create_chat_session(
        db=db,
        user_id=request.user_id,
        title=request.title,
    )

    return ChatSessionResponse.model_validate(
        chat_session
    )