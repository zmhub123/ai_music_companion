import asyncio

from src.integrations.audio_analyzer import extend_timeline_to_duration
from src.integrations.llm_chord_refiner import _fallback_lines
from src.integrations.dashscope_client import DashScopeClient
from src.integrations.llm_chord_refiner import refine_chords_with_llm
from src.services.score_audio_pipeline import SCORE_AUDIO_VERSION, build_score_from_audio


def test_extend_timeline_to_full_duration() -> None:
    timeline = [
        {"start_ms": 0, "chord": "C"},
        {"start_ms": 4000, "chord": "Em7"},
        {"start_ms": 8000, "chord": "Am"},
    ]
    extended = extend_timeline_to_duration(timeline, duration_ms=60_000)
    assert extended[-1]["start_ms"] >= 56_000
    chords = {item["chord"] for item in extended}
    assert len(chords) >= 2


def test_fallback_lines_multi_chords_per_line() -> None:
    lrc_lines = [
        {"start_ms": 10_000, "lyric_line": "后来我总算学会了如何去爱"},
        {"start_ms": 18_000, "lyric_line": "可惜你早已远去消失在人海"},
    ]
    lines = _fallback_lines(lrc_lines, song_name="后来", instrument="ukulele")
    assert len(lines) == 2
    assert len(lines[0]["chord_marks"]) >= 2
    chords = {mark["chord"] for mark in lines[0]["chord_marks"]}
    assert "C" in chords
    assert "Em7" in chords or "Am" in chords


def test_build_score_from_audio_mock() -> None:
    llm = DashScopeClient(force_mock=True)
    lrc_lines = [
        {"start_ms": 13_000, "lyric_line": "后来我总算学会了如何去爱"},
        {"start_ms": 21_000, "lyric_line": "可惜你早已远去消失在人海"},
    ]
    score = asyncio.run(
        build_score_from_audio(
            llm=llm,
            song_id=254485,
            song_name="后来",
            artist_name="刘若英",
            cover_url="",
            duration_ms=320_000,
            instrument="ukulele",
            vocal_version="female",
            skill_level="beginner",
            chord_timeline=[
                {"start_ms": 0, "chord": "C"},
                {"start_ms": 4000, "chord": "Em7"},
            ],
            lrc_lines=lrc_lines,
        )
    )
    assert score["_version"] == SCORE_AUDIO_VERSION
    assert score["chord_source"] == "audio_analysis+llm"
    assert score["capo"] == 3
    assert score["rhythm_pattern"]["label"].startswith("节奏型")
    assert "慢板" in score["rhythm_pattern"]["label"]
    vocal_lines = [line for line in score["lines"] if line.get("section") != "intro"]
    assert len(vocal_lines[0]["chord_marks"]) >= 2
