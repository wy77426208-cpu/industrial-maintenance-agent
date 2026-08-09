from pathlib import Path

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from app.core.logger_handler import logger
from app.model.factory import chat_model
from app.rag.vector_store import VectorStoreService
from app.utils.prompt_loader import load_prompt


def log_prompt(prompt):
    """记录最终发送给模型的 Prompt。"""

    logger.debug(
        "【RAG Prompt】\n%s",
        prompt.to_string(),
    )

    return prompt


class RagService:
    """RAG 检索问答服务。"""

    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retriever()

        self.prompt_text = load_prompt(
            "rag_summary_prompt"
        )

        self.prompt_template = (
            PromptTemplate.from_template(
                self.prompt_text
            )
        )

        self.model = chat_model
        self.chain = self._init_chain()

    def _init_chain(self):
        """创建 RAG 生成链。"""

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
        """根据问题检索相关文档。"""

        return self.retriever.invoke(query)

    @staticmethod
    def format_context(
        docs: list[Document],
    ) -> str:
        """将检索结果整理为 Prompt 上下文。"""

        if not docs:
            return "未检索到相关参考资料。"

        context_parts = []

        for index, doc in enumerate(
            docs,
            start=1,
        ):
            metadata = doc.metadata or {}

            filename = metadata.get("filename")

            if not filename:
                source = metadata.get("source")

                if source:
                    filename = Path(
                        str(source)
                    ).name

            filename = filename or "未知来源"

            page_label = metadata.get(
                "page_label"
            )

            chunk_index = metadata.get(
                "chunk_index"
            )

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

    def answer(
        self,
        query: str,
    ) -> str:
        """检索知识库并生成回答。"""

        docs = self.retrieve_docs(query)

        context = self.format_context(
            docs
        )

        return self.chain.invoke(
            {
                "input": query,
                "context": context,
            }
        )


if __name__ == "__main__":
    rag = RagService()

    result = rag.answer(
        "这个PDF是用来做什么的？"
    )

    print("\n========== RAG 回答 ==========")
    print(result)

