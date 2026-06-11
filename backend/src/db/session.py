"""数据库会话管理。"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from src.core.config import get_settings
from src.db.models import Base

from pycore.core.logger import get_logger

logger = get_logger()
settings = get_settings()


def _engine_kwargs(database_url: str, debug: bool) -> dict:
    kwargs: dict = {"echo": debug}
    if ":memory:" in database_url:
        kwargs["connect_args"] = {"check_same_thread": False}
        kwargs["poolclass"] = StaticPool
    return kwargs


engine = create_async_engine(
    settings.database_url,
    **_engine_kwargs(settings.database_url, settings.debug),
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


def _migrate_schema(sync_conn) -> None:
    from sqlalchemy import inspect, text

    inspector = inspect(sync_conn)
    if inspector.has_table("guest_sessions"):
        columns = {col["name"] for col in inspector.get_columns("guest_sessions")}
        if "netease_nickname" not in columns:
            sync_conn.execute(text("ALTER TABLE guest_sessions ADD COLUMN netease_nickname VARCHAR(128)"))
        if "netease_cookies" not in columns:
            sync_conn.execute(text("ALTER TABLE guest_sessions ADD COLUMN netease_cookies JSON"))


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_schema)
    async with async_session_maker() as session:
        from src.db.chord_chart_seed import seed_chord_charts

        await seed_chord_charts(session)
    logger.info("Database initialized")


async def close_db() -> None:
    await engine.dispose()
    logger.info("Database connection closed")
