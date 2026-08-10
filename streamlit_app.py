import streamlit as st

from app.agent.agent import MaintAIAgent
from app.services.knowledge_service import KnowledgeService


# 页面基础配置
st.set_page_config(
    page_title="MaintAI",
    page_icon="🛠️",
    layout="centered",
)

st.title("🛠️ MaintAI")
st.caption("工业设备智能运维助手")


# ==================== 初始化服务 ====================

if "agent" not in st.session_state:
    st.session_state.agent = MaintAIAgent()

if "knowledge_service" not in st.session_state:
    st.session_state.knowledge_service = (
        KnowledgeService()
    )

if "messages" not in st.session_state:
    st.session_state.messages = []


# ==================== 侧边栏 ====================

with st.sidebar:
    st.header("MaintAI")

    st.write(
        "支持工业设备知识库查询、"
        "故障资料检索和维护问题咨询。"
    )

    st.divider()

    # ---------- 知识库上传 ----------

    st.subheader("📚 知识库")

    uploaded_files = st.file_uploader(
        "上传设备资料",
        type=[
            "pdf",
            "txt",
            "md",
            "docx",
            "ppt",
            "pptx",
        ],
        accept_multiple_files=True,
    )

    if st.button(
        "写入知识库",
        use_container_width=True,
        disabled=not uploaded_files,
    ):
        for uploaded_file in uploaded_files:
            with st.spinner(
                f"正在处理 {uploaded_file.name}..."
            ):
                try:
                    result = (
                        st.session_state
                        .knowledge_service
                        .upload_file_sync(
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                        )
                    )

                    if (
                        result["status"]
                        == "duplicate"
                    ):
                        st.warning(
                            f"{uploaded_file.name} "
                            "已存在于知识库中"
                        )

                    else:
                        st.success(
                            f"{result['filename']} "
                            f"写入成功，共 "
                            f"{result['chunk_count']} "
                            "个切片"
                        )

                except Exception as exc:
                    st.error(
                        f"{uploaded_file.name} "
                        f"处理失败：{exc}"
                    )

    st.divider()

    # ---------- 对话管理 ----------

    st.subheader("💬 对话")

    if st.button(
        "清空对话",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()


# ==================== 显示历史消息 ====================

for message in st.session_state.messages:
    with st.chat_message(
        message["role"]
    ):
        st.markdown(
            message["content"]
        )


# ==================== 用户输入 ====================

prompt = st.chat_input(
    "请输入设备问题..."
)


# ==================== Agent 回答 ====================

if prompt:
    # 当前问题加入之前，先复制历史消息
    history = (
        st.session_state.messages.copy()
    )

    # 保存当前用户消息
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    # 显示当前用户消息
    with st.chat_message("user"):
        st.markdown(prompt)

    response_chunks = []

    # 显示 AI 回答
    with st.chat_message("assistant"):
        with st.spinner(
            "MaintAI 正在分析..."
        ):

            def response_stream():
                """接收 Agent 流式结果并同步保存。"""

                for chunk in (
                    st.session_state
                    .agent
                    .stream(
                        prompt,
                        history=history,
                    )
                ):
                    response_chunks.append(
                        chunk
                    )

                    yield chunk

            st.write_stream(
                response_stream()
            )

    # 合并完整回答
    response = "".join(
        response_chunks
    ).strip()

    # 保存 AI 回答
    if response:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response,
            }
        )