from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.routers.chat import chat_router
from app.routers.knowledge import knowledge_router


app = FastAPI(
    title="MaintAI API",
    description="工业设备智能运维助手后端接口",
    version="0.1.0",
)

# 注册聊天子路由
app.include_router(chat_router)
app.include_router(knowledge_router)


@app.get("/health")
async def health_check():
    """检查后端服务是否正常运行。"""

    return {
        "status": "ok",
        "service": "MaintAI API",
    }


@app.get("/health/database")
async def database_health(
    db: AsyncSession = Depends(get_db),
):
    """检查数据库连接是否正常。"""

    result = await db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": result.scalar_one(),
    }