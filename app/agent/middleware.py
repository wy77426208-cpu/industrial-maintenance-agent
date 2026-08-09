from langchain.agents.middleware import (
    after_agent,
    before_agent,
    before_model,
    wrap_tool_call,
)

from app.core.logger_handler import logger


@before_agent
def log_before_agent(state, runtime):
    """记录一次 Agent 任务开始。"""

    logger.info(
        "【Agent】开始处理请求"
    )


@after_agent
def log_after_agent(state, runtime):
    """记录一次 Agent 任务结束。"""

    logger.info(
        "【Agent】请求处理完成"
    )


@before_model
def log_before_model(state, runtime):
    """记录每次模型调用。"""

    messages = state.get(
        "messages",
        [],
    )

    logger.debug(
        "【Agent】准备调用模型，当前消息数：%d",
        len(messages),
    )


@wrap_tool_call
def monitor_tool(request, handler):
    """记录 Tool 调用及执行结果。"""

    tool_name = request.tool_call["name"]
    tool_args = request.tool_call["args"]

    logger.info(
        "【Agent Tool】调用：%s，参数：%s",
        tool_name,
        tool_args,
    )

    try:
        result = handler(request)

        logger.info(
            "【Agent Tool】执行完成：%s",
            tool_name,
        )

        return result

    except Exception:
        logger.exception(
            "【Agent Tool】执行失败：%s",
            tool_name,
        )

        raise


def get_middleware():
    """获取 MaintAI 默认 Middleware。"""

    return [
        log_before_agent,
        log_after_agent,
        log_before_model,
        monitor_tool,
    ]