from pathlib import Path

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from app.core.logger_handler import logger
from app.model.factory import chat_model
from app.rag.hybrid_retriever import HybridRetrieverService
from app.rag.reranker import RerankService
from app.rag.vector_store import VectorStoreService
from app.utils.prompt_loader import load_prompt


def log_prompt(prompt):
    """记录 RAG Prompt。"""
    logger.debug(
        "【RAG Prompt】\n%s",
        prompt.to_string(),
    )
    return prompt


class RagService:
    """RAG 检索与问答服务。"""

    def __init__(self):
        self.vector_store = VectorStoreService()
        self.hybrid_retriever = HybridRetrieverService(self.vector_store)
        self.reranker = RerankService()

        self.prompt_text = load_prompt("rag_summary_prompt")
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        self.model = chat_model
        self.chain = self._init_chain()

    def _init_chain(self):
        """初始化 RAG 总结链。"""
        return (
            self.prompt_template
            | log_prompt
            | self.model
            | StrOutputParser()
        )

    def retrieve_docs(
        self,
        query: str,
    ) -> list[Document]:
        """检索并重排相关文档切片。"""

        candidates = self.hybrid_retriever.retrieve(query)

        logger.info(
            "【RAG】候选检索完成，query=%s，返回 %d 个切片",
            query,
            len(candidates),
        )

        docs = self.reranker.rerank(
            query,
            candidates,
        )

        logger.info(
            "【RAG】重排完成，保留 %d 个切片",
            len(docs),
        )

        return docs

    @staticmethod
    def _get_filename(
        metadata: dict,
    ) -> str:
        """从 metadata 中获取文件名。"""

        filename = metadata.get("filename")

        if filename:
            return str(filename)

        source = metadata.get("source")

        if source:
            return Path(str(source)).name

        return "未知来源"

    @classmethod
    def format_context(
        cls,
        docs: list[Document],
    ) -> str:
        """将检索结果整理为 Agent 可读取的证据文本。"""

        if not docs:
            return "未检索到相关参考资料。"

        context_parts = []

        for index, doc in enumerate(
            docs,
            start=1,
        ):
            metadata = doc.metadata or {}

            filename = cls._get_filename(metadata)
            page_label = metadata.get("page_label")
            chunk_index = metadata.get("chunk_index")

            source_info = [
                f"文件：{filename}"
            ]

            if page_label is not None:
                source_info.append(
                    f"页码：{page_label}"
                )

            if chunk_index is not None:
                source_info.append(
                    f"切片：{chunk_index}"
                )

            context_parts.append(
                f"【参考资料{index}】\n"
                f"{'，'.join(source_info)}\n"
                f"{doc.page_content.strip()}"
            )

        return "\n\n".join(context_parts)

    def search(
        self,
        query: str,
    ) -> str:
        """检索知识库并返回相关原始资料。"""

        docs = self.retrieve_docs(query)
        context = self.format_context(docs)

        logger.debug(
            "【RAG】原始检索上下文：\n%s",
            context,
        )

        return context

    def answer(
        self,
        query: str,
    ) -> str:
        """根据检索资料生成回答。"""

        docs = self.retrieve_docs(query)
        context = self.format_context(docs)

        return self.chain.invoke(
            {
                "input": query,
                "context": context,
            }
        )