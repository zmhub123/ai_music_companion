import asyncio

from src.integrations.music_provider import (
    SongCandidate,
    _is_cover_version,
    _is_official_seed_song,
    search_songs,
)


def test_cover_detection() -> None:
    cover = SongCandidate(
        netease_song_id=2668397359,
        song_name="晴天 (原唱 周杰伦)",
        artist_name="RyaVocal",
        cover_url="",
    )
    assert _is_cover_version(cover) is True

    official = SongCandidate(
        netease_song_id=186016,
        song_name="晴天",
        artist_name="周杰伦",
        cover_url="",
    )
    assert _is_cover_version(official) is False
    assert _is_official_seed_song(official) is True


def test_homonym_cover_filtered_by_canonical() -> None:
    canonical = SongCandidate(
        netease_song_id=3333988321,
        song_name="一半一半",
        artist_name="Top Barry",
        cover_url="",
        search_rank=0,
        popularity=100.0,
    )
    homonym = SongCandidate(
        netease_song_id=1979007503,
        song_name="一半一半",
        artist_name="洛天依Official",
        cover_url="",
        search_rank=2,
        popularity=20.0,
    )
    assert _is_cover_version(homonym, canonical=canonical) is True
    assert _is_cover_version(canonical, canonical=canonical) is False


def test_search_yiban_yiban_prefers_topbarry(monkeypatch) -> None:
    def fake_search(keywords: str, limit: int) -> list[SongCandidate]:
        return [
            SongCandidate(
                netease_song_id=3333988321,
                song_name="一半一半",
                artist_name="Top Barry",
                cover_url="",
                album_name="一半一半",
                popularity=100.0,
            ),
            SongCandidate(
                netease_song_id=1979007503,
                song_name="一半一半",
                artist_name="洛天依Official",
                cover_url="",
                popularity=20.0,
            ),
            SongCandidate(
                netease_song_id=999,
                song_name="一半一半R&B",
                artist_name="某歌手",
                cover_url="",
                popularity=10.0,
            ),
        ][:limit]

    async def fake_enrich(candidates: list[SongCandidate]) -> list[SongCandidate]:
        for song in candidates:
            song.playable = True
        return candidates

    monkeypatch.setattr("src.integrations.music_provider._pyncm_available", lambda: True)
    monkeypatch.setattr("src.integrations.music_provider._search_pyncm_sync", fake_search)
    monkeypatch.setattr("src.integrations.music_provider._enrich_playability", fake_enrich)

    songs = asyncio.run(search_songs("一半一半", limit=3))
    assert songs
    assert songs[0].netease_song_id == 3333988321
    assert songs[0].artist_name == "Top Barry"
    assert songs[0].is_original is True
    assert all(song.netease_song_id != 1979007503 for song in songs)


def test_search_xingrong_prefers_shen_yicheng(monkeypatch) -> None:
    def fake_search(keywords: str, limit: int) -> list[SongCandidate]:
        if keywords == "形容":
            return [
                SongCandidate(
                    netease_song_id=1819027992,
                    song_name="形容 (Gamer Version)",
                    artist_name="沈以诚",
                    cover_url="",
                    popularity=100.0,
                ),
                SongCandidate(
                    netease_song_id=2049399316,
                    song_name="形容",
                    artist_name="洛依er",
                    cover_url="",
                    popularity=25.0,
                ),
                SongCandidate(
                    netease_song_id=1336856864,
                    song_name="形容",
                    artist_name="沈以诚",
                    cover_url="",
                    popularity=100.0,
                ),
            ][:limit]
        if keywords == "形容 原唱":
            return [
                SongCandidate(
                    netease_song_id=1336856864,
                    song_name="形容",
                    artist_name="沈以诚",
                    cover_url="",
                    popularity=100.0,
                ),
            ][:limit]
        return []

    async def fake_enrich(candidates: list[SongCandidate]) -> list[SongCandidate]:
        for song in candidates:
            song.playable = True
        return candidates

    monkeypatch.setattr("src.integrations.music_provider._pyncm_available", lambda: True)
    monkeypatch.setattr("src.integrations.music_provider._search_pyncm_sync", fake_search)
    monkeypatch.setattr("src.integrations.music_provider._enrich_playability", fake_enrich)

    songs = asyncio.run(search_songs("形容", limit=3))
    assert songs
    assert songs[0].netease_song_id == 1336856864
    assert songs[0].artist_name == "沈以诚"
    assert songs[0].is_original is True
    assert all(song.netease_song_id != 2049399316 for song in songs)
