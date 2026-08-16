from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class KnowledgeUploadResponse(BaseModel):
    """知识库文件上传结果。"""

    status: Literal["success", "duplicate"]
    filename: str
    chunk_count: int = Field(ge=0)

class KnowledgeFileResponse(BaseModel):
    """知识库文件信息。"""

    file_id: str
    filename: str
    created_at: datetime

class KnowledgeDeleteResponse(BaseModel):
    """知识库文件删除结果。"""

    file_id: str
    filename: str
    deleted_chunk_count: int = Field(ge=0)
    source_deleted: bool