from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config.settings import settings

# Database URL format: postgresql+asyncpg://user:password@localhost:5432/dbname
# Make sure to add DATABASE_URL in your .env and config/settings.py
DATABASE_URL = settings.DATABASE_URL 

# 1. Async Engine create karo
engine = create_async_engine(DATABASE_URL, echo=False)

# 2. Async Session maker setup karo
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 3. Base class models ke liye
class Base(DeclarativeBase):
    pass

# 4. Dependency Injection Provider for FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session