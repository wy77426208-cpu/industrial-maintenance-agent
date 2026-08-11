from functools import lru_cache

from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

from app.core.config import CHROMA_CONFIG
from app.core.logger_handler import logger


@lru_cache(maxsize=1)
def get_rerank_model() -> CrossEncoder:
    """获取并复用 Rerank 模型。"""

    model_name = CHROMA_CONFIG["rerank_model"]

    logger.info(
        "【Rerank】加载模型：%s",
        model_name,
    )

    return CrossEncoder(model_name)


class RerankService:
    """候选文档重排服务。"""

    def __init__(self):
        self.model = get_rerank_model()
        self.top_k = CHROMA_CONFIG["rerank_k"]

    def rerank(
        self,
        query: str,
        documents: list[Document],
    ) -> list[Document]:
        """根据查询与文档的相关性重新排序。"""

        if not documents:
            return []

        pairs = [
            (
                query,
                document.page_content,
            )
            for document in documents
        ]

        scores = self.model.predict(
            pairs,
            show_progress_bar=False,
        )

        ranked_results = sorted(
            zip(documents, scores),
            key=lambda item: float(item[1]),
            reverse=True,
        )

        result = []

        for rank, (document, score) in enumerate(
            ranked_results[: self.top_k],
            start=1,
        ):
            rerank_score = float(score)

            document.metadata["rerank_score"] = rerank_score

            logger.info(
                "【Rerank】Top%d：score=%.4f，文件=%s，页码=%s，切片=%s",
                rank,
                rerank_score,
                document.metadata.get(
                    "filename",
                    "未知来源",
                ),
                document.metadata.get(
                    "page_label",
                ),
                document.metadata.get(
                    "chunk_index",
                ),
            )

            result.append(document)

        return result
