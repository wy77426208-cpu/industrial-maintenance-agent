import json
from datetime import datetime
from pathlib import Path

from app.core.logger_handler import logger
from app.core.path_tool import MD5_STORE_FILE


class MD5Store:
    """管理已经进入知识库的文件 MD5。"""

    def __init__(
        self,
        store_path: str | Path = MD5_STORE_FILE,
    ):
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _load(self) -> dict:
        if not self.store_path.exists():
            return {}

        try:
            content = self.store_path.read_text(encoding="utf-8")

            if not content.strip():
                return {}

            return json.loads(content)

        except Exception:
            logger.exception(
                "【MD5记录】读取失败：%s",
                self.store_path,
            )
            return {}

    def contains(self, md5_hex: str) -> bool:
        """判断文件是否已经处理过。"""
        records = self._load()
        return md5_hex in records

    def save(
        self,
        md5_hex: str,
        filename: str,
        source: str,
    ) -> None:
        """保存已入库文件的信息。"""
        records = self._load()

        records[md5_hex] = {
            "filename": filename,
            "source": source,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

        try:
            self.store_path.write_text(
                json.dumps(
                    records,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

        except Exception:
            logger.exception(
                "【MD5记录】保存失败：%s",
                self.store_path,
            )
            raise
