import asyncio
from pathlib import Path
from uuid import uuid4

from app.core.config import CHROMA_CONFIG
from app.core.logger_handler import logger
from app.core.path_tool import UPLOAD_DIR
from app.rag.vector_store import VectorStoreService


class KnowledgeService:
    """知识库业务服务。"""

    def __init__(self):
        self.vector_store = VectorStoreService()

    async def upload_file(
        self,
        filename: str,
        content: bytes,
    ) -> dict:
        """保存上传文件并写入向量数据库。"""

        safe_name = Path(filename).name
        suffix = Path(safe_name).suffix.lower()

        logger.info(
            "【Knowledge】开始处理上传文件：%s，大小：%.2f KB",
            safe_name,
            len(content) / 1024,
        )

        # 校验文件类型
        allowed_types = set(
            CHROMA_CONFIG["allowed_file_types"]
        )

        if suffix not in allowed_types:
            logger.warning(
                "【Knowledge】拒绝不支持的文件类型：%s，文件：%s",
                suffix,
                safe_name,
            )

            raise ValueError(
                f"不支持的文件类型：{suffix}"
            )

        # 防止空文件进入后续解析流程
        if not content:
            logger.warning(
                "【Knowledge】拒绝空文件：%s",
                safe_name,
            )

            raise ValueError(
                "上传文件不能为空"
            )

        # 确保上传目录存在
        UPLOAD_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        target_path = (
            UPLOAD_DIR / safe_name
        )

        # 同名文件不直接覆盖原文件
        if target_path.exists():
            target_path = (
                UPLOAD_DIR
                / (
                    f"{target_path.stem}_"
                    f"{uuid4().hex[:8]}"
                    f"{target_path.suffix}"
                )
            )

            logger.debug(
                "【Knowledge】检测到同名文件，新文件保存为：%s",
                target_path.name,
            )

        # 将 Streamlit 上传的二进制内容保存到本地
        try:
            await asyncio.to_thread(
                target_path.write_bytes,
                content,
            )

            logger.debug(
                "【Knowledge】上传文件已保存：%s",
                target_path,
            )

        except Exception:
            logger.exception(
                "【Knowledge】上传文件保存失败：%s",
                safe_name,
            )
            raise

        # 交给已有 RAG 流程完成解析、切片和向量入库
        try:
            chunk_count = (
                await self.vector_store.add_file(
                    target_path
                )
            )

        except Exception:
            logger.exception(
                "【Knowledge】文件写入知识库失败：%s",
                safe_name,
            )

            # 入库失败时删除刚保存的文件
            target_path.unlink(
                missing_ok=True
            )

            raise

        # DocumentProcessor 返回 0 表示文件内容已经存在
        if chunk_count == 0:
            logger.info(
                "【Knowledge】检测到重复文件，跳过入库：%s",
                safe_name,
            )

            # 删除刚才保存的重复副本
            target_path.unlink(
                missing_ok=True
            )

            return {
                "status": "duplicate",
                "filename": safe_name,
                "chunk_count": 0,
            }

        logger.info(
            "【Knowledge】文件写入知识库成功：%s，共 %d 个切片",
            target_path.name,
            chunk_count,
        )

        return {
            "status": "success",
            "filename": target_path.name,
            "chunk_count": chunk_count,
        }

    def upload_file_sync(
        self,
        filename: str,
        content: bytes,
    ) -> dict:
        """供 Streamlit 等同步界面调用。"""

        return asyncio.run(
            self.upload_file(
                filename,
                content,
            )
        )