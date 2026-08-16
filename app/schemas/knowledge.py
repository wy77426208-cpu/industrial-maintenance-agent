from typing import Literal

from pydantic import BaseModel, Field


class KnowledgeUploadResponse(BaseModel):
    """知识库文件上传结果。"""

    status: Literal["success", "duplicate"]
    filename: str
    chunk_count: int = Field(ge=0)