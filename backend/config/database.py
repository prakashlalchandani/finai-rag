from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config.settings import settings

DATABASE_URL = settings.DATABASE_URL 

# Async Engine create
engine = create_async_engine(DATABASE_URL, echo=False)

# Async Session maker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class models
class Base(DeclarativeBase):
    pass

# Dependency Injection Provider for FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session