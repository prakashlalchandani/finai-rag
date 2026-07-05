import asyncio
from qdrant_client.http import models as qmodels
from config.database import engine, Base
from config.clients import qdrant_client
from config.settings import settings
from models.model import User, Document, ChatSession, Message, RetrievalLog
from config.logger import logger

async def init_postgres():
    logger.info("🚀 Creating PostgreSQL tables asynchronously...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ All tables created successfully inside PostgreSQL!")

async def init_qdrant():
    logger.info("☁️ Checking Qdrant Cloud collections...")
    
    # Fetch all existing collections from your cloud cluster
    response = await qdrant_client.get_collections()
    existing_collections = [col.name for col in response.collections]
    
    if settings.COLLECTION_NAME not in existing_collections:
        logger.info(f"Creating new Qdrant collection: {settings.COLLECTION_NAME}...")
        
        # Create the collection configured for Gemini embeddings
        await qdrant_client.create_collection(
            collection_name=settings.COLLECTION_NAME,
            vectors_config=qmodels.VectorParams(
                size=768,  # Gemini embedding-001 outputs 768 dimensions
                distance=qmodels.Distance.COSINE
            )
        )
        logger.info("✅ Qdrant collection created successfully on the cloud!")
    else:
        logger.info(f"✅ Qdrant collection '{settings.COLLECTION_NAME}' already exists.")

async def main():
    # Run both initializations
    await init_postgres()
    await init_qdrant()

if __name__ == "__main__":
    asyncio.run(main())