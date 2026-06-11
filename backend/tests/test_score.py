from fastapi.testclient import TestClient


def _guest_beginner(client: TestClient) -> str:
    res = client.post("/api/v1/guest/session")
    guest_id = res.json()["data"]["guest_id"]
    client.post(
        "/api/v1/guest/onboarding",
        cookies={"guest_id": guest_id},
        json={"skill_level": "beginner", "style_preferences": ["民谣"]},
    )
    return guest_id


def test_score_guitar_success(client: TestClient) -> None:
    guest_id = _guest_beginner(client)
    res = client.get(
        "/api/v1/songs/186016/score",
        params={"instrument": "guitar"},
        cookies={"guest_id": guest_id},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["song_name"] == "晴天"
    assert data["instrument"] == "guitar"
    assert data["skill_level"] == "beginner"
    assert len(data["lines"]) >= 1
    assert data["practice_tips"]


def test_score_ukulele_success(client: TestClient) -> None:
    guest_id = _guest_beginner(client)
    res = client.get(
        "/api/v1/songs/29715551/score",
        params={"instrument": "ukulele"},
        cookies={"guest_id": guest_id},
    )
    assert res.status_code == 200
    assert res.json()["data"]["instrument"] == "ukulele"


def test_score_not_found(client: TestClient) -> None:
    guest_id = _guest_beginner(client)
    res = client.get(
        "/api/v1/songs/999999999/score",
        cookies={"guest_id": guest_id},
    )
    assert res.status_code == 404
    assert res.json()["code"] == 40403


def test_score_cache_hit(client: TestClient) -> None:
    guest_id = _guest_beginner(client)
    first = client.get(
        "/api/v1/songs/186016/score",
        params={"instrument": "guitar"},
        cookies={"guest_id": guest_id},
    )
    second = client.get(
        "/api/v1/songs/186016/score",
        params={"instrument": "guitar"},
        cookies={"guest_id": guest_id},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"] == second.json()["data"]


def test_score_match_by_wrong_song_id_alias(client: TestClient) -> None:
    """错误版权 ID 应回落到正版谱面。"""
    guest_id = _guest_beginner(client)
    res = client.get(
        "/api/v1/songs/3339230677/score",
        params={"instrument": "guitar"},
        cookies={"guest_id": guest_id},
    )
    assert res.status_code == 200
    assert res.json()["data"]["song_name"] == "晴天"


def test_score_yiban_yiban(client: TestClient) -> None:
    guest_id = _guest_beginner(client)
    res = client.get(
        "/api/v1/songs/3333988321/score",
        params={"instrument": "guitar"},
        cookies={"guest_id": guest_id},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["song_name"] == "一半一半"
    assert data["artist_name"] == "Top Barry"
    assert data["capo"] == 2
    assert data["rhythm_pattern"]["label"]
    assert data["lyric_source"] == "netease"
    assert data["vocal_version"] == "male"
    assert data["chord_source"] == "verified:verified"
    assert data["lines"][5]["chord_marks"]
    assert len(data["lines"]) >= 80
    assert data["lines"][0]["section"] == "intro"
    assert data["lines"][0]["start_ms"] == 0
    vocal_starts = [line["start_ms"] for line in data["lines"] if line["section"] != "intro"]
    assert vocal_starts[0] == 14_610
    assert data["intro_duration_ms"] == 14_610
    assert any("一半一半" in line["lyric_line"] for line in data["lines"])


def test_score_beginner_simplifies_chords(client: TestClient) -> None:
    guest_id = _guest_beginner(client)
    res = client.get(
        "/api/v1/songs/478507889/score",
        params={"instrument": "guitar"},
        cookies={"guest_id": guest_id},
    )
    assert res.status_code == 200
    chords: list[str] = []
    for line in res.json()["data"]["lines"]:
        if line.get("chord_marks"):
            chords.extend(mark["chord"] for mark in line["chord_marks"])
        elif line.get("chord"):
            chords.append(line["chord"])
    assert "F" not in chords
    assert "C" in chords
