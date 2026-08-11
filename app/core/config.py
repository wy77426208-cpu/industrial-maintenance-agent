from app.core.config_handler import load_config
from app.core.path_tool import CONFIG_DIR

CHROMA_CONFIG = load_config(CONFIG_DIR / "chroma.yaml")

PROMPT_CONFIG = load_config(CONFIG_DIR / "prompt.yaml")

AGENT_CONFIG = load_config(CONFIG_DIR / "agent.yaml")
