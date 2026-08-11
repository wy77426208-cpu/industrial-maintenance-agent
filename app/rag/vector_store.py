from pathlib import Path

from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import CHROMA_CONFIG
from app.core.path_tool import CHROMA_DIR, DATA_DIR
from app.model.factory import embed_model
from app.rag.document_processor import DocumentProcessor
from app.rag.md5_store import MD5Store
from app.utils.file_handler import listdir_allowed_type


class VectorStoreService:
    """知识库向量存储服务。"""

    def __init__(self):

        self.vector_store = Chroma(
            collection_name=CHROMA_CONFIG[
                "collection_name"
            ],
            embedding_function=embed_model,
            persist_directory=str(CHROMA_DIR),
        )

        self.splitter = (
            RecursiveCharacterTextSplitter(
                chunk_size=CHROMA_CONFIG[
                    "chunk_size"
                ],
                chunk_overlap=CHROMA_CONFIG[
                    "chunk_overlap"
                ],
            )
        )

        self.md5_store = MD5Store()

        self.document_processor = DocumentProcessor(
            vector_store=self.vector_store,
            md5_store=self.md5_store,
            splitter=self.splitter,
        )

    def get_retriever(self):
        """获取基础向量检索器。"""
        return self.vector_store.as_retriever(
            search_kwargs={
                "k": CHROMA_CONFIG["candidate_k"]
            }
        )

    async def add_file(
        self,
        file_path: str | Path,
    ) -> int:
        """将单个文件加入知识库。"""
        return (
            await self.document_processor.process_file(
                file_path
            )
        )

    async def load_directory(
        self,
        directory: str | Path = DATA_DIR,
    ) -> dict[str, int]:
        """加载目录内允许的知识库文件。"""

        files = await listdir_allowed_type(
            directory,
            tuple(
                CHROMA_CONFIG[
                    "allowed_file_types"
                ]
            ),
        )

        result = {}

        for file_path in files:
            chunk_count = await self.add_file(
                file_path
            )

            result[file_path.name] = chunk_count

        return result

if __name__ == "__main__":
    import asyncio

async def main():
    service = VectorStoreService()

    print("\n========== 1. 初始化 ==========")
    print("VectorStoreService 初始化成功")

    print("\n========== 2. 文档入库 ==========")
    result = await service.load_directory()
    print("文档入库结果：", result)

    print("\n========== 3. 向量检索 ==========")
    retriever = service.get_retriever()

    docs = retriever.invoke(
        "这个PDF是用来做什么的？"
    )

    for index, doc in enumerate(docs, start=1):
        print(f"\n--- 文档 {index} ---")
        print(doc.page_content)
        print("metadata:", doc.metadata)

    print("\n========== 测试结束 ==========\n")