"""ORM 业务模型，对齐 PRD 数据契约。"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class GuestSession(Base):
    __tablename__ = "guest_sessions"

    guest_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    skill_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    style_preferences: Mapped[list[str]] = mapped_column(JSON, nullable=False, insert_default=list)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    netease_nickname: Mapped[str | None] = mapped_column(String(128), nullable=True)
    netease_cookies: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    guest_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("guest_sessions.guest_id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    guest_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("guest_sessions.guest_id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PlaylistSong(Base):
    __tablename__ = "playlist_songs"
    __table_args__ = (UniqueConstraint("playlist_id", "netease_song_id", name="uq_playlist_song"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    playlist_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    netease_song_id: Mapped[int] = mapped_column(Integer, nullable=False)
    song_name: Mapped[str] = mapped_column(String(255), nullable=False)
    artist_name: Mapped[str] = mapped_column(String(255), nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ChordCache(Base):
    __tablename__ = "chord_cache"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    netease_song_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    song_name: Mapped[str] = mapped_column(String(255), nullable=False)
    artist_name: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(String(8), nullable=False, default="C")
    chords: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, insert_default=list)
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="mock")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ChordChart(Base):
    __tablename__ = "chord_charts"
    __table_args__ = (
        UniqueConstraint(
            "netease_song_id", "vocal_version", name="uq_chord_chart_variant"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    netease_song_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    vocal_version: Mapped[str] = mapped_column(String(16), nullable=False, default="male")
    song_name: Mapped[str] = mapped_column(String(255), nullable=False)
    artist_name: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(String(8), nullable=False, default="C")
    capo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chordpro_text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="verified")
    rhythm_style: Mapped[str] = mapped_column(String(32), nullable=False, default="default")
    intro_duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ug_tab_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AiChordJob(Base):
    """AI 扒谱任务占位：Demucs 异步分析队列（MVP 仅记录状态）。"""

    __tablename__ = "ai_chord_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    netease_song_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    vocal_version: Mapped[str] = mapped_column(String(16), nullable=False, default="male")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ScoreGenerationJob(Base):
    """异步谱面生成任务（音频分析 + LRC 对齐）。"""

    __tablename__ = "score_generation_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    guest_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("guest_sessions.guest_id", ondelete="CASCADE"), nullable=False, index=True
    )
    netease_song_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    instrument: Mapped[str] = mapped_column(String(16), nullable=False, default="guitar")
    vocal_version: Mapped[str] = mapped_column(String(16), nullable=False, default="male")
    skill_level: Mapped[str] = mapped_column(String(32), nullable=False, default="beginner")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    error_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ScoreCache(Base):
    __tablename__ = "score_cache"
    __table_args__ = (
        UniqueConstraint(
            "netease_song_id", "instrument", "skill_level", name="uq_score_cache_variant"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    netease_song_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    instrument: Mapped[str] = mapped_column(String(16), nullable=False)
    skill_level: Mapped[str] = mapped_column(String(32), nullable=False)
    rendered_score: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
