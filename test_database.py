import asyncio

from app.database.db import engine, init_db


async def main():
    try:
        await init_db()
        print("数据库表创建成功")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())