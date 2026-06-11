from fastapi.testclient import TestClient
from src.integrations.dashscope_client import DashScopeClient, DashScopeError
from src.services import chat_service


def _create_guest(client: TestClient) -> str:
    res = client.post("/api/v1/guest/session")
    assert res.status_code == 200
    return res.json()["data"]["guest_id"]


def test_chat_bare_song_title_triggers_search(client: TestClient) -> None:
    _create_guest(client)
    sent = client.post(
        "/api/v1/chat/messages",
        json={"content": "形容"},
    )
    assert sent.status_code == 200
    assistant = sent.json()["data"]["assistant_message"]
    assert assistant["metadata"]["intent"] == "play_song"
    assert assistant["metadata"]["auto_play"] is True
    recs = assistant["metadata"]["recommendations"]
    assert recs
    assert any("形容" in item["song_name"] for item in recs)
    assert recs[0]["artist_name"] == "沈以诚"


def test_chat_recommend_specific_song_name(client: TestClient) -> None:
    _create_guest(client)
    sent = client.post(
        "/api/v1/chat/messages",
        json={"content": "我想听晴天"},
    )
    assert sent.status_code == 200
    recs = sent.json()["data"]["assistant_message"]["metadata"]["recommendations"]
    assert recs
    assert any("晴天" in item["song_name"] for item in recs)


def test_chat_message_flow(client: TestClient) -> None:
    _create_guest(client)

    empty = client.get("/api/v1/chat/messages")
    assert empty.status_code == 200
    assert empty.json()["data"]["total"] == 0

    sent = client.post(
        "/api/v1/chat/messages",
        json={"content": "推荐几首适合弹唱的民谣"},
    )
    assert sent.status_code == 200
    body = sent.json()["data"]
    assert body["user_message"]["content"] == "推荐几首适合弹唱的民谣"
    assistant = body["assistant_message"]
    assert assistant["role"] == "assistant"
    assert assistant["metadata"]["intent"] == "recommend_music"
    recs = assistant["metadata"]["recommendations"]
    assert len(recs) >= 1
    assert len(recs) <= 10

    listed = client.get("/api/v1/chat/messages")
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 2


def test_chat_only_intent(client: TestClient) -> None:
    _create_guest(client)
    sent = client.post(
        "/api/v1/chat/messages",
        json={"content": "今天加班好累"},
    )
    assert sent.status_code == 200
    assistant = sent.json()["data"]["assistant_message"]
    assert assistant["metadata"]["intent"] == "chat_only"
    assert assistant["metadata"].get("recommendations") is None


def test_chat_reset_clears_history(client: TestClient) -> None:
    _create_guest(client)
    client.post("/api/v1/chat/messages", json={"content": "想听安静的歌"})
    reset = client.post("/api/v1/chat/reset")
    assert reset.status_code == 200
    data = reset.json()["data"]
    assert data["reset"] is True
    assert data["cleared_message_count"] == 2

    listed = client.get("/api/v1/chat/messages")
    assert listed.json()["data"]["total"] == 0


class _FailingDashScopeClient:
    @property
    def use_mock(self) -> bool:
        return False

    async def generate(self, *_args: object, **_kwargs: object) -> str:
        raise DashScopeError("LLM unavailable")

    async def chat_completion(self, *_args: object, **_kwargs: object) -> str:
        raise DashScopeError("LLM unavailable")


async def test_send_message_llm_failure_returns_50001() -> None:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from src.db.models import GuestSession
    from src.db.session import engine

    session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        from src.db.models import Base

        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as db:
        guest = GuestSession()
        db.add(guest)
        await db.commit()
        await db.refresh(guest)

        try:
            await chat_service.send_message(
                db,
                guest,
                "推荐几首歌",
                client=_FailingDashScopeClient(),  # type: ignore[arg-type]
            )
            raise AssertionError("expected AppApiError")
        except Exception as exc:
            from src.api.errors import AppApiError

            assert isinstance(exc, AppApiError)
            assert exc.code == 50001
            assert exc.http_status == 500


def test_dashscope_mock_mode_uses_placeholder_key() -> None:
    client = DashScopeClient(force_mock=True)
    assert client.use_mock is True


def test_direct_song_request_distinguishes_mood_from_title() -> None:
    from src.integrations.music_provider import is_direct_song_request

    assert is_direct_song_request("形容") is True
    assert is_direct_song_request("我想听晴天") is True
    assert is_direct_song_request("今天很开心，想听欢快的歌") is False
    assert is_direct_song_request("想听安静的歌") is False


def test_mood_keyword_extraction_for_cheerful_request() -> None:
    from src.db.models import GuestSession

    guest = GuestSession()
    query = chat_service._extract_mood_style_query("今天很开心，想听欢快的歌")
    assert query == "欢快 流行"
    keywords = chat_service._extract_keywords_heuristic("今天很开心，想听欢快的歌", guest)
    assert keywords == "欢快 流行"


def test_mood_title_bias_penalizes_sad_song_names() -> None:
    assert chat_service._mood_title_bias("今天晚上的夜还很长", "今天很开心，想听欢快的歌") < 0
    assert chat_service._mood_title_bias("阳光彩虹小白马", "今天很开心，想听欢快的歌") > 0


def test_chat_cheerful_mood_uses_mood_search_not_today(client: TestClient) -> None:
    _create_guest(client)
    sent = client.post(
        "/api/v1/chat/messages",
        json={"content": "今天很开心，想听欢快的歌"},
    )
    assert sent.status_code == 200
    assistant = sent.json()["data"]["assistant_message"]
    assert assistant["metadata"]["intent"] == "recommend_music"
    recs = assistant["metadata"]["recommendations"]
    assert recs
    sad_hits = sum(
        1
        for item in recs
        if any(word in item["song_name"] for word in ("夜", "不想", "麻烦", "难过", "伤心"))
    )
    assert sad_hits <= len(recs) // 2
