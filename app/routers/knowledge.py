from functools import lru_cache

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.knowledge import (
    KnowledgeDeleteResponse,
    KnowledgeFileResponse,
    KnowledgeUploadResponse,
)
from app.services.knowledge_service import KnowledgeService


knowledge_router = APIRouter(
    prefix="/api/knowledge",
    tags=["knowledge"],
)


@lru_cache(maxsize=1)
def get_knowledge_service() -> KnowledgeService:
    """获取并复用知识库服务实例。"""

    return KnowledgeService()

@knowledge_router.get(
    "/files",
    response_model=list[KnowledgeFileResponse],
)
def list_knowledge_files() -> list[KnowledgeFileResponse]:
    """获取知识库文件列表。"""

    records = get_knowledge_service().list_files()

    return [
        KnowledgeFileResponse.model_validate(record)
        for record in records
    ]


@knowledge_router.delete(
    "/files/{file_id}",
    response_model=KnowledgeDeleteResponse,
)
async def delete_knowledge_file(
    file_id: str,
) -> KnowledgeDeleteResponse:
    """删除指定知识库文件。"""

    result = await get_knowledge_service().delete_file(file_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库文件不存在",
        )

    return KnowledgeDeleteResponse.model_validate(result)


@knowledge_router.post(
    "/upload",
    response_model=KnowledgeUploadResponse,
)
async def upload_knowledge_file(
    file: UploadFile = File(...),
) -> KnowledgeUploadResponse:
    """上传文件并写入知识库。"""

    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="上传文件必须包含文件名",
            )

        content = await file.read()

        result = await get_knowledge_service().upload_file(
            filename=file.filename,
            content=content,
        )

        return KnowledgeUploadResponse.model_validate(result)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    finally:
        await file.close()