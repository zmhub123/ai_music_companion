from fastapi.testclient import TestClient


def _create_guest(client: TestClient) -> str:
    res = client.post("/api/v1/guest/session")
    assert res.status_code == 200
    return res.json()["data"]["guest_id"]


def test_playlist_crud_flow(client: TestClient) -> None:
    _create_guest(client)

    created = client.post(
        "/api/v1/playlists",
        json={"name": "周末弹唱", "description": "适合周末练习的歌"},
    )
    assert created.status_code == 200
    body = created.json()
    assert body["code"] == 200
    playlist_id = body["data"]["id"]
    assert body["data"]["song_count"] == 0

    listed = client.get("/api/v1/playlists")
    assert listed.status_code == 200
    items = listed.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["id"] == playlist_id

    updated = client.put(
        f"/api/v1/playlists/{playlist_id}",
        json={"name": "周末弹唱（更新）", "description": "更新描述"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "周末弹唱（更新）"

    added = client.post(
        f"/api/v1/playlists/{playlist_id}/songs",
        json={
            "netease_song_id": 25706282,
            "song_name": "南山南",
            "artist_name": "马頔",
            "cover_url": "https://p1.music.126.net/example.jpg",
        },
    )
    assert added.status_code == 200
    playlist_song_id = added.json()["data"]["id"]

    detail = client.get(f"/api/v1/playlists/{playlist_id}")
    assert detail.status_code == 200
    detail_body = detail.json()["data"]
    assert detail_body["song_count"] == 1
    assert len(detail_body["songs"]) == 1
    assert detail_body["songs"][0]["netease_song_id"] == 25706282

    removed = client.delete(f"/api/v1/playlists/{playlist_id}/songs/{playlist_song_id}")
    assert removed.status_code == 200
    assert removed.json()["data"]["deleted"] is True

    after_remove = client.get(f"/api/v1/playlists/{playlist_id}")
    assert after_remove.json()["data"]["song_count"] == 0

    deleted = client.delete(f"/api/v1/playlists/{playlist_id}")
    assert deleted.status_code == 200
    assert deleted.json()["data"]["deleted"] is True

    empty = client.get("/api/v1/playlists")
    assert empty.json()["data"]["total"] == 0


def test_add_duplicate_song_returns_40001(client: TestClient) -> None:
    _create_guest(client)
    created = client.post("/api/v1/playlists", json={"name": "测试歌单", "description": ""})
    playlist_id = created.json()["data"]["id"]
    song_payload = {
        "netease_song_id": 186016,
        "song_name": "晴天",
        "artist_name": "周杰伦",
        "cover_url": "",
    }

    first = client.post(f"/api/v1/playlists/{playlist_id}/songs", json=song_payload)
    assert first.status_code == 200

    dup = client.post(f"/api/v1/playlists/{playlist_id}/songs", json=song_payload)
    assert dup.status_code == 400
    assert dup.json()["code"] == 40001


def test_guest_isolation(client: TestClient) -> None:
    guest_a = _create_guest(client)
    created = client.post("/api/v1/playlists", json={"name": "A 的歌单", "description": ""})
    playlist_id = created.json()["data"]["id"]

    guest_b_res = client.post("/api/v1/guest/session")
    guest_b = guest_b_res.json()["data"]["guest_id"]
    assert guest_b != guest_a

    forbidden = client.get(
        f"/api/v1/playlists/{playlist_id}",
        cookies={"guest_id": guest_b},
    )
    assert forbidden.status_code == 404
    assert forbidden.json()["code"] == 40401


def test_playlist_requires_guest_cookie(client: TestClient) -> None:
    res = client.get("/api/v1/playlists")
    assert res.status_code == 401
    assert res.json()["code"] == 40101
