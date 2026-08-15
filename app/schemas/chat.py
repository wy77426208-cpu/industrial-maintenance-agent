from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatSessionCreate(BaseModel):
    """创建聊天会话的请求模型。"""

    user_id: int = Field(gt=0)
    title: str = Field(
        default="新对话",
        min_length=1,
        max_length=200,
    )


class ChatSessionUpdate(BaseModel):
    """修改聊天会话标题的请求模型。"""

    title: str = Field(
        min_length=1,
        max_length=200,
    )


class ChatSessionResponse(BaseModel):
    """聊天会话的响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime


class ChatMessageCreate(BaseModel):
    """发送聊天消息的请求模型。"""

    user_id: int = Field(gt=0)
    content: str = Field(min_length=1)


class ChatMessageResponse(BaseModel):
    """聊天消息的响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime