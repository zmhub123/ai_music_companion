from fastapi.testclient import TestClient


def test_guest_session_flow(client: TestClient) -> None:
    res = client.post("/api/v1/guest/session")
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 200
    guest_id = body["data"]["guest_id"]
    assert guest_id
    assert body["data"]["onboarding_completed"] is False

    cookie = res.cookies.get("guest_id")
    assert cookie == guest_id

    me = client.get("/api/v1/guest/me", cookies={"guest_id": guest_id})
    assert me.status_code == 200
    assert me.json()["data"]["guest_id"] == guest_id

    onboard = client.post(
        "/api/v1/guest/onboarding",
        cookies={"guest_id": guest_id},
        json={"skill_level": "beginner", "style_preferences": ["民谣", "流行"]},
    )
    assert onboard.status_code == 200
    assert onboard.json()["data"]["onboarding_completed"] is True

    prefs = client.put(
        "/api/v1/guest/preferences",
        cookies={"guest_id": guest_id},
        json={"skill_level": "intermediate", "style_preferences": ["摇滚"]},
    )
    assert prefs.status_code == 200
    assert prefs.json()["data"]["skill_level"] == "intermediate"

    cleared = client.delete("/api/v1/guest/data", cookies={"guest_id": guest_id})
    assert cleared.status_code == 200
    assert cleared.json()["data"]["cleared"] is True
    assert cleared.json()["data"]["onboarding_completed"] is False


def test_guest_me_without_cookie(client: TestClient) -> None:
    res = client.get("/api/v1/guest/me")
    assert res.status_code == 401
    assert res.json()["code"] == 40101
