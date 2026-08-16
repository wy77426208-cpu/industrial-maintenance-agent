from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionUpdate,
)
from app.services.chat_service import (
    add_message,
    create_chat_session,
    delete_chat_session,
    get_messages,
    get_user_sessions,
    update_chat_title,
)


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

@chat_router.get(
    "/sessions",
    response_model=list[ChatSessionResponse],
)
async def list_sessions(
    user_id: int = Query(gt=0),
    db: AsyncSession = Depends(get_db),
) -> list[ChatSessionResponse]:
    """查询用户的全部聊天会话。"""

    sessions = await get_user_sessions(
        db=db,
        user_id=user_id,
    )

    return [
        ChatSessionResponse.model_validate(session)
        for session in sessions
    ]

@chat_router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    session_id: int,
    request: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    """向指定聊天会话添加用户消息。"""

    try:
        message = await add_message(
            db=db,
            session_id=session_id,
            user_id=request.user_id,
            role="user",
            content=request.content,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ChatMessageResponse.model_validate(message)

@chat_router.get(
    "/sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
)
async def list_messages(
    session_id: int,
    user_id: int = Query(gt=0),
    db: AsyncSession = Depends(get_db),
) -> list[ChatMessageResponse]:
    """查询指定聊天会话的全部消息。"""

    try:
        messages = await get_messages(
            db=db,
            session_id=session_id,
            user_id=user_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return [
        ChatMessageResponse.model_validate(message)
        for message in messages
    ]

@chat_router.patch(
    "/sessions/{session_id}",
    response_model=ChatSessionResponse,
)
async def update_session_title(
    session_id: int,
    request: ChatSessionUpdate,
    user_id: int = Query(gt=0),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionResponse:
    """修改聊天会话标题。"""

    try:
        chat_session = await update_chat_title(
            db=db,
            session_id=session_id,
            user_id=user_id,
            title=request.title,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ChatSessionResponse.model_validate(chat_session)

@chat_router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_session(
    session_id: int,
    user_id: int = Query(gt=0),
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除指定聊天会话。"""

    deleted = await delete_chat_session(
        db=db,
        session_id=session_id,
        user_id=user_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在",
        )