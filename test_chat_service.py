import asyncio
from uuid import uuid4

from app.database.db import AsyncSessionLocal, engine
from app.database.models import User
from app.services.chat_service import (
    add_message,
    create_chat_session,
    delete_chat_session,
    get_messages,
    get_user_sessions,
    update_chat_title,
)


async def main():
    try:
        async with AsyncSessionLocal() as db:
            # 创建测试用户
            user = User(
                username=f"test_user_{uuid4().hex[:8]}"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            print(f"用户创建成功：id={user.id}, username={user.username}")

            # 创建属于该用户的聊天会话
            chat_session = await create_chat_session(
                db=db,
                user_id=user.id,
                title="电机故障诊断",
            )

            print(
                f"会话创建成功：id={chat_session.id}, "
                f"user_id={chat_session.user_id}, "
                f"title={chat_session.title}"
            )

                        # 添加用户消息
            await add_message(
                db=db,
                session_id=chat_session.id,
                user_id=user.id,
                role="user",
                content="电机运行时温度过高，应该检查什么？",
            )

            # 添加助手消息
            await add_message(
                db=db,
                session_id=chat_session.id,
                user_id=user.id,
                role="assistant",
                content="建议先检查电机负载、散热风扇和轴承状态。",
            )

            # 查询当前会话的全部消息
            messages = await get_messages(
                db=db,
                session_id=chat_session.id,
                user_id=user.id,
            )

            print(f"查询到消息数量：{len(messages)}")

            for message in messages:
                print(
                    f"消息：id={message.id}, "
                    f"role={message.role}, "
                    f"content={message.content}"
                )

                        # 查询当前用户的全部会话
            sessions = await get_user_sessions(
                db=db,
                user_id=user.id,
            )

            print(f"当前用户的会话数量：{len(sessions)}")

            # 修改会话标题
            updated_session = await update_chat_title(
                db=db,
                session_id=chat_session.id,
                user_id=user.id,
                title="电机高温故障排查",
            )

            print(f"修改后的标题：{updated_session.title}")

            # 删除当前会话
            deleted = await delete_chat_session(
                db=db,
                session_id=chat_session.id,
                user_id=user.id,
            )

            print(f"会话删除结果：{deleted}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())