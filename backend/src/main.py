"""音伴后端入口。"""

from pycore.api import APIConfig, APIServer
from pycore.core import Logger, LoggerConfig, LogLevel, get_logger
from src.api.errors import register_exception_handlers
from src.api.routes.chat import router as chat_router
from src.api.routes.guest import router as guest_router
from src.api.routes.health import router as health_router
from src.api.routes.playlist import router as playlist_router
from src.api.routes.netease import router as netease_router
from src.api.routes.song import router as song_router
from src.core.config import settings
from src.db.session import close_db, init_db

Logger.configure(
    LoggerConfig(
        level=LogLevel.DEBUG if settings.debug else LogLevel.INFO,
        app_name="ai-music-companion",
        json_format=False,
    )
)
logger = get_logger()

server = APIServer(
    APIConfig(
        title="音伴 API",
        description="音伴 AI 音乐陪伴助手后端 API",
        version="0.1.0",
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
        cors_enabled=True,
        cors_origins=settings.cors_origins,
    )
)

server.on_startup(init_db)
server.on_shutdown(close_db)

app = server.app

app.router.routes = [
    route for route in app.router.routes if getattr(route, "path", None) != "/health"
]
app.include_router(health_router)
app.include_router(guest_router)
app.include_router(playlist_router)
app.include_router(chat_router)
app.include_router(song_router)
app.include_router(netease_router)
register_exception_handlers(app)

logger.info("音伴 API configured", host=settings.host, port=settings.port)
