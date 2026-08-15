import jieba
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from app.core.config import CHROMA_CONFIG
from app.core.logger_handler import logger


def tokenize_text(
    text: str,
) -> list[str]:
    """对检索文本进行中文分词。"""

    tokens = jieba.lcut_for_search(text.lower())

    return [token.strip() for token in tokens if token.strip()]


class BM25Service:
    """BM25 关键词检索服务。"""

    def __init__(
        self,
        documents: list[Document],
    ):
        self.documents = documents
        self.top_k = CHROMA_CONFIG["bm25_k"]
        self.retriever = self._build_retriever()

    def _build_retriever(
        self,
    ) -> BM25Retriever | None:
        """创建 BM25 检索器。"""

        if not self.documents:
            return None

        retriever = BM25Retriever.from_documents(
            self.documents,
            preprocess_func=tokenize_text,
            k=self.top_k,
        )

        logger.info(
            "【BM25】索引创建完成，共 %d 个切片",
            len(self.documents),
        )

        return retriever

    def retrieve(
        self,
        query: str,
    ) -> list[Document]:
        """根据关键词相关性检索文档切片。"""

        if self.retriever is None:
            return []

        documents = self.retriever.invoke(query)

        logger.info(
            "【BM25】检索完成，query=%s，返回 %d 个切片",
            query,
            len(documents),
        )

        for index, document in enumerate(
            documents,
            start=1,
        ):
            metadata = document.metadata or {}

            logger.info(
                "【BM25】Top%d：文件=%s，页码=%s，切片=%s",
                index,
                metadata.get(
                    "filename",
                    "未知来源",
                ),
                metadata.get(
                    "page_label",
                ),
                metadata.get(
                    "chunk_index",
                ),
            )

        return documents
