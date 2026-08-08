import asyncio
from pathlib import Path

from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import CHROMA_CONFIG
from app.core.logger_handler import logger
from app.rag.md5_store import MD5Store
from app.utils.file_handler import (
    get_file_md5_hex,
    markdown_loader,
    pdf_loader,
    ppt_loader,
    resolve_file_path,
    txt_loader,
    word_loader,
)


class DocumentProcessor:
    """负责文档解析、切片和向量入库。"""

    def __init__(
        self,
        vector_store: Chroma,
        md5_store: MD5Store,
        splitter: RecursiveCharacterTextSplitter,
    ):
        self.vector_store = vector_store
        self.md5_store = md5_store
        self.splitter = splitter

    async def _load_documents(
        self,
        file_path: Path,
    ):
        loaders = {
            ".pdf": pdf_loader,
            ".txt": txt_loader,
            ".md": markdown_loader,
            ".docx": word_loader,
            ".ppt": ppt_loader,
            ".pptx": ppt_loader,
        }

        loader = loaders.get(
            file_path.suffix.lower()
        )

        if loader is None:
            logger.warning(
                "【文档处理】暂不支持文件类型：%s",
                file_path.suffix,
            )
            return []

        return await loader(file_path)

    async def process_file(
        self,
        file_path: str | Path,
    ) -> int:
        """
        处理单个知识库文件。

        返回成功写入向量库的 chunk 数量。
        """
        abs_file_path = resolve_file_path(file_path)

        if not abs_file_path.is_file():
            logger.error(
                "【文档处理】文件不存在：%s",
                abs_file_path,
            )
            return 0

        if (
            abs_file_path.suffix.lower()
            not in CHROMA_CONFIG["allowed_file_types"]
        ):
            logger.warning(
                "【文档处理】不允许的文件类型：%s",
                abs_file_path.suffix,
            )
            return 0

        md5_hex = await get_file_md5_hex(
            abs_file_path
        )

        if not md5_hex:
            return 0

        if self.md5_store.contains(md5_hex):
            logger.info(
                "【文档处理】文件已存在知识库，跳过：%s",
                abs_file_path.name,
            )
            return 0

        documents = await self._load_documents(
            abs_file_path
        )

        if not documents:
            logger.warning(
                "【文档处理】未读取到有效内容：%s",
                abs_file_path.name,
            )
            return 0

        # 为文档保留文件级元数据。
        for document in documents:
            document.metadata.update(
                {
                    "filename": abs_file_path.name,
                    "file_md5": md5_hex,
                }
            )

        chunks = await asyncio.to_thread(
            self.splitter.split_documents,
            documents,
        )

        if not chunks:
            logger.warning(
                "【文档处理】文档切片为空：%s",
                abs_file_path.name,
            )
            return 0

        for index, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = index

        await asyncio.to_thread(
            self.vector_store.add_documents,
            chunks,
        )

        # 必须在向量入库成功以后再保存 MD5。
        self.md5_store.save(
            md5_hex=md5_hex,
            filename=abs_file_path.name,
            source=str(abs_file_path),
        )

        logger.info(
            "【文档处理】入库成功：%s，共 %d 个 chunk",
            abs_file_path.name,
            len(chunks),
        )

        return len(chunks)