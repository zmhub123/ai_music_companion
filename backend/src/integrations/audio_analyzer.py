"""从音频流提取和弦时间轴（HPSS + 拍点 chroma + 七和弦模板）。"""

from __future__ import annotations

import asyncio
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
from pycore.core.logger import get_logger

logger = get_logger()

_MAX_ANALYZE_SEC = 90
_ANALYZE_SR = 11025
_DOWNLOAD_MAX_BYTES = 16 * 1024 * 1024

_CHROMA_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

_CHORD_TEMPLATES: dict[str, list[float]] = {}


def _add_template(name: str, intervals: tuple[int, ...]) -> None:
    for root in range(12):
        vec = [0.0] * 12
        for interval in intervals:
            vec[(root + interval) % 12] = 1.0
        chord_name = _CHROMA_NOTES[root] if name == "maj" else f"{_CHROMA_NOTES[root]}{name}"
        if name == "maj":
            chord_name = _CHROMA_NOTES[root]
        elif name == "min":
            chord_name = f"{_CHROMA_NOTES[root]}m"
        elif name == "7":
            chord_name = f"{_CHROMA_NOTES[root]}7"
        elif name == "maj7":
            chord_name = f"{_CHROMA_NOTES[root]}maj7"
        elif name == "m7":
            chord_name = f"{_CHROMA_NOTES[root]}m7"
        else:
            chord_name = f"{_CHROMA_NOTES[root]}{name}"
        _CHORD_TEMPLATES[chord_name] = vec


_add_template("maj", (0, 4, 7))
_add_template("min", (0, 3, 7))
_add_template("7", (0, 4, 7, 10))
_add_template("maj7", (0, 4, 7, 11))
_add_template("m7", (0, 3, 7, 10))


def _best_chord(chroma_vec: list[float]) -> str:
    import numpy as np

    vec = np.array(chroma_vec, dtype=float)
    best_name = "C"
    best_score = -1.0
    for name, template in _CHORD_TEMPLATES.items():
        t = np.array(template, dtype=float)
        score = float(np.dot(vec, t) / (np.linalg.norm(t) + 1e-6))
        if score > best_score:
            best_score = score
            best_name = name
    return best_name


def extend_timeline_to_duration(
    timeline: list[dict[str, Any]],
    duration_ms: int,
) -> list[dict[str, Any]]:
    """把分析窗口内的和弦走向平铺到整首歌时长。"""
    if not timeline or duration_ms <= 0:
        return timeline
    last_ms = int(timeline[-1]["start_ms"])
    if last_ms >= duration_ms - 2000:
        return timeline

    gaps = [
        int(timeline[i + 1]["start_ms"]) - int(timeline[i]["start_ms"])
        for i in range(len(timeline) - 1)
    ]
    avg_gap = int(sum(gaps) / len(gaps)) if gaps else 4000
    avg_gap = max(avg_gap, 1500)

    extended = list(timeline)
    cursor = last_ms + avg_gap
    index = 0
    while cursor < duration_ms:
        chord = str(timeline[index % len(timeline)]["chord"])
        extended.append({"start_ms": cursor, "chord": chord})
        cursor += avg_gap
        index += 1
    return extended


def analyze_audio_file(
    audio_path: Path,
    *,
    max_duration_sec: float = _MAX_ANALYZE_SEC,
    on_progress: Callable[[int], None] | None = None,
) -> list[dict[str, Any]]:
    import librosa
    import numpy as np

    y, sr = librosa.load(
        str(audio_path),
        mono=True,
        sr=_ANALYZE_SR,
        duration=max_duration_sec,
    )
    if y.size == 0:
        return [{"start_ms": 0, "chord": "C"}]

    y_harm, _y_perc = librosa.effects.hpss(y)
    hop_length = 4096
    chroma = librosa.feature.chroma_stft(y=y_harm, sr=sr, hop_length=hop_length)

    tempo, beat_frames = librosa.beat.beat_track(y=y_harm, sr=sr, hop_length=hop_length)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)

    timeline: list[dict[str, Any]] = []
    if beat_times.size >= 4:
        beats_per_chord = 8
        for index in range(0, len(beat_times) - 1, beats_per_chord):
            start_frame = beat_frames[index]
            end_frame = beat_frames[min(index + beats_per_chord, len(beat_frames) - 1)]
            if end_frame <= start_frame:
                continue
            segment = chroma[:, start_frame:end_frame]
            if segment.size == 0:
                continue
            vec = segment.mean(axis=1)
            vec = (vec / (np.linalg.norm(vec) + 1e-6)).tolist()
            chord = _best_chord(vec)
            timeline.append(
                {
                    "start_ms": int(float(beat_times[index]) * 1000),
                    "chord": chord,
                }
            )
            if on_progress and beat_times.size:
                on_progress(int(min(100, (index / beat_times.size) * 100)))
    else:
        frame_times = librosa.frames_to_time(range(chroma.shape[1]), sr=sr, hop_length=hop_length)
        window_sec = 3.0
        duration_sec = float(frame_times[-1]) if frame_times.size else 0.0
        window_count = max(int(duration_sec / window_sec) + 1, 1)
        for index in range(window_count):
            start_sec = index * window_sec
            end_sec = start_sec + window_sec
            mask = (frame_times >= start_sec) & (frame_times < end_sec)
            if not np.any(mask):
                continue
            vec = chroma[:, mask].mean(axis=1)
            vec = (vec / (np.linalg.norm(vec) + 1e-6)).tolist()
            chord = _best_chord(vec)
            timeline.append({"start_ms": int(start_sec * 1000), "chord": chord})

    if not timeline:
        timeline = [{"start_ms": 0, "chord": "C"}]

    merged: list[dict[str, Any]] = []
    for item in timeline:
        if merged and merged[-1]["chord"] == item["chord"]:
            continue
        merged.append(item)

    unique = len({item["chord"] for item in merged})
    logger.info(
        "audio chord timeline ready",
        segments=len(merged),
        unique_chords=unique,
        analyzed_sec=round(float(len(y)) / sr, 1),
    )
    return merged


async def download_audio_to_temp(source_url: str) -> Path:
    suffix = ".mp3"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = Path(tmp.name)
    tmp.close()
    total = 0
    async with httpx.AsyncClient(trust_env=False, timeout=90.0, follow_redirects=True) as client:
        async with client.stream("GET", source_url) as response:
            response.raise_for_status()
            with tmp_path.open("wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=65536):
                    total += len(chunk)
                    if total > _DOWNLOAD_MAX_BYTES:
                        logger.warning("audio download truncated", bytes=total)
                        break
                    f.write(chunk)
    return tmp_path


async def analyze_audio_from_url(
    source_url: str,
    *,
    duration_ms: int | None = None,
    on_progress: Callable[[int], None] | None = None,
) -> list[dict[str, Any]]:
    path = await download_audio_to_temp(source_url)
    try:
        timeline = await asyncio.to_thread(analyze_audio_file, path, on_progress=on_progress)
        if duration_ms and duration_ms > 0:
            timeline = extend_timeline_to_duration(timeline, duration_ms)
        return timeline
    finally:
        path.unlink(missing_ok=True)
