import asyncio
import hashlib
from pathlib import Path

import aiofiles
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPDFLoader,
    UnstructuredPowerPointLoader,
)
from langchain_core.documents import Document

from app.core.logger_handler import logger
from app.core.path_tool import PROJECT_ROOT


def resolve_file_path(file_path: str | Path) -> Path:
    """
    将文件或目录路径解析为绝对路径。
    :param file_path: 文件或目录路径
    :return: 规范化后的绝对 Path 对象
    """
    path = Path(file_path)

    if path.is_absolute():
        return path.resolve()

    return (PROJECT_ROOT / path).resolve()


async def get_file_md5_hex(file_path: str | Path) -> str:
    """
    异步计算文件 MD5。
    :param file_path: 文件路径
    :return: MD5 十六进制字符串；失败时返回空字符串
    """
    abs_file_path = resolve_file_path(file_path)

    # 路径不存在
    if not abs_file_path.exists():
        logger.error("【MD5计算】文件不存在：%s", abs_file_path)
        return ""

    # 路径存在，但不是普通文件
    if not abs_file_path.is_file():
        logger.error("【MD5计算】路径不是文件：%s", abs_file_path)
        return ""

    md5_object = hashlib.md5()

    # 每次读取 1 MB。
    chunk_size = 1024 * 1024

    try:
        async with aiofiles.open(abs_file_path, "rb") as file:
            while chunk := await file.read(chunk_size):
                md5_object.update(chunk)

        md5_hex = md5_object.hexdigest()

        logger.debug(
            "【MD5计算】文件：%s，MD5：%s",
            abs_file_path.name,
            md5_hex,
        )

        return md5_hex

    except Exception:
        logger.exception(
            "【MD5计算】读取文件失败：%s",
            abs_file_path,
        )
        return ""


def get_file_md5_hex_sync(file_path: str | Path) -> str:
    """
    同步计算文件 MD5。
    :param file_path: 文件路径
    :return: MD5 十六进制字符串；失败时返回空字符串
    """
    abs_file_path = resolve_file_path(file_path)

    if not abs_file_path.exists():
        logger.error("【MD5计算】文件不存在：%s", abs_file_path)
        return ""

    if not abs_file_path.is_file():
        logger.error("【MD5计算】路径不是文件：%s", abs_file_path)
        return ""

    md5_object = hashlib.md5()
    chunk_size = 1024 * 1024

    try:
        with abs_file_path.open("rb") as file:
            while chunk := file.read(chunk_size):
                md5_object.update(chunk)

        return md5_object.hexdigest()

    except Exception:
        logger.exception(
            "【MD5计算】读取文件失败：%s",
            abs_file_path,
        )
        return ""


async def listdir_allowed_type(
    directory: str | Path,
    allowed_types: tuple[str, ...],
) -> tuple[Path, ...]:
    """
    异步获取目录下所有允许类型的文件。
    :param directory: 需要扫描的目录
    :param allowed_types: 允许的文件后缀，例如 (".pdf", ".txt")
    :return: 符合条件的文件绝对路径元组
    """
    abs_directory = resolve_file_path(directory)

    if not abs_directory.exists():
        logger.error("【文件扫描】目录不存在：%s", abs_directory)
        return ()

    if not abs_directory.is_dir():
        logger.error("【文件扫描】路径不是目录：%s", abs_directory)
        return ()

    # 全部统一转小写，避免 .PDF、.Pdf 等情况漏掉。
    allowed_types = tuple(
        suffix.lower() if suffix.startswith(".") else f".{suffix.lower()}"
        for suffix in allowed_types
    )

    try:
        files = await asyncio.to_thread(lambda: list(abs_directory.iterdir()))

        result = tuple(
            file
            for file in files
            if file.is_file() and file.suffix.lower() in allowed_types
        )

        logger.debug(
            "【文件扫描】目录 %s 共发现 %d 个允许类型文件",
            abs_directory,
            len(result),
        )

        return result

    except Exception:
        logger.exception(
            "【文件扫描】扫描目录失败：%s",
            abs_directory,
        )
        return ()


async def pdf_loader(
    file_path: str | Path,
    password: str | None = None,
) -> list[Document]:
    """
    异步加载 PDF 文件。
    :param file_path: PDF 文件路径
    :param password: PDF 密码，没有则为 None
    :return: LangChain Document 列表
    """
    abs_file_path = resolve_file_path(file_path)

    if not abs_file_path.is_file():
        logger.error("【PDF加载】文件不存在：%s", abs_file_path)
        return []

    try:
        # 加密 PDF 优先使用 PyPDFLoader。
        if password:
            loader = PyPDFLoader(
                str(abs_file_path),
                password=password,
            )

            docs = await asyncio.to_thread(loader.load)

            logger.info(
                "【PDF加载】成功加载加密 PDF：%s，共 %d 个 Document",
                abs_file_path.name,
                len(docs),
            )

            return docs

        # 第一种方式：UnstructuredPDFLoader

        try:
            loader = UnstructuredPDFLoader(str(abs_file_path))

            docs = await asyncio.to_thread(loader.load)

            # 有 Document，并且至少一个 Document 有有效文本，
            # 才认为本次加载成功。
            if docs and any(doc.page_content.strip() for doc in docs):
                logger.info(
                    "【PDF加载】UnstructuredPDFLoader 加载成功：%s",
                    abs_file_path.name,
                )
                return docs

        except Exception as exc:
            logger.warning(
                "【PDF加载】UnstructuredPDFLoader 加载失败，"
                "准备退回 PyPDFLoader：%s",
                exc,
            )

        # 第二种方式：PyPDFLoader 兜底
        loader = PyPDFLoader(str(abs_file_path))

        docs = await asyncio.to_thread(loader.load)

        logger.info(
            "【PDF加载】PyPDFLoader 加载成功：%s，共 %d 个 Document",
            abs_file_path.name,
            len(docs),
        )

        return docs

    except Exception:
        logger.exception(
            "【PDF加载】PDF 加载失败：%s",
            abs_file_path,
        )
        return []


async def txt_loader(
    file_path: str | Path,
) -> list[Document]:
    """
    异步加载 TXT 文件。
    :param file_path: TXT 文件路径
    :return: LangChain Document 列表
    """
    abs_file_path = resolve_file_path(file_path)

    if not abs_file_path.is_file():
        logger.error("【TXT加载】文件不存在：%s", abs_file_path)
        return []

    encodings = ("utf-8", "gbk")

    for encoding in encodings:
        try:
            loader = TextLoader(
                str(abs_file_path),
                encoding=encoding,
            )

            docs = await asyncio.to_thread(loader.load)

            logger.info(
                "【TXT加载】加载成功：%s，编码：%s",
                abs_file_path.name,
                encoding,
            )

            return docs

        except UnicodeDecodeError:
            logger.warning(
                "【TXT加载】编码 %s 无法解析文件：%s",
                encoding,
                abs_file_path.name,
            )

        except Exception:
            logger.exception(
                "【TXT加载】加载文件失败：%s",
                abs_file_path,
            )
            return []

    logger.error(
        "【TXT加载】所有编码均加载失败：%s",
        abs_file_path,
    )

    return []


async def markdown_loader(
    file_path: str | Path,
) -> list[Document]:
    """
    异步加载 Markdown 文件。
    :param file_path: .md 文件路径
    :return: LangChain Document 列表
    """
    abs_file_path = resolve_file_path(file_path)

    if not abs_file_path.is_file():
        logger.error(
            "【Markdown加载】文件不存在：%s",
            abs_file_path,
        )
        return []

    try:
        loader = UnstructuredMarkdownLoader(
            str(abs_file_path),
            mode="single",
        )

        docs = await asyncio.to_thread(loader.load)

        logger.info(
            "【Markdown加载】加载成功：%s",
            abs_file_path.name,
        )

        return docs

    except Exception:
        logger.exception(
            "【Markdown加载】加载失败：%s",
            abs_file_path,
        )
        return []


async def word_loader(
    file_path: str | Path,
) -> list[Document]:
    """
    异步加载 Word DOCX 文件。
    :param file_path: .docx 文件路径
    :return: LangChain Document 列表
    """
    abs_file_path = resolve_file_path(file_path)

    if not abs_file_path.is_file():
        logger.error(
            "【Word加载】文件不存在：%s",
            abs_file_path,
        )
        return []

    try:
        loader = Docx2txtLoader(str(abs_file_path))

        docs = await asyncio.to_thread(loader.load)

        logger.info(
            "【Word加载】加载成功：%s",
            abs_file_path.name,
        )

        return docs

    except Exception:
        logger.exception(
            "【Word加载】加载失败：%s",
            abs_file_path,
        )
        return []


async def ppt_loader(
    file_path: str | Path,
) -> list[Document]:
    """
    异步加载 PPT/PPTX 文件。
    :param file_path: PowerPoint 文件路径
    :return: LangChain Document 列表
    """
    abs_file_path = resolve_file_path(file_path)

    if not abs_file_path.is_file():
        logger.error(
            "【PPT加载】文件不存在：%s",
            abs_file_path,
        )
        return []

    try:
        loader = UnstructuredPowerPointLoader(
            str(abs_file_path),
            mode="single",
        )

        docs = await asyncio.to_thread(loader.load)

        logger.info(
            "【PPT加载】加载成功：%s",
            abs_file_path.name,
        )

        return docs

    except Exception:
        logger.exception(
            "【PPT加载】加载失败：%s",
            abs_file_path,
        )
        return []


def pdf_loader_sync(
    file_path: str | Path,
    password: str | None = None,
) -> list[Document]:
    """
    同步加载 PDF。
    用于普通同步程序或线程池环境。
    """
    abs_file_path = resolve_file_path(file_path)

    if not abs_file_path.is_file():
        logger.error("【PDF加载】文件不存在：%s", abs_file_path)
        return []

    try:
        if password:
            return PyPDFLoader(
                str(abs_file_path),
                password=password,
            ).load()

        try:
            docs = UnstructuredPDFLoader(str(abs_file_path)).load()

            if docs and any(doc.page_content.strip() for doc in docs):
                return docs

        except Exception as exc:
            logger.warning(
                "【PDF加载】UnstructuredPDFLoader 失败，" "退回 PyPDFLoader：%s",
                exc,
            )

        return PyPDFLoader(str(abs_file_path)).load()

    except Exception:
        logger.exception(
            "【PDF加载】加载失败：%s",
            abs_file_path,
        )
        return []


def txt_loader_sync(
    file_path: str | Path,
) -> list[Document]:
    """
    同步加载 TXT 文件。
    """
    abs_file_path = resolve_file_path(file_path)

    for encoding in ("utf-8", "gbk"):
        try:
            return TextLoader(
                str(abs_file_path),
                encoding=encoding,
            ).load()

        except UnicodeDecodeError:
            continue

        except Exception:
            logger.exception(
                "【TXT加载】加载失败：%s",
                abs_file_path,
            )
            return []

    return []


def markdown_loader_sync(
    file_path: str | Path,
) -> list[Document]:
    """
    同步加载 Markdown 文件。
    """
    abs_file_path = resolve_file_path(file_path)

    try:
        return UnstructuredMarkdownLoader(
            str(abs_file_path),
            mode="single",
        ).load()

    except Exception:
        logger.exception(
            "【Markdown加载】加载失败：%s",
            abs_file_path,
        )
        return []


def word_loader_sync(
    file_path: str | Path,
) -> list[Document]:
    """
    同步加载 Word DOCX 文件。
    """
    abs_file_path = resolve_file_path(file_path)

    try:
        return Docx2txtLoader(str(abs_file_path)).load()

    except Exception:
        logger.exception(
            "【Word加载】加载失败：%s",
            abs_file_path,
        )
        return []


def ppt_loader_sync(
    file_path: str | Path,
) -> list[Document]:
    """
    同步加载 PPT/PPTX 文件。
    """
    abs_file_path = resolve_file_path(file_path)

    try:
        return UnstructuredPowerPointLoader(
            str(abs_file_path),
            mode="single",
        ).load()

    except Exception:
        logger.exception(
            "【PPT加载】加载失败：%s",
            abs_file_path,
        )
        return []
