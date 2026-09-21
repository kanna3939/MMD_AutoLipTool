from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from pathlib import Path
import subprocess

from src.core.audio_convert import convert_to_analysis_wav
from src.core.audio_probe import probe_audio_file
from src.core.ffmpeg_runner import (
    run_ffmpeg_analysis_wav_cancellable,
    run_ffmpeg_mmd_wav_cancellable,
)
from src.core.ffmpeg_locator import locate_ffmpeg_tools
from src.core.mmd_wav_export import export_mmd_wav
from tests.ms26_wav_duration_helpers import (
    assert_conversion_result_identity,
    assert_source_identity,
    compare_wav_durations,
    sha256_file,
    write_test_pcm_wav,
)


CONVERSION_TIMEOUT_SEC = 300.0


@dataclass(frozen=True)
class MatrixCase:
    name: str
    source_format: str
    channels: int
    source_rate_hz: int
    duration_sec: float
    use_cancellable_runner: bool


def _matrix_cases() -> tuple[MatrixCase, ...]:
    cases: list[MatrixCase] = []
    for source_rate_hz in (44100, 48000):
        for channels in (1, 2, 3):
            for duration_sec in (1.37, 5.11):
                cases.append(
                    MatrixCase(
                        name=f"wav_{channels}ch_{source_rate_hz}hz_{duration_sec}",
                        source_format="wav",
                        channels=channels,
                        source_rate_hz=source_rate_hz,
                        duration_sec=duration_sec,
                        use_cancellable_runner=False,
                    )
                )
    for source_format in ("mp3", "m4a"):
        for channels in (1, 2):
            for duration_sec in (1.37, 5.11):
                cases.append(
                    MatrixCase(
                        name=f"{source_format}_{channels}ch_48000hz_{duration_sec}",
                        source_format=source_format,
                        channels=channels,
                        source_rate_hz=48000,
                        duration_sec=duration_sec,
                        use_cancellable_runner=False,
                    )
                )
    cancellable_cases = [
        replace(
            case,
            name=f"{case.name}_cancellable",
            use_cancellable_runner=True,
        )
        for case in cases
        if case.source_format in {"wav", "m4a"}
        and case.channels == 2
        and case.source_rate_hz == 48000
    ]
    return tuple(cases + cancellable_cases)


def _encode_compressed_source(
    ffmpeg_path: Path,
    source_pcm_path: Path,
    output_path: Path,
    source_format: str,
    channels: int,
) -> None:
    codec = "libmp3lame" if source_format == "mp3" else "aac"
    command = [
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_pcm_path),
        "-vn",
        "-c:a",
        codec,
        "-ar",
        "48000",
        "-ac",
        str(channels),
        "-b:a",
        "128k",
        str(output_path),
    ]
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=CONVERSION_TIMEOUT_SEC,
        shell=False,
    )
    assert result.returncode == 0, (
        f"FFmpeg source generation failed for {output_path.name}: "
        f"returncode={result.returncode}\n{result.stderr}"
    )
    assert output_path.is_file() and output_path.stat().st_size > 0


def _create_source(tmp_path: Path, case: MatrixCase, ffmpeg_path: Path) -> Path:
    if case.source_format == "wav":
        source_path = tmp_path / f"{case.name}.wav"
        write_test_pcm_wav(
            source_path,
            duration_sec=case.duration_sec,
            sample_rate_hz=case.source_rate_hz,
            channel_count=case.channels,
        )
        return source_path

    pcm_path = tmp_path / f"{case.name}_source.wav"
    write_test_pcm_wav(
        pcm_path,
        duration_sec=case.duration_sec,
        sample_rate_hz=case.source_rate_hz,
        channel_count=case.channels,
    )
    source_path = tmp_path / f"{case.name}.{case.source_format}"
    _encode_compressed_source(
        ffmpeg_path,
        pcm_path,
        source_path,
        case.source_format,
        case.channels,
    )
    return source_path


def _tool_version(tool_path: Path) -> str:
    result = subprocess.run(
        [str(tool_path), "-version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=CONVERSION_TIMEOUT_SEC,
        shell=False,
    )
    assert result.returncode == 0, (
        f"tool version check failed for {tool_path}: "
        f"returncode={result.returncode}\n{result.stderr}"
    )
    return (result.stdout or result.stderr).splitlines()[0]


def test_real_ffmpeg_duration_matrix_and_runner_paths(tmp_path: Path) -> None:
    locator = locate_ffmpeg_tools()
    assert locator.is_complete
    assert locator.ffmpeg.path is not None
    assert locator.ffprobe.path is not None
    ffmpeg_path = locator.ffmpeg.path
    ffprobe_path = locator.ffprobe.path
    assert ffmpeg_path.is_file(), f"required FFmpeg is missing: {ffmpeg_path}"
    assert ffprobe_path.is_file(), f"required ffprobe is missing: {ffprobe_path}"
    ffmpeg_version = _tool_version(ffmpeg_path)
    ffprobe_version = _tool_version(ffprobe_path)
    cases = _matrix_cases()
    assert len(cases) == 24

    measurements: list[str] = []
    for case in cases:
        source_path = _create_source(tmp_path, case, ffmpeg_path)
        source_sha256 = sha256_file(source_path)
        probe = probe_audio_file(
            source_path,
            ffprobe_path,
            timeout_sec=CONVERSION_TIMEOUT_SEC,
        )
        assert_source_identity(source_path, source_sha256)
        assert probe.source_path.resolve() == source_path.resolve()
        assert probe.audio_stream.channel_count == case.channels
        assert probe.audio_stream.sample_rate_hz == case.source_rate_hz

        analysis_cache = tmp_path / "analysis_cache" / case.name
        analysis_runner = (
            run_ffmpeg_analysis_wav_cancellable
            if case.use_cancellable_runner
            else None
        )
        mmd_runner = (
            run_ffmpeg_mmd_wav_cancellable
            if case.use_cancellable_runner
            else None
        )
        analysis_result = convert_to_analysis_wav(
            probe,
            ffmpeg_path,
            cache_dir=analysis_cache,
            runner=analysis_runner,
            timeout_sec=CONVERSION_TIMEOUT_SEC,
        )
        assert_source_identity(source_path, source_sha256)
        mmd_path = tmp_path / "mmd_outputs" / f"{case.name}.wav"
        mmd_result = export_mmd_wav(
            probe,
            ffmpeg_path,
            mmd_path,
            runner=mmd_runner,
            timeout_sec=CONVERSION_TIMEOUT_SEC,
        )
        assert_source_identity(source_path, source_sha256)
        assert_conversion_result_identity(source_path, analysis_result, mmd_result)
        comparison = compare_wav_durations(
            analysis_result.analysis_wav_path,
            mmd_result.mmd_wav_path,
        )
        assert comparison.difference <= Fraction(1, 20)
        measurements.append(
            " | ".join(
                (
                    case.name,
                    f"runner={'cancellable' if case.use_cancellable_runner else 'normal'}",
                    f"analysis_frames={comparison.analysis.frames}",
                    f"analysis_rate={comparison.analysis.rate_hz}",
                    f"analysis_duration={float(comparison.analysis.duration):.9f}",
                    f"mmd_frames={comparison.mmd.frames}",
                    f"mmd_rate={comparison.mmd.rate_hz}",
                    f"mmd_duration={float(comparison.mmd.duration):.9f}",
                    f"difference={float(comparison.difference):.9f}",
                    f"source_sha256={source_sha256}",
                )
            )
        )

    print(
        "MS26-B2 locator: "
        f"ffmpeg_source={locator.ffmpeg.source.value} "
        f"ffmpeg_path={ffmpeg_path} "
        f"ffmpeg_version={ffmpeg_version} "
        f"ffprobe_source={locator.ffprobe.source.value} "
        f"ffprobe_path={ffprobe_path} "
        f"ffprobe_version={ffprobe_version}"
    )
    print("MS26-B2 real FFmpeg duration matrix")
    for measurement in measurements:
        print(measurement)
    assert len(measurements) == len(cases)
