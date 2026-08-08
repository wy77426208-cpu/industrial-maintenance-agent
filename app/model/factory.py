import os
from abc import ABC, abstractmethod
from functools import lru_cache

from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.logger_handler import logger
from app.core.path_tool import ENV_FILE

load_dotenv(ENV_FILE)


class DashScopeEmbeddingsWrapper(Embeddings):
    """将 DashScope Embedding API 适配为 LangChain Embeddings。"""

    def __init__(
        self,
        model_name: str = "text-embedding-v4",
        api_key: str | None = None,
    ):
        try:
            import dashscope
        except ImportError as exc:
            raise ImportError(
                "缺少 dashscope，请执行：python -m pip install dashscope"
            ) from exc

        self.dashscope = dashscope
        self.model_name = model_name

        self.dashscope.api_key = (
            api_key
            or os.getenv("ALIYUN_ACCESS_KEY_SECRET")
        )

        if not self.dashscope.api_key:
            raise ValueError("未配置阿里云 DashScope API Key")

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """批量将文档转换为向量。"""

        if not texts:
            return []

        results = []
        batch_size = 10

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            response = self.dashscope.TextEmbedding.call(
                model=self.model_name,
                input=batch,
            )

            if response.status_code != 200:
                logger.error(
                    "【Embedding】DashScope 调用失败：%s",
                    response.message,
                )
                raise RuntimeError(
                    f"DashScope Embedding 调用失败：{response.message}"
                )

            results.extend(
                item["embedding"]
                for item in response.output["embeddings"]
            )

        return results

    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        """将单条查询转换为向量。"""

        response = self.dashscope.TextEmbedding.call(
            model=self.model_name,
            input=text,
        )

        if response.status_code != 200:
            logger.error(
                "【Embedding】DashScope 调用失败：%s",
                response.message,
            )
            raise RuntimeError(
                f"DashScope Embedding 调用失败：{response.message}"
            )

        return response.output["embeddings"][0]["embedding"]


class BaseModelFactory(ABC):
    """模型工厂基类。"""

    @abstractmethod
    def generator(
        self,
    ) -> BaseChatModel | Embeddings:
        pass


class ChatModelFactory(BaseModelFactory):
    """聊天模型工厂。"""

    @lru_cache(maxsize=1)
    def generator(self) -> BaseChatModel:
        llm_type = (
            os.getenv("LLM_TYPE")
            or "ALIYUN"
        ).upper()

        if llm_type == "ALIYUN":
            model_name = os.getenv(
                "CHAT_MODEL_NAME",
                "qwen3-max",
            )

            api_key = os.getenv(
                "ALIYUN_ACCESS_KEY_SECRET"
            )

            if api_key:
                os.environ["DASHSCOPE_API_KEY"] = api_key

            return ChatTongyi(
                model=model_name,
            )

        if llm_type == "OLLAMA":
            model_name = os.getenv(
                "OLLAMA_MODEL_NAME",
                os.getenv(
                    "OLLAMA_CHAT_MODEL_NAME",
                    "qwen3:7b",
                ),
            )

            base_url = os.getenv(
                "OLLAMA_BASE_URL",
                "http://localhost:11434",
            )

            return ChatOllama(
                model=model_name,
                base_url=base_url,
            )

        if llm_type == "OPENAI":
            model_name = os.getenv(
                "OPENAI_MODEL_NAME"
            )

            if not model_name:
                raise ValueError(
                    "未配置 OPENAI_MODEL_NAME"
                )

            return ChatOpenAI(
                model=model_name,
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=(
                    os.getenv("OPENAI_BASE_URL")
                    or None
                ),
            )

        raise ValueError(
            f"不支持的聊天模型类型：{llm_type}"
        )


class EmbedModelFactory(BaseModelFactory):
    """Embedding 模型工厂。"""

    @lru_cache(maxsize=1)
    def generator(self) -> Embeddings:
        embed_type = (
            os.getenv("EMBED_MODEL_TYPE")
            or os.getenv("LLM_TYPE")
            or "ALIYUN"
        ).upper()

        if embed_type == "ALIYUN":
            return DashScopeEmbeddingsWrapper(
                model_name=os.getenv(
                    "ALIYUN_EMBED_MODEL_NAME",
                    "text-embedding-v4",
                ),
                api_key=os.getenv(
                    "ALIYUN_ACCESS_KEY_SECRET"
                ),
            )

        if embed_type == "OLLAMA":
            return OllamaEmbeddings(
                model=os.getenv(
                    "OLLAMA_EMBED_MODEL_NAME",
                    "qwen3-embedding:0.6b",
                ),
                base_url=os.getenv(
                    "OLLAMA_BASE_URL",
                    "http://localhost:11434",
                ),
            )

        if embed_type == "OPENAI":
            model_name = os.getenv(
                "OPENAI_EMBED_MODEL_NAME"
            )

            if not model_name:
                raise ValueError(
                    "未配置 OPENAI_EMBED_MODEL_NAME"
                )

            return OpenAIEmbeddings(
                model=model_name,
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=(
                    os.getenv("OPENAI_BASE_URL")
                    or None
                ),
            )

        if embed_type == "LOCAL":
            return HuggingFaceEmbeddings(
                model_name=os.getenv(
                    "LOCAL_EMBED_MODEL_NAME",
                    "BAAI/bge-small-zh-v1.5",
                ),
                model_kwargs={
                    "device": os.getenv(
                        "LOCAL_EMBED_DEVICE",
                        "cpu",
                    )
                },
                encode_kwargs={
                    "normalize_embeddings": True,
                },
            )

        raise ValueError(
            f"不支持的 Embedding 模型类型：{embed_type}"
        )


class VisionModelFactory(BaseModelFactory):
    """视觉模型工厂。"""

    @lru_cache(maxsize=1)
    def generator(self) -> BaseChatModel:
        vision_type = (
            os.getenv("VISION_MODEL_TYPE")
            or os.getenv("LLM_TYPE")
            or "ALIYUN"
        ).upper()

        if vision_type == "ALIYUN":
            model_name = os.getenv(
                "ALIYUN_VISION_MODEL_NAME",
                "qwen-vl-max",
            )

            api_key = os.getenv(
                "ALIYUN_ACCESS_KEY_SECRET"
            )

            if api_key:
                os.environ["DASHSCOPE_API_KEY"] = api_key

            return ChatTongyi(
                model=model_name,
                streaming=False,
            )

        if vision_type == "OLLAMA":
            model_name = os.getenv(
                "OLLAMA_VISION_MODEL_NAME",
                "qwen2.5vl:7b",
            )

            base_url = os.getenv(
                "OLLAMA_BASE_URL",
                "http://localhost:11434",
            )

            return ChatOllama(
                model=model_name,
                base_url=base_url,
                streaming=False,
            )

        if vision_type == "OPENAI":
            model_name = os.getenv(
                "OPENAI_VISION_MODEL_NAME"
            )

            if not model_name:
                raise ValueError(
                    "未配置 OPENAI_VISION_MODEL_NAME"
                )

            return ChatOpenAI(
                model=model_name,
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=(
                    os.getenv("OPENAI_BASE_URL")
                    or None
                ),
                streaming=False,
            )

        raise ValueError(
            f"不支持的视觉模型类型：{vision_type}"
        )

# 只创建一个工厂实例，保证 generator() 的缓存能够复用。
chat_model_factory = ChatModelFactory()
embed_model_factory = EmbedModelFactory()
vision_model_factory = VisionModelFactory()

chat_model = chat_model_factory.generator()
embed_model = embed_model_factory.generator()
vision_model = vision_model_factory.generator()