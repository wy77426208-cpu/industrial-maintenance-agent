from pathlib import Path


# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 各功能目录
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"

STORAGE_DIR = PROJECT_ROOT / "storage"
CHROMA_DIR = STORAGE_DIR / "chroma"
UPLOAD_DIR = STORAGE_DIR / "uploads"

MD5_STORE_FILE = STORAGE_DIR / "md5_store.json"
ENV_FILE = PROJECT_ROOT / ".env"

LOG_DIR = PROJECT_ROOT / "logs"

def create_runtime_directories():
    """创建程序运行时需要的目录。"""

    for path in [
        STORAGE_DIR,
        CHROMA_DIR,
        UPLOAD_DIR,
        LOG_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    print("项目根目录：", PROJECT_ROOT)
    print("数据目录：", DATA_DIR)
    print("配置目录：", CONFIG_DIR)
    print("Chroma目录：", CHROMA_DIR)
    print("上传目录：", UPLOAD_DIR)
    print("日志目录：", LOG_DIR)