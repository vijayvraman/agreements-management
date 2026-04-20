from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from agreements.config import settings
from agreements.models.agreement import Base

engine = create_async_engine(settings.database_url, echo=False)

AsyncSessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
