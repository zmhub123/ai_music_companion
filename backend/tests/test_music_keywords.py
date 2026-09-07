from src.integrations.music_provider import (
    extract_artist_search_keywords,
    extract_song_search_keywords,
    is_direct_song_request,
    is_mood_style_search_target,
)


def test_extract_song_name_from_want_listen() -> None:
    assert extract_song_search_keywords("我想听晴天") == "晴天"


def test_extract_song_name_from_quotes() -> None:
    assert extract_song_search_keywords("播放《南山南》") == "南山南"


def test_extract_seed_song_from_long_sentence() -> None:
    assert extract_song_search_keywords("最近很喜欢平凡之路，推荐一下") == "平凡之路"


def test_extract_artist_nickname_meimei() -> None:
    assert extract_artist_search_keywords("我很高兴，想听霉霉的歌") == "Taylor Swift"
    assert extract_artist_search_keywords("想听霉霉的歌") == "Taylor Swift"
    assert extract_artist_search_keywords("播放泰勒斯威夫特") == "Taylor Swift"


def test_meimei_request_is_not_mood_style_target() -> None:
    assert is_mood_style_search_target("霉霉的歌") is False
    assert is_direct_song_request("想听霉霉的歌") is True


def test_cheerful_request_still_mood_style_target() -> None:
    assert is_mood_style_search_target("欢快的歌") is True
    assert is_direct_song_request("今天很开心，想听欢快的歌") is False
