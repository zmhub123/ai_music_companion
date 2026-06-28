from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.integrations.music_provider import (
    PlayabilityInfo,
    TrackAudioResult,
    _inspect_track_audio_item,
)


def test_inspect_full_play_url() -> None:
    info = _inspect_track_audio_item(
        {
            "id": 1,
            "code": 200,
            "fee": 0,
            "url": "http://example.com/full.mp3",
        }
    )
    assert info.playable is True
    assert info.trial_preview is False
    assert info.vip_required is False


def test_inspect_vip_trial_url() -> None:
    info = _inspect_track_audio_item(
        {
            "id": 382844,
            "code": 200,
            "fee": 1,
            "url": "http://example.com/trial.mp3",
            "freeTrialInfo": {"start": 0, "end": 30},
        }
    )
    assert info.playable is True
    assert info.trial_preview is True
    assert info.trial_duration_sec == 30
    assert info.vip_required is False


def test_inspect_vip_without_url() -> None:
    info = _inspect_track_audio_item(
        {
            "id": 186016,
            "code": 404,
            "fee": 1,
            "url": None,
        }
    )
    assert info.playable is False
    assert info.trial_preview is False
    assert info.vip_required is True


def test_play_url_vip_trial_returns_metadata(client: TestClient) -> None:
    guest = client.post("/api/v1/guest/session")
    cookies = {"guest_id": guest.json()["data"]["guest_id"]}
    trial = TrackAudioResult(
        url="http://example.com/trial.mp3",
        info=PlayabilityInfo(
            playable=True,
            vip_required=False,
            trial_preview=True,
            trial_duration_sec=30,
        ),
    )
    with patch(
        "src.services.music_service.resolve_track_audio",
        new_callable=AsyncMock,
        return_value=trial,
    ):
        res = client.get("/api/v1/songs/382844/play-url", cookies=cookies)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["url"] == "http://example.com/trial.mp3"
    assert data["vip_trial"] is True
    assert data["trial_duration_sec"] == 30
    assert data["vip_only"] is True
