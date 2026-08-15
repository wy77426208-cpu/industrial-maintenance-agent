from datetime import datetime
from types import SimpleNamespace

from pydantic import ValidationError

from app.schemas.chat import (
    ChatMessageCreate,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionUpdate,
)


# 1. 测试合法的创建会话请求
valid_session = ChatSessionCreate(
    user_id=1,
    title="电机故障诊断",
)

print("合法会话请求：", valid_session.model_dump())


# 2. 测试默认标题
default_title_session = ChatSessionCreate(
    user_id=1,
)

print("默认标题：", default_title_session.title)


# 3. 测试非法user_id
try:
    ChatSessionCreate(
        user_id=0,
        title="电机故障诊断",
    )
except ValidationError as error:
    print("非法user_id已被拦截：")
    print(error.errors()[0]["msg"])


# 4. 测试空标题
try:
    ChatSessionUpdate(title="")
except ValidationError as error:
    print("空标题已被拦截：")
    print(error.errors()[0]["msg"])


# 5. 测试空消息
try:
    ChatMessageCreate(
        user_id=1,
        content="",
    )
except ValidationError as error:
    print("空消息已被拦截：")
    print(error.errors()[0]["msg"])


# 6. 模拟SQLAlchemy查询得到的ORM实例
fake_chat_session = SimpleNamespace(
    id=10,
    user_id=1,
    title="电机故障诊断",
    created_at=datetime.now(),
    updated_at=datetime.now(),
)

response = ChatSessionResponse.model_validate(
    fake_chat_session
)

print("响应模型转换成功：")
print(response.model_dump())