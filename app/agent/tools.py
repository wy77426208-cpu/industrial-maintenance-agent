from datetime import datetime
from functools import lru_cache

from langchain_core.tools import tool

from app.rag.rag_service import RagService


@lru_cache(maxsize=1)
def get_rag_service() -> RagService:
    """获取并复用 RAG 服务实例。"""
    return RagService()


@tool(
    description=(
        "查询 MaintAI 本地知识库中的文档内容。"
        "可用于查询已上传的 PDF、TXT、Word、Markdown、PPT 等文档，"
        "包括设备手册、故障说明、维护方法、操作规范等资料。"
        "当用户询问知识库、已上传文档、PDF、手册或文档中的具体内容时，"
        "应使用此工具获取可靠依据。"
    )
)
def search_knowledge(
    query: str,
) -> str:
    """根据问题查询工业设备知识库。"""

    rag_service = get_rag_service()

    return rag_service.answer(query)


@tool(
    description=(
        "获取当前系统的日期和时间。"
        "当用户询问当前日期、时间或需要当前时间信息时使用。"
    )
)
def get_current_time() -> str:
    """获取当前系统时间。"""

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


if __name__ == "__main__":
    print(
        "\n========== 知识库 Tool =========="
    )

    result = search_knowledge.invoke(
        {
            "query": "这个PDF是用来做什么的？"
        }
    )

    print(result)

    print(
        "\n========== 时间 Tool =========="
    )

    time_result = get_current_time.invoke({})

    print(time_result)