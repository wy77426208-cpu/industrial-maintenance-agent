import logging
from datetime import datetime

from app.core.path_tool import LOG_DIR, create_runtime_directories


def get_logger(
    name: str = "agent",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
) -> logging.Logger:

    create_runtime_directories()

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s "
        "- %(filename)s:%(lineno)d - %(message)s"
    )

    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    # 文件日志
    log_file = LOG_DIR / f"{name}_{datetime.now():%Y%m%d}.log"

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = get_logger()


if __name__ == "__main__":
    logger.debug("这是调试日志")
    logger.info("这是信息日志")
    logger.warning("这是警告日志")
    logger.error("这是错误日志")
    logger.critical("这是严重错误日志")
