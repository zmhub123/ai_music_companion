from src.integrations.lyric_provider import parse_lrc_text
from src.services.score_merge import merge_chords_with_lrc


def test_parse_lrc_text() -> None:
    lrc = """
{"t":0,"c":[{"tx":"作词"}]}
[00:14.61]无力感在把眼泪一点一点吞噬
[00:17.99]空旷的街道早没了一点声
"""
    lines = parse_lrc_text(lrc)
    assert len(lines) == 2
    assert lines[0]["start_ms"] == 14_610
    assert lines[0]["lyric_line"] == "无力感在把眼泪一点一点吞噬"


def test_merge_chords_with_lrc() -> None:
    chord_lines = [
        {"position": 0, "chord": "C", "lyric_line": "（前奏）", "section": "intro"},
        {"position": 0, "chord": "G", "lyric_line": "· · · ·", "section": "intro"},
        {"position": 0, "chord": "C", "lyric_line": "无力感在把眼泪一点一点吞噬", "section": "vocal"},
        {"position": 0, "chord": "E7", "lyric_line": "空旷的街道早没了一点声", "section": "vocal"},
    ]
    lrc_lines = [
        {"start_ms": 14_610, "lyric_line": "无力感在把眼泪一点一点吞噬", "section": "vocal"},
        {"start_ms": 17_990, "lyric_line": "空旷的街道早没了一点声", "section": "vocal"},
        {"start_ms": 21_600, "lyric_line": "那天回到我们俩熟悉的城市", "section": "vocal"},
    ]

    merged = merge_chords_with_lrc(
        chord_lines,
        lrc_lines,
        skill_level="intermediate",
        simplify_chord=lambda chord, _: chord,
    )
    assert merged[0]["section"] == "intro"
    assert merged[2]["start_ms"] == 14_610
    assert merged[2]["chord"] == "C"
    assert merged[2]["chord_marks"][0]["position"] == 0
    assert merged[3]["chord"] == "E7"
    assert merged[4]["lyric_line"] == "那天回到我们俩熟悉的城市"


def test_female_chart_transpose() -> None:
    from src.integrations.chord_library import load_chart_from_file

    female = load_chart_from_file(3333988321, "female")
    assert female is not None
    assert female.key == "G"
    assert female.capo == 0
    assert female.parsed.guitar_lines[4]["chord"] == "Gmaj7"
