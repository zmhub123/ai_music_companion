from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _guest_cookies(client: TestClient) -> dict[str, str]:
    res = client.post("/api/v1/guest/session")
    assert res.status_code == 200
    guest_id = res.json()["data"]["guest_id"]
    return {"guest_id": guest_id}


def test_search_songs(client: TestClient) -> None:
    res = client.get("/api/v1/songs/search", params={"q": "民谣"})
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 200
    assert body["data"]["total"] >= 1


def test_search_qingtian_returns_official_original(client: TestClient) -> None:
    res = client.get("/api/v1/songs/search", params={"q": "晴天"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert items
    top = items[0]
    assert top["netease_song_id"] == 186016
    assert top["song_name"] == "晴天"
    assert top["artist_name"] == "周杰伦"
    assert top["is_original"] is True
    assert top["vip_only"] is True
    assert top["playable"] is False
    cover_markers = ("翻唱", "女声版", "原唱", "钢琴版")
    for item in items:
        assert not any(marker in item["song_name"] for marker in cover_markers)


def test_get_song_detail(client: TestClient) -> None:
    res = client.get("/api/v1/songs/186016")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["song_name"] == "晴天"
    assert data["album_name"] == "叶惠美"
    assert data["netease_url"] == "https://music.163.com/song?id=186016"


def test_get_song_not_found(client: TestClient) -> None:
    res = client.get("/api/v1/songs/999999999")
    assert res.status_code == 404
    assert res.json()["code"] == 40402


def test_play_url_legacy_id_alias(client: TestClient) -> None:
    with patch(
        "src.services.music_service.resolve_direct_play_url",
        new_callable=AsyncMock,
        return_value="http://example.com/qingtian.mp3",
    ):
        res = client.get("/api/v1/songs/186016/play-url", cookies=_guest_cookies(client))
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["url"]
    assert data["expires_in"] == 1200


def test_play_url_returns_stream_or_direct(client: TestClient) -> None:
    with patch(
        "src.services.music_service.resolve_direct_play_url",
        new_callable=AsyncMock,
        return_value="http://example.com/qingtian.mp3",
    ):
        res = client.get("/api/v1/songs/186016/play-url", cookies=_guest_cookies(client))
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["url"]
    assert data["expires_in"] == 1200
    assert data["fallback_url"] == "https://music.163.com/song?id=186016"


def test_play_url_wrong_metadata_id_still_plays(client: TestClient) -> None:
    with patch(
        "src.services.music_service.resolve_direct_play_url",
        new_callable=AsyncMock,
        return_value="http://example.com/qingtian.mp3",
    ):
        res = client.get("/api/v1/songs/3339230677/play-url", cookies=_guest_cookies(client))
    assert res.status_code == 200
    assert res.json()["data"]["url"]


def test_stream_returns_audio(client: TestClient) -> None:
    async def _fake_chunks():
        yield b"\x00" * 128

    class _FakeStreamCtx:
        def __init__(self, response: object) -> None:
            self._response = response

        async def __aenter__(self) -> object:
            return self._response

        async def __aexit__(self, *_args: object) -> None:
            return None

    mock_response = AsyncMock()
    mock_response.raise_for_status = lambda: None
    mock_response.aiter_bytes = _fake_chunks

    mock_http_client = AsyncMock()
    mock_http_client.stream = lambda *_args, **_kwargs: _FakeStreamCtx(mock_response)

    with (
        patch(
            "src.api.routes.song.music_service.get_stream_source",
            new_callable=AsyncMock,
            return_value="http://example.com/qingtian.mp3",
        ),
        patch("src.api.routes.song.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client_cls.return_value.__aenter__.return_value = mock_http_client
        with client.stream("GET", "/api/v1/songs/186016/stream") as res:
            assert res.status_code == 200
            assert res.headers.get("content-type", "").startswith("audio/mpeg")
            first_chunk = next(res.iter_bytes())
            assert len(first_chunk) > 100


def test_stream_not_found(client: TestClient) -> None:
    res = client.get("/api/v1/songs/999999999/stream")
    assert res.status_code == 404
    assert res.json()["code"] == 40402


def test_play_url_vip_returns_vip_required(client: TestClient) -> None:
    with (
        patch(
            "src.services.music_service.resolve_direct_play_url",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "src.services.music_service.check_playability",
            new_callable=AsyncMock,
            return_value=__import__(
                "src.integrations.music_provider", fromlist=["PlayabilityInfo"]
            ).PlayabilityInfo(playable=False, vip_required=True),
        ),
        patch(
            "src.services.music_service.get_song_detail",
            new_callable=AsyncMock,
            return_value=object(),
        ),
    ):
        res = client.get("/api/v1/songs/186016/play-url", cookies=_guest_cookies(client))
    assert res.status_code == 500
    body = res.json()
    assert body["code"] == 50004
    assert body["data"]["vip_required"] is True
    assert body["data"]["need_netease_login"] is True


def test_play_url_unavailable_returns_50004(client: TestClient) -> None:
    with (
        patch(
            "src.services.music_service.resolve_direct_play_url",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "src.services.music_service.get_song_detail",
            new_callable=AsyncMock,
            return_value=object(),
        ),
    ):
        res = client.get("/api/v1/songs/123456/play-url", cookies=_guest_cookies(client))
    assert res.status_code == 500
    body = res.json()
    assert body["code"] == 50004
    assert body["data"]["fallback_url"] == "https://music.163.com/song?id=123456"
