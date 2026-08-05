from app.core.path_tool import CONFIG_DIR
from app.core.config_handler import load_config


CHROMA_CONFIG = load_config(
    CONFIG_DIR / "chroma.yaml"
)

RAG_CONFIG = load_config(
    CONFIG_DIR / "rag.yaml"
)

PROMPT_CONFIG = load_config(
    CONFIG_DIR / "prompt.yaml"
)

AGENT_CONFIG = load_config(
    CONFIG_DIR / "agent.yaml"
)


if __name__ == "__main__":
    print("RAG 配置：", RAG_CONFIG["chat_model_name"])
