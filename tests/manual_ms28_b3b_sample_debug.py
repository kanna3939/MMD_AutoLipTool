from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import wx


REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "sample"
TARGETS = tuple(
    SAMPLE / f"{index:02d}-MMD_AutoLipTool説明3.txt" for index in range(4)
)
DEBUG_ROOT = REPO / "debug"
REQUIRED_SUMMARY_KEYS = {
    "failure_context",
    "resolver_diagnostics",
    "execution_diagnostics",
    "sync_inputs",
    "contract_summary",
    "downstream",
}


def pump_until(app: wx.App, predicate, *, timeout: float | None, label: str) -> None:
    deadline = None if timeout is None else time.monotonic() + timeout
    while deadline is None or time.monotonic() < deadline:
        app.ProcessPendingEvents()
        wx.YieldIfNeeded()
        if predicate():
            return
        time.sleep(0.05)
    raise RuntimeError(f"timeout while waiting for {label}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_artifact_manifest(run_dir: Path, manifest: dict, relative_name: str) -> None:
    artifact = next(
        (
            item
            for item in manifest.get("artifact_files", [])
            if str(item.get("relative_name", "")).replace("\\", "/")
            == relative_name.replace("\\", "/")
        ),
        None,
    )
    if not isinstance(artifact, dict):
        raise RuntimeError(f"manifest entry is missing: {relative_name}")
    path = run_dir / relative_name
    if not path.is_file():
        raise RuntimeError(f"artifact is missing: {path}")
    expected_bytes = artifact.get("bytes")
    if isinstance(expected_bytes, int) and path.stat().st_size != expected_bytes:
        raise RuntimeError(f"artifact size mismatch: {path}")
    if artifact.get("sha256") != _sha256(path):
        raise RuntimeError(f"artifact hash mismatch: {path}")


def _normalized_relative_name(value: object) -> str:
    return str(value).replace("\\", "/").lstrip("./")


def _load_projection_revisions(run_dir: Path, manifest: dict) -> list[int]:
    revisions: set[int] = set()
    for item in manifest.get("artifact_files", []):
        relative_name = _normalized_relative_name(item.get("relative_name", ""))
        parts = relative_name.split("/")
        if len(parts) >= 3 and parts[0] == "projections" and parts[2] == "projection_input.json":
            try:
                revisions.add(int(parts[1]))
            except (TypeError, ValueError):
                continue
    return sorted(revisions)


def _records_for_revision(manifest: dict, revision: int) -> list[dict]:
    return [
        item
        for item in manifest.get("stage_status", [])
        if item.get("projection_revision") == revision
    ]


def _execution_result(payload: dict) -> tuple[str, bool | str]:
    execution = payload.get("execution_diagnostics")
    if not isinstance(execution, dict):
        return "not_evaluable", "not_evaluable"
    operation = (execution.get("operations") or {}).get("preview_projection")
    if not isinstance(operation, dict):
        return "not_evaluable", "not_evaluable"
    outcome = operation.get("outcome")
    if outcome == "success":
        return "succeeded", operation.get("model_valid") is True
    if outcome == "failed":
        return "failed", False
    if outcome == "not_applicable":
        return "skipped", "not_evaluable"
    return "not_evaluable", "not_evaluable"


def _validate_run(run_dir: Path, *, input_name: str, expected_mode: str) -> dict:
    manifest_path = run_dir / "manifest.json"
    diagnostics_path = run_dir / "diagnostics.txt"
    if not manifest_path.is_file() or not diagnostics_path.is_file():
        raise RuntimeError(f"missing run metadata: {run_dir}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifact_errors: list[str] = []
    artifact_entries = manifest.get("artifact_files", [])
    for item in artifact_entries:
        relative_name = _normalized_relative_name(item.get("relative_name", ""))
        if not relative_name:
            artifact_errors.append("manifest relative_name is empty")
            continue
        try:
            _validate_artifact_manifest(run_dir, manifest, relative_name)
        except RuntimeError as error:
            artifact_errors.append(str(error))
    revisions = _load_projection_revisions(run_dir, manifest)
    if not revisions:
        artifact_errors.append("no projection_input revision is present")
    projection_payloads: list[dict] = []
    diagnostic_errors: list[str] = []
    preview_results: list[tuple[str, bool | str]] = []
    all_stage_names: list[str] = []
    for revision in revisions:
        projection_input_path = run_dir / "projections" / str(revision) / "projection_input.json"
        if not projection_input_path.is_file():
            artifact_errors.append(f"missing projection input: {projection_input_path}")
            continue
        projection_input = json.loads(projection_input_path.read_text(encoding="utf-8"))
        projection_payloads.append(projection_input)
        if not REQUIRED_SUMMARY_KEYS.issubset(projection_input):
            diagnostic_errors.append(f"diagnostic summary keys are incomplete: revision {revision}")
        stages = _records_for_revision(manifest, revision)
        stage_names = [item.get("stage") for item in stages]
        all_stage_names.extend(stage_names)
        stage_sequences = [item.get("record_sequence") for item in stages]
        if stage_sequences != sorted(
            value for value in stage_sequences if isinstance(value, int)
        ):
            diagnostic_errors.append(f"stage sequence is not ordered: revision {revision}")
        artifact_by_sequence = {
            item.get("record_sequence"): item
            for item in artifact_entries
            if isinstance(item.get("record_sequence"), int)
        }
        for stage in stages:
            sequence = stage.get("record_sequence")
            artifact = artifact_by_sequence.get(sequence)
            relative_name = _normalized_relative_name(
                artifact.get("relative_name", "") if isinstance(artifact, dict) else ""
            )
            if not relative_name.startswith("stages/"):
                continue
            stage_path = run_dir / relative_name
            if not stage_path.is_file():
                diagnostic_errors.append(f"stage artifact is missing: {relative_name}")
                continue
            stage_payload = json.loads(stage_path.read_text(encoding="utf-8"))
            if stage_payload.get("analysis_run_id") != manifest.get("analysis_run_id"):
                diagnostic_errors.append(f"stage owner mismatch: revision {revision}")
            if stage_payload.get("owner_kind") != "analysis_result":
                diagnostic_errors.append(f"stage owner kind mismatch: revision {revision}")
        if "projection_input" not in stage_names:
            diagnostic_errors.append(f"projection_input stage is missing: revision {revision}")
        if "effective_shape" in stage_names and stage_names.index("projection_input") > stage_names.index("effective_shape"):
            diagnostic_errors.append(f"projection stage order is invalid: revision {revision}")
        resolver = projection_input.get("resolver_diagnostics")
        if not isinstance(resolver, dict):
            diagnostic_errors.append(f"resolver diagnostics are missing: revision {revision}")
        else:
            attempts = resolver.get("attempts")
            if not isinstance(attempts, list):
                diagnostic_errors.append(f"resolver attempts are missing: revision {revision}")
            for attempt in attempts or []:
                if attempt.get("status") == "failed":
                    failure = attempt.get("failure")
                    if not isinstance(failure, dict):
                        diagnostic_errors.append(f"failed attempt has no leaf failure: revision {revision}")
                    elif failure.get("failure_code") in {None, "unknown_contract_failure"}:
                        diagnostic_errors.append(f"failed attempt has no concrete failure code: revision {revision}")
        execution = projection_input.get("execution_diagnostics")
        if not isinstance(execution, dict) or not isinstance(execution.get("operations"), dict):
            diagnostic_errors.append(f"execution diagnostics are missing: revision {revision}")
        comparison_path = run_dir / "projections" / str(revision) / "comparison.json"
        comparison_payload = (
            json.loads(comparison_path.read_text(encoding="utf-8"))
            if comparison_path.is_file()
            else projection_input
        )
        preview_results.append(_execution_result(comparison_payload))

    diagnostics_text = diagnostics_path.read_text(encoding="utf-8")
    if "stage=projection_input" not in diagnostics_text:
        diagnostic_errors.append(f"diagnostics text has no projection stage: {run_dir}")
    input_mode = manifest.get("input_mode") or manifest.get("input_mode_snapshot")
    regression_errors = []
    if input_mode is not None and input_mode != expected_mode:
        regression_errors.append(f"input mode mismatch: {input_mode} != {expected_mode}")
    diagnostic_validation = "passed" if not diagnostic_errors else "failed"
    artifact_validation = "passed" if not artifact_errors else "failed"
    regression_validation = "passed" if not regression_errors else "failed"
    preview_statuses = [item[0] for item in preview_results]
    if not preview_statuses:
        preview_execution = "not_evaluable"
        preview_model_valid: bool | str = "not_evaluable"
    elif all(status == "succeeded" for status in preview_statuses):
        preview_execution = "succeeded"
        preview_model_valid = True
    elif any(status == "failed" for status in preview_statuses):
        preview_execution = "failed"
        preview_model_valid = False
    elif any(status == "skipped" for status in preview_statuses):
        preview_execution = "skipped"
        preview_model_valid = "not_evaluable"
    else:
        preview_execution = "not_evaluable"
        preview_model_valid = "not_evaluable"
    return {
        "input": input_name,
        "input_mode": expected_mode,
        "run_dir": str(run_dir),
        "capture_status": manifest.get("capture_status"),
        "revision_count": len(revisions),
        "artifact_validation": artifact_validation,
        "diagnostic_validation": diagnostic_validation,
        "preview_execution": preview_execution,
        "preview_model_valid": preview_model_valid,
        "regression_validation": regression_validation,
        "reproduction_status": "not_evaluable",
        "harness_status": "completed"
        if artifact_validation == diagnostic_validation == regression_validation == "passed"
        else "failed",
        "projection_statuses": [payload.get("status") for payload in projection_payloads],
        "stage_names": all_stage_names,
        "artifact_errors": artifact_errors,
        "diagnostic_errors": diagnostic_errors,
        "regression_errors": regression_errors,
    }


def _child_run(*, sample_index: int, mode: str) -> int:
    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(REPO / "src"))

    from gui_wx.app import AutoLipToolApp

    original_message_box = wx.MessageBox
    wx.MessageBox = lambda message, caption="", *args, **kwargs: (
        print(f"MESSAGEBOX[{caption}]: {message}"),
        wx.ID_OK,
    )[1]
    app = None
    frame = None
    results: list[dict] = []
    try:
        app = AutoLipToolApp(False)
        frame = app.frame
        frame.Hide()
        frame.ui_state.debug_mode_enabled = True
        pump_until(
            app,
            lambda: frame.ui_state.whisper_model_selection.availability_scan_status
            != "pending",
            timeout=None,
            label="Whisper availability scan",
        )
        if frame.ui_state.whisper_model_selection.availability_scan_status != "succeeded":
            state = frame.ui_state.whisper_model_selection
            raise RuntimeError(
                "Whisper availability scan failed: "
                f"{state.availability_scan_status}/{state.availability_scan_failure_code}"
            )

        text_path = TARGETS[sample_index]
        wav_path = text_path.with_suffix(".wav")
        if not text_path.is_file() or not wav_path.is_file():
            raise FileNotFoundError(f"missing pair: {text_path} / {wav_path}")
        print(f"START {sample_index:02d} {mode}")
        if mode == "text_audio":
            frame._open_text_file(str(text_path), auto_load_counterpart=False)
        frame.controller.request_open_audio_file(str(wav_path))
        pump_until(
            app,
            lambda: not frame.ui_state.audio_worker_active
            and frame.ui_state.selected_analysis_wav is not None,
            timeout=None,
            label=f"audio load {text_path.name} ({mode})",
        )
        if frame.ui_state.input_mode != mode:
            raise RuntimeError(
                f"input mode mismatch before analysis: {frame.ui_state.input_mode} != {mode}"
            )
        frame._run_analysis()
        pump_until(
            app,
            lambda: not frame.ui_state.is_busy
            and frame._active_analysis_job_id is None,
            timeout=None,
            label=f"analysis {text_path.name} ({mode})",
        )
        app.ProcessPendingEvents()
        frame._debug_store.flush(timeout=30.0)
        trace = frame._accepted_debug_trace
        if trace is None:
            raise RuntimeError(f"no accepted debug trace for {text_path.name} ({mode})")
        run_dir = DEBUG_ROOT / f"{trace.folder_timestamp}_{trace.analysis_run_id}"
        result = _validate_run(
            run_dir,
            input_name=text_path.name,
            expected_mode=mode,
        )
        result["reproduction_status"] = (
            "reproduced"
            if sample_index in {0, 2}
            and any(
                payload.get("status") == "unavailable"
                for payload in (
                    json.loads(
                        (run_dir / "projections" / str(revision) / "projection_input.json").read_text(
                            encoding="utf-8"
                        )
                    )
                    for revision in _load_projection_revisions(
                        run_dir,
                        json.loads((run_dir / "manifest.json").read_text(encoding="utf-8")),
                    )
                )
            )
            else "not_reproduced"
            if sample_index in {0, 2}
            else "not_applicable"
        )
        print("CASE_RESULT " + json.dumps(result, ensure_ascii=False))
        return 0
    finally:
        wx.MessageBox = original_message_box
        if frame is not None:
            try:
                frame._shutdown_debug_store()
            except Exception as error:
                print(f"debug store shutdown failed: {error}")
            try:
                frame.Destroy()
            except Exception:
                pass


def _failed_case(*, sample_index: int, mode: str, message: str) -> dict:
    return {
        "input": TARGETS[sample_index].name,
        "input_mode": mode,
        "artifact_validation": "not_evaluable",
        "diagnostic_validation": "not_evaluable",
        "preview_execution": "not_evaluable",
        "preview_model_valid": "not_evaluable",
        "regression_validation": "not_evaluable",
        "reproduction_status": "not_evaluable",
        "harness_status": "failed",
        "harness_error": message,
    }


def _parent_run(*, check: str) -> int:
    results: list[dict] = []
    for sample_index in range(4):
        for mode in ("text_audio", "voice_only"):
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "--child",
                "--sample-index",
                str(sample_index),
                "--mode",
                mode,
            ]
            completed = subprocess.run(
                command,
                cwd=REPO,
                capture_output=True,
                text=True,
                check=False,
            )
            case = None
            for line in reversed(completed.stdout.splitlines()):
                if line.startswith("CASE_RESULT "):
                    case = json.loads(line[len("CASE_RESULT ") :])
                    break
            if case is None:
                case = _failed_case(
                    sample_index=sample_index,
                    mode=mode,
                    message=(completed.stderr.strip() or "child process did not return a case result"),
                )
            results.append(case)
            print(json.dumps(case, ensure_ascii=False))

    diagnostics_ok = all(
        result.get("artifact_validation") == "passed"
        and result.get("diagnostic_validation") == "passed"
        and result.get("regression_validation") == "passed"
        and result.get("harness_status") == "completed"
        for result in results
    )
    preview_ok = all(
        result.get("preview_execution") == "succeeded"
        and result.get("preview_model_valid") is True
        for result in results
    )
    print(f"CHECK {check}")
    print("RESULTS")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if not diagnostics_ok:
        return 1
    if check == "preview" and not preview_ok:
        return 2
    return 0


def run() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", choices=("diagnostics", "preview"), default="diagnostics")
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--sample-index", type=int, choices=range(4))
    parser.add_argument("--mode", choices=("text_audio", "voice_only"))
    args = parser.parse_args()
    if args.child:
        if args.sample_index is None or args.mode is None:
            raise SystemExit("--child requires --sample-index and --mode")
        return _child_run(sample_index=args.sample_index, mode=args.mode)
    return _parent_run(check=args.check)


if __name__ == "__main__":
    raise SystemExit(run())
