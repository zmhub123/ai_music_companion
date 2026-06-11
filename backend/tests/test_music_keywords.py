from src.integrations.music_provider import extract_song_search_keywords


def test_extract_song_name_from_want_listen() -> None:
    assert extract_song_search_keywords("我想听晴天") == "晴天"


def test_extract_song_name_from_quotes() -> None:
    assert extract_song_search_keywords("播放《南山南》") == "南山南"


def test_extract_seed_song_from_long_sentence() -> None:
    assert extract_song_search_keywords("最近很喜欢平凡之路，推荐一下") == "平凡之路"
