from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gui_wx.analysis_rollback import (  # noqa: E402
    ROLLBACK_FORBIDDEN_FAILURE_CLASSES,
    is_rollback_forbidden_failure_class,
)
from gui_wx.voice_only_errors import format_voice_only_analysis_error  # noqa: E402
from src.core.whisper_model_runtime import WhisperModelRuntimeError  # noqa: E402
from src.core.whisper_timing import WhisperTimingError  # noqa: E402


def test_b6_rollback_forbidden_classes_are_shared():
    assert ROLLBACK_FORBIDDEN_FAILURE_CLASSES == frozenset(
        {
            "model_unavailable",
            "integrity_mismatch",
            "load_failure",
            "memory_failure",
            "transcribe_failure",
        }
    )
    assert is_rollback_forbidden_failure_class("load_failure")
    assert not is_rollback_forbidden_failure_class("cancelled")


def test_voice_only_whisper_notice_does_not_expose_raw_exception():
    raw = "C:/private/model.bin?token=secret"
    message = format_voice_only_analysis_error(
        WhisperTimingError(raw, code="whisper_transcribe_failed")
    )
    assert raw not in message
    assert "詳細:" not in message


def test_voice_only_runtime_failure_notice_is_safe():
    raw = "loader traceback C:/private/model.bin"
    message = format_voice_only_analysis_error(
        WhisperModelRuntimeError(
            "checkpoint_bytes_load_failed",
            raw,
            failure_class="memory_failure",
        )
    )
    assert raw not in message
    assert "メモリ" in message
