import asyncio
from config.database import engine, Base
from models.model import User, Document, ChatSession, Message, RetrievalLog # Sabhi models import karna zaroori hai
from config.logger import logger

async def init_models():
    logger.info("🚀 Creating PostgreSQL tables asynchronously...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ All tables created successfully inside PostgreSQL!")

if __name__ == "__main__":
    asyncio.run(init_models())