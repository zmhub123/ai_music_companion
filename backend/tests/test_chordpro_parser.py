from pathlib import Path

from src.integrations.chord_library import load_chart_from_file
from src.integrations.chordpro_parser import parse_chordpro

CHORDPRO_SAMPLE = """
{title:一半一半}
{artist:Top Barry}
{key:C}
{capo:2}
{source:verified}
{start_of_intro}
[Cmaj7|C]（前奏）
[G|G]· · · ·
{end_of_intro}
[Cmaj7|C]无力感在把眼泪一点一点吞噬
[E7|E7]空旷的街道早没了一点声
"""


def test_parse_chordpro_metadata_and_lines() -> None:
    chart = parse_chordpro(CHORDPRO_SAMPLE)
    assert chart.title == "一半一半"
    assert chart.artist == "Top Barry"
    assert chart.key == "C"
    assert chart.capo == 2
    assert chart.source == "verified"
    assert len(chart.guitar_lines) == 4
    assert chart.guitar_lines[0]["section"] == "intro"
    assert chart.guitar_lines[0]["chord"] == "Cmaj7"
    assert chart.ukulele_lines[0]["chord"] == "C"
    assert chart.guitar_lines[-1]["lyric_line"] == "空旷的街道早没了一点声"


def test_load_yiban_chart_from_seed_file() -> None:
    chart = load_chart_from_file(3333988321, "male")
    assert chart is not None
    assert chart.song_name == "一半一半"
    assert chart.capo == 2
    assert len(chart.parsed.guitar_lines) >= 20


def test_female_chart_transposed_from_male_seed() -> None:
    male = load_chart_from_file(3333988321, "male")
    female = load_chart_from_file(3333988321, "female")
    assert male is not None and female is not None
    assert female.key == "G"
    assert female.capo == 0
    assert female.parsed.guitar_lines[0]["chord"] == "Gmaj7"


def test_chordpro_seed_file_exists() -> None:
    path = Path(__file__).resolve().parents[1] / "data" / "chordpro" / "3333988321_male.chordpro"
    assert path.is_file()
