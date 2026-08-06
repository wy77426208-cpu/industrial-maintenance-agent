from app.core.config import PROMPT_CONFIG
from app.core.logger_handler import logger
from app.core.path_tool import PROJECT_ROOT


def load_prompt(prompt_type: str = "main_prompt") -> str:
    """
    根据 Prompt 类型读取对应的提示词文件。
    """

    if prompt_type not in PROMPT_CONFIG:
        logger.error(
            "【Prompt加载】配置中不存在 Prompt 类型：%s",
            prompt_type,
        )

        raise KeyError(
            f"配置中不存在 Prompt 类型：{prompt_type}"
        )

    relative_path = PROMPT_CONFIG[prompt_type]

    # 将相对路径转换为项目中的绝对路径。
    prompt_path = (PROJECT_ROOT / relative_path).resolve()

    try:
        prompt_text = prompt_path.read_text(
            encoding="utf-8"
        )

        logger.debug(
            "【Prompt加载】加载成功：%s -> %s",
            prompt_type,
            prompt_path,
        )

        return prompt_text

    except Exception:
        # logger.exception() 会把完整 Traceback
        # 一起写入日志，方便排查问题。
        logger.exception(
            "【Prompt加载】读取 Prompt 文件失败：%s",
            prompt_path,
        )

        raise