from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ChatMessage, ChatSession


async def create_chat_session(
    db: AsyncSession,
    user_id: int,
    title: str = "新对话",
) -> ChatSession:
    """创建聊天会话。"""

    chat_session = ChatSession(user_id=user_id, title=title)
    db.add(chat_session)
    await db.commit()
    await db.refresh(chat_session)
    return chat_session


async def get_chat_session(
    db: AsyncSession,
    session_id: int,
    user_id: int,
) -> ChatSession | None:
    """获取指定用户的聊天会话。"""

    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_user_sessions(
    db: AsyncSession,
    user_id: int,
) -> list[ChatSession]:
    """获取用户的全部聊天会话。"""

    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
    )
    return list(result.scalars().all())


async def add_message(
    db: AsyncSession,
    session_id: int,
    user_id: int,
    role: str,
    content: str,
) -> ChatMessage:
    """添加聊天消息。"""

    chat_session = await get_chat_session(db, session_id, user_id)
    if chat_session is None:
        raise ValueError("聊天会话不存在")

    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
    )

    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_messages(
    db: AsyncSession,
    session_id: int,
    user_id: int,
) -> list[ChatMessage]:
    """获取聊天会话的全部消息。"""

    chat_session = await get_chat_session(db, session_id, user_id)
    if chat_session is None:
        raise ValueError("聊天会话不存在")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return list(result.scalars().all())


async def update_chat_title(
    db: AsyncSession,
    session_id: int,
    user_id: int,
    title: str,
) -> ChatSession:
    """修改聊天会话标题。"""

    chat_session = await get_chat_session(db, session_id, user_id)
    if chat_session is None:
        raise ValueError("聊天会话不存在")

    chat_session.title = title
    await db.commit()
    await db.refresh(chat_session)
    return chat_session


async def delete_chat_session(
    db: AsyncSession,
    session_id: int,
    user_id: int,
) -> bool:
    """删除聊天会话。"""

    chat_session = await get_chat_session(db, session_id, user_id)
    if chat_session is None:
        return False

    await db.delete(chat_session)
    await db.commit()
    return True