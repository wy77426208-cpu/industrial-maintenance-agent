from collections.abc import Iterator

from langchain.agents import create_agent

from app.agent.tools import (
    get_current_time,
    search_knowledge,
)
from app.agent.middleware import get_middleware
from app.model.factory import chat_model
from app.utils.prompt_loader import load_prompt
from langchain_core.messages import AIMessage


class MaintAIAgent:
    """MaintAI 智能运维 Agent。"""

    def __init__(
        self,
        model=None,
        tools=None,
        middleware=None,
    ):
        self.model = (
            model
            if model is not None
            else chat_model
        )

        self.tools = (
            tools
            if tools is not None
            else [
                search_knowledge,
                get_current_time,
            ]
        )

        self.middleware = (
            middleware
            if middleware is not None
            else get_middleware()
)

        self.system_prompt = load_prompt(
            "main_prompt"
        )

        self.agent = self._create_agent()

    def _create_agent(self):
        """创建带工具调用能力的 Agent。"""

        return create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            middleware=self.middleware,
        )

    @staticmethod
    def _build_input(query: str) -> dict:
        """将用户问题转换为 Agent 消息格式。"""

        return {
            "messages": [
                {
                    "role": "user",
                    "content": query,
                }
            ]
        }

    def invoke(
        self,
        query: str,
    ) -> str:
        """一次性执行 Agent 并返回最终回答。"""

        result = self.agent.invoke(
            self._build_input(query)
        )

        return result["messages"][-1].content

    def stream(
        self,
        query: str,
    ) -> Iterator[str]:
        """流式执行 Agent。"""

        for chunk in self.agent.stream(
            self._build_input(query),
            stream_mode="values",
        ):
            latest_message = chunk["messages"][-1]

            if isinstance(latest_message, AIMessage) and latest_message.content:
                yield (
                    str(latest_message.content).strip()
                    + "\n"
                )


if __name__ == "__main__":
    agent = MaintAIAgent()

    for chunk in agent.stream(
        "这个PDF是用来做什么的？"
    ):
        print(
            chunk,
            end="",
            flush=True,
        )