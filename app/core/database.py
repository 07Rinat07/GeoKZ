from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

if settings.environment == "test":
    # pytest-asyncio может создавать отдельный event loop для разных тестов.
    # asyncpg-соединение из обычного пула привязано к loop, в котором оно создано,
    # поэтому в integration tests используем новые соединения вместо межтестового reuse.
    engine = create_async_engine(
        settings.database_url,
        echo=settings.sql_echo,
        pool_pre_ping=True,
        poolclass=NullPool,
    )
else:
    engine = create_async_engine(
        settings.database_url,
        echo=settings.sql_echo,
        pool_pre_ping=True,
    )

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: одна транзакционная сессия на HTTP-запрос."""

    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
