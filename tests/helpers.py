from __future__ import annotations

from contextlib import contextmanager
import math
from pathlib import Path
import shutil
import struct
from uuid import uuid4
import wave


def write_test_wav(
    path: Path,
    sample_rate: int = 44100,
    lead_sec: float = 0.2,
    speech_sec: float = 0.6,
    trail_sec: float = 0.2,
    amplitude: int = 12000,
) -> None:
    total_sec = lead_sec + speech_sec + trail_sec
    total_frames = int(total_sec * sample_rate)
    lead_frames = int(lead_sec * sample_rate)
    speech_frames = int(speech_sec * sample_rate)
    speech_end = lead_frames + speech_frames

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        frames: list[bytes] = []
        for frame_index in range(total_frames):
            if lead_frames <= frame_index < speech_end:
                t = (frame_index - lead_frames) / sample_rate
                sample = int(amplitude * math.sin(2.0 * math.pi * 220.0 * t))
            else:
                sample = 0
            frames.append(struct.pack("<h", sample))

        wav_file.writeframes(b"".join(frames))


@contextmanager
def workspace_tempdir(prefix: str = "test") -> Path:
    temp_dir = Path("sample") / f"_{prefix}_{uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
