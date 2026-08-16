from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent import MaintAIAgent
from app.database.models import ChatMessage
from app.services.chat_service import (
    add_message,
    get_messages,
)


@lru_cache(maxsize=1)
def get_agent() -> MaintAIAgent:
    """创建并复用同一个Agent实例。"""

    return MaintAIAgent()


async def chat_with_agent(
    db: AsyncSession,
    session_id: int,
    user_id: int,
    content: str,
) -> tuple[ChatMessage, ChatMessage]:
    """保存用户问题，调用Agent，并保存助手回答。"""

    history_messages = await get_messages(
        db=db,
        session_id=session_id,
        user_id=user_id,
    )

    history = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in history_messages
    ]

    user_message = await add_message(
        db=db,
        session_id=session_id,
        user_id=user_id,
        role="user",
        content=content,
    )

    answer = await get_agent().ainvoke(
        query=content,
        history=history,
    )

    assistant_message = await add_message(
        db=db,
        session_id=session_id,
        user_id=user_id,
        role="assistant",
        content=answer,
    )

    return user_message, assistant_message