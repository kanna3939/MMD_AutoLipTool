from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.audio_errors import AudioConvertError, AudioErrorCode
from src.core.delivery_package import (
    DeliveryArtifactOperations,
    DeliveryCancelToken,
    DeliveryContractError,
    DeliveryStartContext,
    capture_source_audio_identity,
)
from src.core.diagnostic_report import (
    DiagnosticReportError,
    format_diagnostic_report,
    write_diagnostic_report,
)
from src.core.ffmpeg_runner import run_ffmpeg_mmd_wav_cancellable
from src.core.mmd_wav_export import (
    MMD_WAV_SPEC,
    MmdWavExportResult,
    _validate_mmd_wav_file,
    export_mmd_wav,
)
from src.vmd_writer.effective_shape_adapter import (
    build_morph_frames_from_effective_shape_plan,
)
from src.vmd_writer.validator import (
    VmdReadbackValidationError,
    validate_morph_vmd_readback,
)
from src.vmd_writer.writer import write_morph_frames_vmd


_UTF8_BOM = b"\xef\xbb\xbf"


def _raise_delivery_error(
    code: str,
    message: str,
    cause: BaseException | None = None,
) -> None:
    error = DeliveryContractError(code, message)
    if cause is None:
        raise error
    raise error from cause


def _raise_cancelled() -> None:
    _raise_delivery_error("output_cancelled", "delivery output was cancelled.")


def _ensure_not_cancelled(cancel_token: DeliveryCancelToken) -> None:
    if cancel_token.cancel_requested:
        _raise_cancelled()


def _resolve_for_comparison(value: object) -> Path:
    try:
        return Path(value).resolve(strict=False)
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        raise ValueError("path could not be normalized") from error


def _raise_if_cancelled_after_error(
    cancel_token: DeliveryCancelToken,
    cause: BaseException,
) -> None:
    if cancel_token.cancel_requested:
        try:
            _raise_cancelled()
        except DeliveryContractError as error:
            raise error from cause


def _generate_and_validate_vmd(
    context: DeliveryStartContext,
    output_path: Path,
    cancel_token: DeliveryCancelToken,
) -> None:
    _ensure_not_cancelled(cancel_token)
    state = context.current_state

    try:
        prepared_frames = build_morph_frames_from_effective_shape_plan(
            state.effective_shape_plan,
            output_morph_names=state.output_morph_names,
        )
        expected_frame_count = state.diagnostics_snapshot.adjustment_summary.effective_morph_frame_count
        if expected_frame_count is not None and expected_frame_count != len(prepared_frames):
            _raise_delivery_error(
                "vmd_write_failed",
                "effective morph frame count does not match the delivery state.",
            )
        write_morph_frames_vmd(
            output_path=output_path,
            morph_frames=prepared_frames,
            model_name=state.writer_parameters.vmd_model_name,
            output_morph_names=state.output_morph_names,
        )
    except DeliveryContractError:
        raise
    except Exception as error:
        _raise_if_cancelled_after_error(cancel_token, error)
        _raise_delivery_error(
            "vmd_write_failed",
            "the delivery VMD could not be generated.",
            error,
        )

    _ensure_not_cancelled(cancel_token)
    try:
        validate_morph_vmd_readback(
            output_path,
            expected_model_name=state.writer_parameters.vmd_model_name,
            expected_morph_frames=prepared_frames,
            expected_output_morph_names=state.output_morph_names,
        )
    except VmdReadbackValidationError as error:
        _raise_if_cancelled_after_error(cancel_token, error)
        _raise_delivery_error(
            "vmd_validation_failed",
            "the generated delivery VMD did not pass read-back validation.",
            error,
        )
    except Exception as error:
        _raise_if_cancelled_after_error(cancel_token, error)
        _raise_delivery_error(
            "vmd_validation_failed",
            "the generated delivery VMD could not be validated.",
            error,
        )
    _ensure_not_cancelled(cancel_token)


def _map_audio_convert_error(error: AudioConvertError) -> tuple[str, str]:
    code = error.info.code
    if code == AudioErrorCode.MMD_WAV_VALIDATION_FAILED:
        return (
            "mmd_wav_validation_failed",
            "the generated MMD WAV did not pass format validation.",
        )
    return (
        "mmd_wav_write_failed",
        "the MMD WAV could not be generated.",
    )


def _raise_source_audio_changed(cause: BaseException | None = None) -> None:
    _raise_delivery_error(
        "source_audio_changed",
        "the source audio identity changed during delivery.",
        cause,
    )


def _validate_mmd_wav_result(
    result: object,
    output_path: Path,
    context: DeliveryStartContext,
) -> None:
    if not isinstance(result, MmdWavExportResult):
        _raise_delivery_error(
            "mmd_wav_validation_failed",
            "the MMD WAV exporter returned an invalid result.",
        )

    state = context.current_state
    try:
        result_source_path = _resolve_for_comparison(result.source_path)
        expected_source_path = state.source_identity.resolved_path
        result_output_path = _resolve_for_comparison(result.mmd_wav_path)
        expected_output_path = _resolve_for_comparison(output_path)
    except ValueError as error:
        _raise_delivery_error(
            "mmd_wav_validation_failed",
            "the MMD WAV exporter returned an invalid path.",
            error,
        )

    if result_source_path != expected_source_path:
        _raise_delivery_error(
            "mmd_wav_validation_failed",
            "the MMD WAV exporter used an unexpected source path.",
        )
    if result_output_path != expected_output_path:
        _raise_delivery_error(
            "mmd_wav_validation_failed",
            "the MMD WAV exporter used an unexpected output path.",
        )
    if result.spec != MMD_WAV_SPEC or result.spec != state.mmd_wav_spec:
        _raise_delivery_error(
            "mmd_wav_validation_failed",
            "the MMD WAV exporter returned an unexpected format specification.",
        )

    try:
        output_stat = output_path.stat()
        output_is_file = output_path.is_file()
    except OSError as error:
        _raise_delivery_error(
            "mmd_wav_validation_failed",
            "the generated MMD WAV could not be inspected.",
            error,
        )
    if not output_is_file or output_stat.st_size <= 0:
        _raise_delivery_error(
            "mmd_wav_validation_failed",
            "the generated MMD WAV is missing or empty.",
        )
    if result.file_size_bytes != output_stat.st_size:
        _raise_delivery_error(
            "mmd_wav_validation_failed",
            "the MMD WAV result size does not match the output file.",
        )

    try:
        _validate_mmd_wav_file(output_path)
    except AudioConvertError as error:
        code, message = _map_audio_convert_error(error)
        _raise_delivery_error(code, message, error)
    except Exception as error:
        _raise_delivery_error(
            "mmd_wav_validation_failed",
            "the generated MMD WAV could not be validated.",
            error,
        )


def _generate_and_validate_mmd_wav(
    context: DeliveryStartContext,
    output_path: Path,
    cancel_token: DeliveryCancelToken,
) -> None:
    _ensure_not_cancelled(cancel_token)
    state = context.current_state
    source_path = state.audio_probe.source_path

    try:
        pre_identity = capture_source_audio_identity(source_path)
    except Exception as error:
        _raise_if_cancelled_after_error(cancel_token, error)
        _raise_source_audio_changed(error)
    if pre_identity != state.source_identity:
        _raise_source_audio_changed()

    def cancellable_runner(**kwargs: Any):
        return run_ffmpeg_mmd_wav_cancellable(
            **kwargs,
            cancel_token=cancel_token,
        )

    try:
        result = export_mmd_wav(
            probe_result=state.audio_probe,
            ffmpeg_path=state.ffmpeg_path,
            output_path=output_path,
            runner=cancellable_runner,
        )
    except DeliveryContractError:
        raise
    except Exception as error:
        _raise_if_cancelled_after_error(cancel_token, error)
        if isinstance(error, AudioConvertError):
            code, message = _map_audio_convert_error(error)
            _raise_delivery_error(code, message, error)
        _raise_delivery_error(
            "mmd_wav_write_failed",
            "the MMD WAV could not be generated.",
            error,
        )

    _ensure_not_cancelled(cancel_token)
    _validate_mmd_wav_result(result, Path(output_path), context)
    _ensure_not_cancelled(cancel_token)

    try:
        post_identity = capture_source_audio_identity(source_path)
    except Exception as error:
        _raise_if_cancelled_after_error(cancel_token, error)
        _raise_source_audio_changed(error)
    if post_identity != state.source_identity:
        _raise_source_audio_changed()
    _ensure_not_cancelled(cancel_token)


def _validate_report_bytes(actual_bytes: bytes, expected_bytes: bytes) -> None:
    if actual_bytes != expected_bytes:
        _raise_delivery_error(
            "report_validation_failed",
            "the generated diagnostic report bytes do not match the snapshot.",
        )
    try:
        actual_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        _raise_delivery_error(
            "report_validation_failed",
            "the generated diagnostic report is not valid UTF-8.",
            error,
        )
    if actual_bytes.startswith(_UTF8_BOM):
        _raise_delivery_error(
            "report_validation_failed",
            "the generated diagnostic report contains a UTF-8 BOM.",
        )
    if b"\r" in actual_bytes or not actual_bytes.endswith(b"\n"):
        _raise_delivery_error(
            "report_validation_failed",
            "the generated diagnostic report does not use LF line endings.",
        )


def _generate_and_validate_report(
    context: DeliveryStartContext,
    output_path: Path,
    cancel_token: DeliveryCancelToken,
) -> None:
    _ensure_not_cancelled(cancel_token)
    snapshot = context.current_state.diagnostics_snapshot
    try:
        expected_bytes = format_diagnostic_report(
            snapshot,
            generated_at=context.report_generated_at,
        ).encode("utf-8")
        write_diagnostic_report(
            snapshot,
            output_path,
            generated_at=context.report_generated_at,
        )
    except DeliveryContractError:
        raise
    except (DiagnosticReportError, OSError, UnicodeError, ValueError, TypeError) as error:
        _raise_if_cancelled_after_error(cancel_token, error)
        _raise_delivery_error(
            "report_write_failed",
            "the delivery diagnostic report could not be generated.",
            error,
        )
    except Exception as error:
        _raise_if_cancelled_after_error(cancel_token, error)
        _raise_delivery_error(
            "report_write_failed",
            "the delivery diagnostic report could not be generated.",
            error,
        )

    _ensure_not_cancelled(cancel_token)
    try:
        actual_bytes = Path(output_path).read_bytes()
    except (OSError, ValueError, TypeError) as error:
        _raise_if_cancelled_after_error(cancel_token, error)
        _raise_delivery_error(
            "report_validation_failed",
            "the delivery diagnostic report could not be read back.",
            error,
        )
    _validate_report_bytes(actual_bytes, expected_bytes)
    _ensure_not_cancelled(cancel_token)


def build_delivery_artifact_operations() -> DeliveryArtifactOperations:
    """Build the GUI-independent B3 artifact generation operations."""
    return DeliveryArtifactOperations(
        generate_and_validate_vmd=_generate_and_validate_vmd,
        generate_and_validate_mmd_wav=_generate_and_validate_mmd_wav,
        generate_and_validate_report=_generate_and_validate_report,
    )


__all__ = ["build_delivery_artifact_operations"]
