from langchain_core.documents import Document

from app.core.logger_handler import logger
from app.rag.bm25_retriever import BM25Service
from app.rag.vector_store import VectorStoreService


class HybridRetrieverService:
    """混合检索服务。"""

    def __init__(
        self,
        vector_store: VectorStoreService,
    ):
        self.vector_store = vector_store
        self.vector_retriever = vector_store.get_retriever()

        documents = vector_store.get_all_documents()

        self.bm25 = BM25Service(documents)

    def retrieve(
        self,
        query: str,
    ) -> list[Document]:
        """执行 Vector 与 BM25 混合检索。"""

        vector_docs = self.vector_retriever.invoke(query)

        bm25_docs = self.bm25.retrieve(query)

        documents = self._merge_documents(
            vector_docs,
            bm25_docs,
        )

        logger.info(
            "【Hybrid】Vector=%d，BM25=%d，合并后=%d",
            len(vector_docs),
            len(bm25_docs),
            len(documents),
        )

        return documents

    @staticmethod
    def _merge_documents(
        vector_docs: list[Document],
        bm25_docs: list[Document],
    ) -> list[Document]:
        """合并并去重检索结果。"""

        documents = []
        seen = set()

        for document in vector_docs + bm25_docs:
            metadata = document.metadata or {}

            key = (
                metadata.get("file_md5"),
                metadata.get("chunk_index"),
            )

            if key in seen:
                continue

            seen.add(key)
            documents.append(document)

        return documents
