"""Strict MS33-B4 comparison-manifest and evidence-reference handling."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.cleanup_evaluation import (
    CleanupArtifactReference,
    CleanupEvaluationError,
    CleanupEvaluationRequest,
    verify_cleanup_artifact_reference,
)
from src.core.cleanup_evaluation import read_event_cleanup_policy
from src.core.event_cleanup import build_event_cleanup_policy
from src.core.final_morph_key_reduction_plan import KeyReductionPolicy
from src.core.ms33_b4c_vowel_quality import (
    B4CVowelQualityError,
    SCHEMA_ID as B4C_QUALITY_SCHEMA,
    validate_vowel_quality_record,
)


COMPARISON_SCHEMA = "ms33-b4-comparison/v2"
AUDIT_SCHEMA = "ms33-b4-check/v1"
CASE_IDS = tuple(
    f"ms33-b1-{pair:02d}-{mode}"
    for pair in range(4)
    for mode in ("ta", "vo")
)
VARIANTS = ("baseline", "keys_only", "events_only", "events_and_keys")
REQUIRED_B4_TEST_PATHS = (
    "tests/test_ms33_b4_shared_output.py",
    "tests/test_ms33_b4_lifecycle.py",
    "tests/test_ms33_b4_selection_history.py",
    "tests/test_ms33_b4_verified_save.py",
    "tests/test_ms33_b4_delivery_output.py",
    "tests/test_ms33_b4_quality_cli.py",
    "tests/test_ms33_b4c_vowel_trace.py",
    "tests/test_ms33_b4_profile_config.py",
    "tests/test_ms33_b4_technical_replay.py",
    "tests/test_wx_ms33_b4_shared_output.py",
    "tests/test_wx_ms32_b3_shared_output.py",
    "tests/test_wx_ms32_b5_default_flow.py",
    "tests/test_ms33_b2_cleanup_contract.py",
    "tests/test_ms33_b2_event_cleanup.py",
    "tests/test_ms33_b2_cleanup_projection.py",
    "tests/test_ms33_b2_check_cli.py",
    "tests/test_ms33_b3_reduction_contract.py",
    "tests/test_ms33_b3_key_reduction.py",
    "tests/test_ms33_b3_reduction_projection.py",
    "tests/test_ms33_b3_check_cli.py",
    "tests/test_ms32_b3_shared_output.py",
    "tests/test_ms32_b3_lifecycle.py",
    "tests/test_ms32_b3_analysis_binding.py",
    "tests/test_ms32_b3_diagnostics_selection.py",
    "tests/test_ms32_b3_verified_save.py",
    "tests/test_ms32_b3_delivery_output.py",
    "tests/test_ms32_b4b_shared_output.py",
    "tests/test_ms32_b5_scope_identity.py",
    "tests/test_ms21_b3_selection_commit.py",
    "tests/test_wx_ms21_b3_preview_selection.py",
    "tests/test_ms21_b6_adjustment_history.py",
    "tests/test_ms22_b4_generation_history.py",
    "tests/test_ms23_b4_profile_history.py",
    "tests/test_ms19_b5_transcription_edit_state.py",
    "tests/test_ms19_b8_workspace_reset.py",
    "tests/test_ms25_b6_delivery_failure_recovery.py",
    "tests/test_ms25_b6_delivery_gui_recovery.py",
)
B4B_TEST_PATHS = (
    "tests/test_startup_diagnostics.py",
    "tests/test_wx_startup_splash.py",
    "tests/test_ms24_b4_controller.py",
)
RUNTIME_LOCK_PATHS = (
    "src/core/startup_diagnostics.py",
    "src/core/canonical_morph_value.py",
    "src/core/cleanup_evaluation.py",
    "src/core/cleanup_quality.py",
    "src/core/cleanup_shared_output.py",
    "src/core/event_cleanup.py",
    "src/core/final_morph_capture.py",
    "src/core/final_morph_cleanup_plan.py",
    "src/core/final_morph_closure_plan.py",
    "src/core/final_morph_plan.py",
    "src/core/final_morph_key_reduction_plan.py",
    "src/core/morph_name_sets.py",
    "src/core/redundant_key_reduction.py",
    "src/core/final_output_projection.py",
    "src/core/final_output_state.py",
    "src/core/final_output_gate.py",
    "src/core/verified_vmd_save.py",
    "src/core/delivery_package.py",
    "src/core/delivery_artifacts.py",
    "src/core/preview_transform.py",
    "src/core/output_diagnostics.py",
    "src/core/diagnostic_report.py",
    "src/core/ms33_b4c_vowel_quality.py",
    "src/main.py",
    "src/vmd_writer/final_morph_closure_adapter.py",
    "src/vmd_writer/final_morph_cleanup_adapter.py",
    "src/vmd_writer/final_morph_key_reduction_adapter.py",
    "src/gui_wx/final_output_sync.py",
    "src/gui_wx/app.py",
    "src/gui_wx/app_controller.py",
    "src/gui_wx/main_frame.py",
    "src/gui_wx/right_pane.py",
    "src/gui_wx/output_diagnostics_adapter.py",
    "tools/ms33-shared-output-check.py",
    "tools/ms33-b4-technical-replay.py",
    "tools/ms33-key-reduction-check.py",
    "tools/run-ms33-cleanup-candidate.py",
    *REQUIRED_B4_TEST_PATHS,
    *B4B_TEST_PATHS,
    "tools/run-tests.ps1",
)
REQUIRED_B4B_TEST_PATHS = (*REQUIRED_B4_TEST_PATHS, *B4B_TEST_PATHS)


class CleanupQualityError(ValueError):
    """Raised when supplied B1/B3 evidence is contradictory or malformed."""


class CleanupQualityInsufficient(RuntimeError):
    """Raised when required source or evidence is unavailable."""


def _validate_b1_baseline_binding(
    actual: object,
    expected: dict[str, object],
    *,
    case_id: str,
) -> None:
    """Require the manifest's baseline bundle to match its accepted B1 source exactly."""
    if type(actual) is not dict or set(actual) != set(expected) or actual != expected:
        raise CleanupQualityError(
            f"B4 accepted B1 baseline references differ from research: {case_id}"
        )


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CleanupQualityError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise CleanupQualityError(f"non-finite JSON constant: {value}")


def _json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise CleanupQualityError("value is not canonical JSON") from error


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _file_ref(path: Path) -> dict[str, object]:
    try:
        resolved = path.resolve(strict=True)
        before = resolved.stat()
        payload = resolved.read_bytes()
        after = resolved.stat()
    except OSError as error:
        raise CleanupQualityInsufficient(f"cannot read artifact: {path}") from error
    if (
        not resolved.is_file()
        or before.st_size != after.st_size
        or getattr(before, "st_mtime_ns", None) != getattr(after, "st_mtime_ns", None)
        or len(payload) != after.st_size
    ):
        raise CleanupQualityError(f"artifact changed while it was being hashed: {path}")
    return {"path": str(resolved), "sha256": _sha256_bytes(payload), "bytes": len(payload)}


def _normalized_test_targets(value: object) -> set[str] | None:
    if type(value) is not list or not value or any(type(item) is not str for item in value):
        return None
    normalized: set[str] = set()
    for item in value:
        target = item.replace("\\", "/").strip()
        while target.startswith("./"):
            target = target[2:]
        components = target.split("/")
        if (
            not target
            or target.startswith("/")
            or ":" in target
            or any(component in {"", ".", ".."} for component in components)
        ):
            return None
        normalized.add(target.casefold())
    return normalized


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except FileNotFoundError as error:
        raise CleanupQualityInsufficient(f"required JSON is missing: {path}") from error
    except OSError as error:
        raise CleanupQualityInsufficient(f"required JSON cannot be read: {path}") from error
    except json.JSONDecodeError as error:
        raise CleanupQualityError(f"invalid JSON: {path}") from error
    if type(value) is not dict:
        raise CleanupQualityError(f"JSON root must be an object: {path}")
    return value


def _read_roots(value: object, declaring_file: Path) -> tuple[Path, ...]:
    if type(value) is not list or not value:
        raise CleanupQualityError("read_roots must be a non-empty array")
    roots: list[Path] = []
    for raw in value:
        if type(raw) is not str or not raw.strip():
            raise CleanupQualityError("read_roots entries must be non-empty paths")
        path = Path(raw)
        if not path.is_absolute():
            path = declaring_file.parent / path
        try:
            resolved = path.resolve(strict=True)
        except OSError as error:
            raise CleanupQualityInsufficient(f"read root is unavailable: {path}") from error
        if not resolved.is_dir():
            raise CleanupQualityError("read_roots entries must be directories")
        roots.append(resolved)
    return tuple(dict.fromkeys(roots))


def _within(path: Path, roots: tuple[Path, ...]) -> bool:
    return any(path == root or path.is_relative_to(root) for root in roots)


def _resolve_ref(
    value: object,
    *,
    name: str,
    declaring_file: Path,
    roots: tuple[Path, ...],
) -> tuple[Path, dict[str, object]]:
    if type(value) is not dict or set(value) != {"path", "sha256", "bytes"}:
        raise CleanupQualityError(f"{name} artifact reference fields are invalid")
    raw_path, digest, size = value["path"], value["sha256"], value["bytes"]
    if (
        type(raw_path) is not str or not raw_path
        or type(digest) is not str or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
        or isinstance(size, bool) or not isinstance(size, int) or size < 0
    ):
        raise CleanupQualityError(f"{name} artifact reference values are invalid")
    path = Path(raw_path)
    if not path.is_absolute():
        path = declaring_file.parent / path
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise CleanupQualityInsufficient(f"{name} artifact is unavailable") from error
    if not resolved.is_file() or not _within(resolved, roots):
        raise CleanupQualityError(f"{name} artifact escapes declared read_roots")
    actual = _file_ref(resolved)
    if actual["sha256"] != digest or actual["bytes"] != size:
        raise CleanupQualityError(f"{name} artifact hash or size changed")
    return resolved, actual


def _load_b3_checker(root: Path):
    path = root / "tools" / "ms33-key-reduction-check.py"
    spec = importlib.util.spec_from_file_location("ms33_b3_cleanup_quality_check", path)
    if spec is None or spec.loader is None:
        raise CleanupQualityInsufficient("MS33-B3 checker cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_b1_snapshot_decoder(root: Path):
    path = root / "tools" / "ms30-shadow-check.py"
    spec = importlib.util.spec_from_file_location("ms33_b4_b1_snapshot_decoder", path)
    if spec is None or spec.loader is None:
        raise CleanupQualityInsufficient("B1 snapshot decoder cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _decode_locked_b1_snapshot(
    *,
    full_snapshot_path: Path,
    case_id: str,
    decoder: Any,
) -> tuple[Any, Any, Any, Any, Any]:
    """Decode a frozen B1 snapshot and validate its recorded internal identities."""
    snapshot = _load_json(full_snapshot_path)
    required_fields = {
        "schema_id", "input_kind", "identity_context", "base_input",
        "adjustment_snapshot", "effective_plan_snapshot", "issuer_evidence",
    }
    input_kind = snapshot.get("input_kind")
    if (
        set(snapshot) != required_fields
        or snapshot.get("schema_id") != decoder.SNAPSHOT_SCHEMA
        or input_kind not in {"captured_snapshot", "synthetic_snapshot"}
    ):
        raise CleanupQualityError(f"B1 full snapshot fields are invalid for {case_id}")
    try:
        identity = decoder._decode_typed(
            decoder.FinalMorphIdentityContext,
            snapshot["identity_context"],
            "identity_context",
        )
        base_input = decoder._decode_base_input(snapshot["base_input"])
        adjustment = decoder._decode_typed(
            decoder.AdjustmentLayerSnapshot,
            snapshot["adjustment_snapshot"],
            "adjustment_snapshot",
        )
        effective = decoder._decode_typed(
            decoder.EffectiveShapePlan,
            snapshot["effective_plan_snapshot"],
            "effective_plan_snapshot",
        )
        evidence = decoder._decode_typed(
            decoder.FinalMorphIssuerEvidence,
            snapshot["issuer_evidence"],
            "issuer_evidence",
        )
        from src.core.effective_shape_plan import build_base_plan_identity

        base_identity = build_base_plan_identity(base_input)
        if (
            (input_kind == "synthetic_snapshot" and identity.source_run_id != f"fixture:{case_id}")
            or identity.numeric_policy_id != decoder.POLICY_ID
            or identity.base_plan_digest != base_identity.digest
            or adjustment.base_plan_identity != base_identity
            or effective.base_plan_identity != base_identity
            or effective.shape_parameters != base_input.shape_parameters
            or identity.effective_plan_digest
            != decoder.final_morph_legacy_bridge.effective_plan_snapshot_digest(effective)
        ):
            raise ValueError("recorded B1 identity differs from its captured snapshot")
        expected_evidence = decoder.capture_issuer_evidence(
            effective,
            source_run_id=identity.source_run_id,
            analysis_generation=identity.analysis_generation,
            manual_revision=identity.manual_revision,
        )
        if evidence != expected_evidence:
            raise ValueError("B1 issuer evidence differs from its captured snapshot")
    except (AttributeError, KeyError, TypeError, ValueError, RuntimeError, OverflowError) as error:
        raise CleanupQualityError(
            f"B1 full snapshot is internally inconsistent for {case_id}"
        ) from error
    return identity, base_input, adjustment, effective, evidence


def _locked_b1_base_plan_digest(
    *,
    b1_case: dict[str, Any],
    full_snapshot_path: Path,
    case_id: str,
    decoder: Any,
) -> str:
    """Return the base-input identity after checking it against B1's typed snapshot."""
    identity, _base_input, _adjustment, _effective, _evidence = _decode_locked_b1_snapshot(
        full_snapshot_path=full_snapshot_path,
        case_id=case_id,
        decoder=decoder,
    )

    source_identity = b1_case.get("source_identity")
    if type(source_identity) is not dict:
        raise CleanupQualityError(f"B1 source identity is missing for {case_id}")
    expected_identity = {
        "source_run_id": identity.source_run_id,
        "analysis_generation": identity.analysis_generation,
        "base_plan_digest": identity.base_plan_digest,
        "effective_plan_digest": identity.effective_plan_digest,
        "manual_revision": identity.manual_revision,
        "resolved_profile_id": identity.resolved_profile_id,
        "output_mapping": [list(item) for item in identity.output_mapping],
    }
    if any(source_identity.get(name) != value for name, value in expected_identity.items()):
        raise CleanupQualityError(f"B1 source identity differs from its full snapshot: {case_id}")
    return identity.base_plan_digest


def _accepted_b1_baseline_refs(
    *,
    case_id: str,
    b1_case: dict[str, Any],
    research: dict[str, Any],
    research_path: Path,
    research_ref: dict[str, object],
    audit: dict[str, Any],
    audit_ref: dict[str, object],
    full_snapshot_ref: dict[str, object],
    source_refs: dict[str, dict[str, object] | None],
    roots: tuple[Path, ...],
    decoder: Any,
) -> dict[str, object]:
    """Bind the accepted current B1 baseline artifacts to their exact source case."""
    from src.core.final_morph_capture import snapshot_digest
    from src.core.final_morph_transition_plan import (
        TransitionPlanError,
        read_final_morph_transition_plan,
    )

    if (
        research.get("schema_id") != "ms33-b1-research/v1"
        or type(research.get("run_id")) is not str
        or not research["run_id"]
        or b1_case.get("case_id") != case_id
        or b1_case.get("technical_state") != "valid"
    ):
        raise CleanupQualityError(f"B1 research run or case is invalid: {case_id}")
    research_roots = _merge_roots(roots, _read_roots(research.get("read_roots"), research_path))
    input_ref_record = CleanupArtifactReference.from_dict(research.get("input_ref")).to_dict()
    snapshot_ref = source_refs.get("full_snapshot")
    if type(snapshot_ref) is not dict:
        raise CleanupQualityError(f"B1 full snapshot reference is missing: {case_id}")
    capture_path = Path(str(snapshot_ref["path"])).parent / "capture-manifest.json"
    capture_path = capture_path.resolve(strict=True)
    if not _within(capture_path, research_roots):
        raise CleanupQualityError(f"B1 capture manifest is outside accepted read roots: {case_id}")
    capture_ref = _file_ref(capture_path)
    capture_manifest = _load_json(capture_path)
    capture_artifacts = capture_manifest.get("artifact_records")
    capture_artifact_map = (
        {row.get("role"): row for row in capture_artifacts if type(row) is dict}
        if type(capture_artifacts) is list else {}
    )
    if (
        capture_manifest.get("schema_id") != "ms31-capture-evidence/v1"
        or capture_manifest.get("case_id") != capture_path.parent.name
        or capture_manifest.get("scenario_case_id") != capture_path.parent.name
        or capture_manifest.get("input_mode") != b1_case.get("input_mode")
        or len(capture_artifact_map) != len(capture_artifacts or ())
    ):
        raise CleanupQualityError(f"B1 capture manifest does not match its accepted source: {case_id}")
    optional = b1_case.get("optional_artifacts")
    reference_result = optional.get("reference_vmd") if type(optional) is dict else None
    if type(reference_result) is not dict:
        raise CleanupQualityError(f"B1 historical reference VMD result is missing: {case_id}")
    requested_reference = reference_result.get("requested_ref")
    if requested_reference is None:
        if reference_result.get("state") not in {"not_supplied", "unavailable"}:
            raise CleanupQualityError(f"B1 historical reference VMD state is inconsistent: {case_id}")
        historical_reference: dict[str, object] | None = None
    else:
        _requested_path, requested_ref = _resolve_ref(
            requested_reference, name=f"B1 {case_id} research reference VMD",
            declaring_file=research_path, roots=research_roots,
        )
        historical_reference = requested_ref
        if (
            reference_result.get("state") != "available"
            or reference_result.get("comparison_state") not in {"performed", "unavailable"}
        ):
            raise CleanupQualityError(f"B1 historical reference VMD state is invalid: {case_id}")

    expected_case_root = research_path.parent / "cases" / case_id
    plan_path, plan_ref = _resolve_ref(
        b1_case.get("plan_ref"), name=f"B1 {case_id} baseline plan",
        declaring_file=research_path, roots=research_roots,
    )
    vmd_path, vmd_ref = _resolve_ref(
        b1_case.get("vmd_ref"), name=f"B1 {case_id} baseline VMD",
        declaring_file=research_path, roots=research_roots,
    )
    readback_path, readback_ref = _resolve_ref(
        b1_case.get("readback_ref"), name=f"B1 {case_id} baseline readback",
        declaring_file=research_path, roots=research_roots,
    )
    if (
        plan_path != (expected_case_root / "baseline-plan.json").resolve(strict=True)
        or vmd_path != (expected_case_root / "baseline.vmd").resolve(strict=True)
        or readback_path != (expected_case_root / "readback.json").resolve(strict=True)
    ):
        raise CleanupQualityError(f"B1 baseline references do not belong to the accepted run/case: {case_id}")
    try:
        plan = read_final_morph_transition_plan(plan_path.read_bytes())
    except (OSError, TransitionPlanError) as error:
        raise CleanupQualityError(f"B1 baseline plan is invalid: {case_id}") from error
    if plan.state != "valid" or plan.issues:
        raise CleanupQualityError(f"B1 baseline plan is not valid: {case_id}")

    snapshot_path = Path(str(full_snapshot_ref["path"]))
    source_identity, _base_input, adjustment, _effective, _evidence = _decode_locked_b1_snapshot(
        full_snapshot_path=snapshot_path, case_id=case_id, decoder=decoder,
    )
    capture_origin = capture_manifest.get("origin")
    capture_hashes = capture_manifest.get("input_hashes")
    if (
        type(capture_origin) is not dict
        or type(capture_hashes) is not dict
        or capture_origin.get("source_run_id") != source_identity.source_run_id
        or capture_origin.get("analysis_generation") != source_identity.analysis_generation
        or capture_origin.get("input_mode") != b1_case.get("input_mode")
        or capture_origin.get("audio_sha256") != source_refs["source_audio"]["sha256"]
        or capture_origin.get("text_sha256") != (
            None if source_refs["source_text"] is None else source_refs["source_text"]["sha256"]
        )
        or capture_manifest.get("resolved_profile_id") != source_identity.resolved_profile_id
        or capture_hashes.get("audio") != source_refs["source_audio"]["sha256"]
        or capture_hashes.get("text") != (
            None if source_refs["source_text"] is None else source_refs["source_text"]["sha256"]
        )
        or capture_manifest.get("effective_plan_digest_before_after") != source_identity.effective_plan_digest
    ):
        raise CleanupQualityError(f"B1 capture manifest identity differs from its source snapshot: {case_id}")
    for role in ("analysis_trace", "full_snapshot"):
        record = capture_artifact_map.get(role)
        if (
            type(record) is not dict
            or record.get("role") != role
            or type(record.get("path")) is not str
        ):
            raise CleanupQualityError(f"B1 capture manifest lacks its {role} artifact: {case_id}")
        artifact_path = (capture_path.parent / record["path"]).resolve(strict=True)
        if not artifact_path.is_relative_to(capture_path.parent.resolve(strict=True)):
            raise CleanupQualityError(f"B1 capture artifact escapes its case root: {case_id}/{role}")
        artifact_ref = _file_ref(artifact_path)
        if (
            artifact_ref != source_refs[role]
            or record.get("sha256") != artifact_ref["sha256"]
            or record.get("bytes") != artifact_ref["bytes"]
        ):
            raise CleanupQualityError(f"B1 capture artifact differs from its accepted source: {case_id}/{role}")
    saved_vmd_record = capture_artifact_map.get("saved_vmd")
    if historical_reference is None:
        if saved_vmd_record is not None:
            raise CleanupQualityError(f"B1 capture has an unreferenced historical VMD: {case_id}")
    else:
        if (
            type(saved_vmd_record) is not dict
            or saved_vmd_record.get("role") != "saved_vmd"
            or type(saved_vmd_record.get("path")) is not str
        ):
            raise CleanupQualityError(f"B1 capture lacks its accepted historical VMD: {case_id}")
        saved_vmd_path = (capture_path.parent / saved_vmd_record["path"]).resolve(strict=True)
        saved_vmd_ref = _file_ref(saved_vmd_path)
        if (
            not saved_vmd_path.is_relative_to(capture_path.parent.resolve(strict=True))
            or saved_vmd_ref != historical_reference
            or saved_vmd_record.get("sha256") != saved_vmd_ref["sha256"]
            or saved_vmd_record.get("bytes") != saved_vmd_ref["bytes"]
        ):
            raise CleanupQualityError(f"B1 historical VMD differs from its original capture: {case_id}")
    lineage = plan.identity_context.source_lineage
    settings = b1_case.get("settings")
    policy = settings.get("policy") if type(settings) is dict else None
    if type(policy) is not dict:
        raise CleanupQualityError(f"B1 baseline policy identity is missing: {case_id}")
    if (
        plan.identity_context.baseline_effective_digest != lineage.effective_plan_digest
        or plan.identity_context.policy_digest != lineage.policy_digest
        or lineage.source_kind != "replayed_capture"
        or lineage.origin_kind != "captured_snapshot"
        or lineage.run_id != source_identity.source_run_id
        or lineage.origin_identity != f"{source_identity.source_run_id}/{source_identity.analysis_generation}"
        or lineage.analysis_generation != str(source_identity.analysis_generation)
        or type(lineage.resolved_profile_id) is not str
        or not lineage.resolved_profile_id
        or lineage.input_mode != b1_case.get("input_mode")
        or lineage.analysis_wav_sha256 != source_refs["analysis_wav"]["sha256"]
        or lineage.original_source_sha256 != full_snapshot_ref["sha256"]
        or lineage.capture_manifest_sha256 != capture_ref["sha256"]
        or lineage.base_plan_digest != source_identity.base_plan_digest
        or lineage.manual_revision != source_identity.manual_revision
        or lineage.manual_snapshot_digest != snapshot_digest(adjustment)
        or tuple(lineage.output_mapping) != tuple(source_identity.output_mapping)
        or lineage.current_runtime_sha256 != b1_case.get("runtime_digest")
        or lineage.current_runtime_sha256 != research.get("runtime_digest")
        or lineage.policy_digest != policy.get("policy_digest")
        or policy.get("policy_id") != "ms32-cross-vowel-transition/evaluation-v2"
        or settings.get("analysis_wav_digest") != source_refs["analysis_wav"]["sha256"]
        or settings.get("source_audio_digest") != source_refs["source_audio"]["sha256"]
        or settings.get("source_text_digest") != (
            None if source_refs["source_text"] is None else source_refs["source_text"]["sha256"]
        )
        or plan.identity_context.acoustic_digest != settings.get("acoustic_digest")
        or lineage.acoustic_evidence_digest != settings.get("acoustic_digest")
    ):
        raise CleanupQualityError(f"B1 current baseline identity differs from its accepted input: {case_id}")

    readback = _load_json(readback_path)
    if (
        readback.get("schema_id") != "ms33-b1-readback/v1"
        or readback.get("status") != "passed"
        or readback.get("plan_digest") != plan.semantic_digest
        or readback.get("wire_digest") != plan.identity_context.closure_wire_digest
        or type(readback.get("projection_digest")) is not str
        or type(readback.get("verified_transition_count")) is not int
        or type(readback.get("measurements")) is not list
        or readback.get("verified_transition_count") != len(readback.get("measurements", ()))
    ):
        raise CleanupQualityError(f"B1 baseline readback does not match its plan: {case_id}")

    return {
        "case_id": case_id,
        "research_run_id": research["run_id"],
        "research_input_ref_record": input_ref_record,
        "capture_manifest_ref": capture_ref,
        "historical_reference_vmd_ref": historical_reference,
        "plan_ref": plan_ref,
        "vmd_ref": vmd_ref,
        "readback_ref": readback_ref,
        "baseline_effective_digest": lineage.effective_plan_digest,
        "policy_id": policy["policy_id"],
        "policy_digest": policy["policy_digest"],
        "runtime_digest": lineage.current_runtime_sha256,
        "resolved_profile_id": lineage.resolved_profile_id,
        "research_ref": research_ref,
        "audit_ref": audit_ref,
    }


def _merge_roots(*roots: tuple[Path, ...]) -> tuple[Path, ...]:
    return tuple(dict.fromkeys(path for group in roots for path in group))


def _source_lock(root: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for relative in RUNTIME_LOCK_PATHS:
        path = root / relative
        if not path.is_file():
            raise CleanupQualityInsufficient(f"B4 runtime source is missing: {relative}")
        ref = _file_ref(path)
        result.append({"path": relative, "sha256": ref["sha256"], "bytes": ref["bytes"]})
    return result


def _case_map(rows: object, *, label: str) -> dict[str, dict[str, Any]]:
    if type(rows) is not list or len(rows) != len(CASE_IDS) or any(type(row) is not dict for row in rows):
        raise CleanupQualityError(f"{label} must contain exactly eight cases")
    result = {row.get("case_id"): row for row in rows}
    if tuple(case_id for case_id in CASE_IDS if case_id in result) != CASE_IDS or len(result) != len(CASE_IDS):
        raise CleanupQualityError(f"{label} case IDs differ from the locked B1 matrix")
    return result


def _profile_config_bundle(
    profile_config_directory: Path,
    *,
    cases: list[dict[str, object]],
    declaring_file: Path | None = None,
    roots: tuple[Path, ...] | None = None,
) -> tuple[dict[str, dict[str, object]], tuple[Path, ...]]:
    """Bind profile and preset files used to replay accepted B1 profile IDs."""
    directory = profile_config_directory.resolve(strict=True)
    profiles_path = (directory / "profiles.json").resolve(strict=True)
    presets_path = (directory / "presets.json").resolve(strict=True)
    if profiles_path.parent != directory or presets_path.parent != directory:
        raise CleanupQualityError("profile configuration files must be directly inside their declared directory")

    profiles_document = _load_json(profiles_path)
    presets_document = _load_json(presets_path)
    user_profiles = profiles_document.get("user_profiles")
    user_presets = presets_document.get("user_presets")
    if (
        profiles_document.get("schema_version") != 1
        or type(user_profiles) is not list
        or presets_document.get("schema_version") != 1
        or type(user_presets) is not list
    ):
        raise CleanupQualityError("profile configuration files do not match the version 1 store schema")

    required_profile_ids: set[str] = set()
    for case in cases:
        baseline = case.get("b1_baseline") if type(case) is dict else None
        profile_id = baseline.get("resolved_profile_id") if type(baseline) is dict else None
        if type(profile_id) is not str or not profile_id:
            raise CleanupQualityError("accepted B1 baseline lacks a model profile identity")
        required_profile_ids.add(profile_id)
    if not required_profile_ids:
        raise CleanupQualityError("accepted B1 baselines do not declare model profile identities")
    stored_profile_ids = {
        profile.get("id")
        for profile in user_profiles
        if type(profile) is dict and type(profile.get("id")) is str
    }
    if not required_profile_ids.issubset(stored_profile_ids):
        raise CleanupQualityError("profile configuration does not define every accepted B1 model profile")

    roots_result = tuple(dict.fromkeys((*(roots or ()), directory)))
    if declaring_file is None:
        refs = {
            "profiles_ref": _file_ref(profiles_path),
            "presets_ref": _file_ref(presets_path),
        }
    else:
        if roots is None:
            raise ValueError("read roots are required when verifying a profile configuration bundle")
        _profiles_path, profiles_ref = _resolve_ref(
            _file_ref(profiles_path),
            name="model profile configuration",
            declaring_file=declaring_file,
            roots=roots_result,
        )
        _presets_path, presets_ref = _resolve_ref(
            _file_ref(presets_path),
            name="generation preset configuration",
            declaring_file=declaring_file,
            roots=roots_result,
        )
        refs = {"profiles_ref": profiles_ref, "presets_ref": presets_ref}
    return refs, roots_result


def _verify_profile_config_bundle(
    value: object,
    *,
    cases: list[dict[str, object]],
    declaring_file: Path,
    roots: tuple[Path, ...],
) -> tuple[Path, Path] | None:
    if value is None:
        return None
    if type(value) is not dict or set(value) != {"profiles_ref", "presets_ref"}:
        raise CleanupQualityError("B4 profile configuration bundle references are malformed")
    profiles_path, _profiles_ref = _resolve_ref(
        value["profiles_ref"],
        name="model profile configuration",
        declaring_file=declaring_file,
        roots=roots,
    )
    presets_path, _presets_ref = _resolve_ref(
        value["presets_ref"],
        name="generation preset configuration",
        declaring_file=declaring_file,
        roots=roots,
    )
    if (
        profiles_path.name != "profiles.json"
        or presets_path.name != "presets.json"
        or profiles_path.parent != presets_path.parent
    ):
        raise CleanupQualityError("B4 profile and preset references do not form one configuration bundle")

    profiles_document = _load_json(profiles_path)
    presets_document = _load_json(presets_path)
    user_profiles = profiles_document.get("user_profiles")
    user_presets = presets_document.get("user_presets")
    if (
        profiles_document.get("schema_version") != 1
        or type(user_profiles) is not list
        or presets_document.get("schema_version") != 1
        or type(user_presets) is not list
    ):
        raise CleanupQualityError("B4 profile configuration files do not match the version 1 store schema")
    required_profile_ids: set[str] = set()
    for case in cases:
        baseline = case.get("b1_baseline") if type(case) is dict else None
        profile_id = baseline.get("resolved_profile_id") if type(baseline) is dict else None
        if type(profile_id) is not str or not profile_id:
            raise CleanupQualityError("accepted B1 baseline lacks a model profile identity")
        required_profile_ids.add(profile_id)
    if not required_profile_ids:
        raise CleanupQualityError("accepted B1 baselines do not declare model profile identities")
    stored_profile_ids = {
        profile.get("id")
        for profile in user_profiles
        if type(profile) is dict and type(profile.get("id")) is str
    }
    if not required_profile_ids.issubset(stored_profile_ids):
        raise CleanupQualityError("B4 profile bundle does not define every accepted B1 model profile")
    return profiles_path, presets_path


def prepare_comparison_manifest(
    *,
    b3_audit_path: Path,
    output_root: Path,
    repository_root: Path,
    profile_config_directory: Path | None = None,
) -> tuple[Path, dict[str, object]]:
    """Validate G33-03 and prepare a source-locked, explicitly incomplete B4 manifest."""
    audit_path = b3_audit_path.resolve(strict=True)
    b3_audit = _load_json(audit_path)
    audit_roots = _read_roots(b3_audit.get("read_roots"), audit_path)
    if (
        b3_audit.get("schema_id") != "ms33-b3-check/v1"
        or b3_audit.get("g33_03") != "established"
        or b3_audit.get("exit_code") != 0
        or b3_audit.get("standalone_state") != "accepted"
        or b3_audit.get("combined_state") != "accepted"
        or b3_audit.get("issues") != []
        or b3_audit.get("insufficient") != []
    ):
        raise CleanupQualityInsufficient("the supplied B3 audit does not establish G33-03")
    if not _within(audit_path, audit_roots):
        raise CleanupQualityError("B3 audit is outside its declared read_roots")

    b3_audit_ref = _file_ref(audit_path)
    lock_path, lock_ref = _resolve_ref(
        b3_audit.get("lock_ref"), name="B3 contract lock", declaring_file=audit_path,
        roots=audit_roots,
    )
    standalone_path, standalone_ref = _resolve_ref(
        b3_audit.get("standalone_results_ref"), name="B3 standalone results",
        declaring_file=audit_path, roots=audit_roots,
    )
    combined_path, combined_ref = _resolve_ref(
        b3_audit.get("combined_results_ref"), name="B3 combined results",
        declaring_file=audit_path, roots=audit_roots,
    )
    b3_checker = _load_b3_checker(repository_root)
    lock, contract, b1_audit, research, lock_roots, key_policy = b3_checker._read_lock(lock_path)
    if lock_ref != b3_audit.get("lock_ref"):
        raise CleanupQualityError("B3 contract lock reference changed")
    roots = _merge_roots(audit_roots, lock_roots)
    standalone = _load_json(standalone_path)
    combined = _load_json(combined_path)
    if (
        standalone.get("schema_id") != "ms33-b3-results/v1"
        or standalone.get("technical_state") != "valid"
        or standalone.get("valid_case_count") != len(CASE_IDS)
        or combined.get("schema_id") != "ms33-b3-results/v1"
        or combined.get("technical_state") != "valid"
        or combined.get("valid_case_count") != len(CASE_IDS)
    ):
        raise CleanupQualityError("B3 result files do not match the accepted audit")
    standalone_cases = _case_map(standalone.get("cases"), label="B3 standalone cases")
    combined_cases = _case_map(combined.get("cases"), label="B3 combined cases")

    b2_refs = combined.get("b2_refs")
    if type(b2_refs) is not dict or set(b2_refs) != {"audit", "results"}:
        raise CleanupQualityError("B3 combined results lack the B2 handoff")
    b2_results_path, b2_results_ref = _resolve_ref(
        b2_refs["results"], name="B2 results", declaring_file=combined_path, roots=roots,
    )
    b2_audit_path, b2_audit_ref = _resolve_ref(
        b2_refs["audit"], name="B2 audit", declaring_file=combined_path, roots=roots,
    )
    b2_results = _load_json(b2_results_path)
    b2_audit_doc = _load_json(b2_audit_path)
    if (
        b2_results.get("schema_id") != "ms33-b2-results/v1"
        or b2_audit_doc.get("schema_id") != "ms33-b2-check/v1"
        or b2_audit_doc.get("g33_02") != "established"
        or b2_audit_doc.get("exit_code") != 0
        or b2_audit_doc.get("results_ref") != b2_refs["results"]
        or b2_audit_doc.get("issues") != []
        or b2_audit_doc.get("insufficient") != []
    ):
        raise CleanupQualityError("B2 handoff is not currently valid")
    b2_cases = _case_map(b2_results.get("cases"), label="B2 cases")
    if b2_audit_doc.get("application_result") != b2_results.get("application_result"):
        raise CleanupQualityError("B2 result and audit application states differ")

    b1_refs = lock.get("b1_refs")
    if type(b1_refs) is not dict or set(b1_refs) != {"contract", "audit", "research"}:
        raise CleanupQualityError("B3 lock does not carry the expected B1 evidence")
    contract_path, contract_ref = _resolve_ref(
        b1_refs["contract"], name="B1 contract", declaring_file=lock_path, roots=roots,
    )
    b1_audit_path, b1_audit_ref = _resolve_ref(
        b1_refs["audit"], name="B1 audit", declaring_file=lock_path, roots=roots,
    )
    research_path, research_ref = _resolve_ref(
        b1_refs["research"], name="B1 research", declaring_file=lock_path, roots=roots,
    )
    if contract.get("schema_id") != "ms33-b1-contract/v1":
        raise CleanupQualityError("B1 contract schema is invalid")
    event_contract = contract.get("event_contract")
    if type(event_contract) is not dict or event_contract.get("status") != "adopted":
        raise CleanupQualityInsufficient("B1 event contract is not adopted")
    key_contract = contract.get("key_contract")
    if type(key_contract) is not dict or key_contract.get("status") != "adopted":
        raise CleanupQualityInsufficient("B1 key contract is not adopted")
    comparison_path, comparison_ref = _resolve_ref(
        event_contract.get("comparison_ref"), name="B1 event comparison",
        declaring_file=contract_path, roots=roots,
    )
    audit_research_path, audit_research_ref = _resolve_ref(
        b1_audit.get("input_refs", {}).get("research")
        if type(b1_audit.get("input_refs")) is dict else None,
        name="B1 audit research input", declaring_file=b1_audit_path, roots=roots,
    )
    if audit_research_path != research_path or audit_research_ref != research_ref:
        raise CleanupQualityError("B1 accepted audit does not bind the supplied research run")
    b1_acceptance = b1_audit.get("acceptance")
    b1_gates = b1_audit.get("gates")
    gate_states = {
        row.get("gate_id"): row.get("status")
        for row in b1_gates if type(row) is dict
    } if type(b1_gates) is list else {}
    if (
        b1_audit.get("schema_id") != "ms33-b1-contract-check/v1"
        or type(b1_acceptance) is not dict
        or gate_states.get("G33-00") != "established"
        or gate_states.get("G33-01") != "established"
        or gate_states.get("G33-01K") != "established"
        or b1_acceptance.get("G33-01") != "established"
        or b1_acceptance.get("G33-01K") != "established"
        or b1_acceptance.get("b1") != "complete"
        or b1_audit.get("exit_code") != 0
        or b1_audit.get("issues") != []
        or b1_audit.get("insufficient") != []
        or research.get("schema_id") != "ms33-b1-research/v1"
        or research.get("status") != "complete"
    ):
        raise CleanupQualityInsufficient("B1 audit and research do not establish an accepted complete baseline")

    event_policy = build_event_cleanup_policy(
        contract,
        contract_digest=contract_ref["sha256"],
        comparison_digest=comparison_ref["sha256"],
    )
    if key_policy.to_dict() != lock.get("policy"):
        raise CleanupQualityError("B3 locked policy differs from the checked source")
    policy = KeyReductionPolicy(
        policy_id=lock["policy"]["policy_id"],
        key_contract_digest=lock["policy"]["key_contract_digest"],
        protections=tuple(lock["policy"]["protections"]),
        curve_domains=tuple(lock["policy"]["curve_domains"]),
        algorithm_id=lock["policy"]["algorithm_id"],
        enabled=lock["policy"]["enabled"],
        policy_digest=lock["policy"]["policy_digest"],
        schema_id=lock["policy"]["schema_id"],
    )
    research_cases = _case_map(research.get("cases"), label="B1 research cases")
    if research_path.resolve(strict=True) != Path(research_ref["path"]).resolve(strict=True):
        raise CleanupQualityError("B1 research reference changed")
    b1_snapshot_decoder = _load_b1_snapshot_decoder(repository_root)

    cases: list[dict[str, object]] = []
    for case_id in CASE_IDS:
        b2_case = b2_cases[case_id]
        b3_solo = standalone_cases[case_id]
        b3_combined = combined_cases[case_id]
        b1_case = research_cases[case_id]
        if (
            b2_case.get("technical_state") != "valid"
            or b2_case.get("issues") != []
            or b3_solo.get("technical_state") != "valid"
            or b3_solo.get("readback_status") != "passed"
            or b3_solo.get("issues") != []
            or b3_combined.get("technical_state") != "valid"
            or b3_combined.get("readback_status") != "passed"
            or b3_combined.get("issues") != []
            or b1_case.get("technical_state") != "valid"
        ):
            raise CleanupQualityError(f"upstream evidence is invalid for {case_id}")
        raw_source_refs = b1_case.get("source_refs")
        if type(raw_source_refs) is not dict or set(raw_source_refs) != {
            "analysis_trace", "analysis_wav", "full_snapshot", "source_audio", "source_text"
        }:
            raise CleanupQualityError(f"B1 source references are incomplete for {case_id}")
        source_refs: dict[str, dict[str, object] | None] = {}
        for role, value in raw_source_refs.items():
            if value is None:
                if role != "source_text" or b1_case.get("input_mode") != "voice_only":
                    raise CleanupQualityError(f"unexpected missing {role} source for {case_id}")
                source_refs[role] = None
                continue
            _resolved, ref = _resolve_ref(
                value, name=f"{case_id} {role}", declaring_file=research_path, roots=roots,
            )
            source_refs[role] = ref
        base_plan_digest = _locked_b1_base_plan_digest(
            b1_case=b1_case,
            full_snapshot_path=Path(source_refs["full_snapshot"]["path"]),
            case_id=case_id,
            decoder=b1_snapshot_decoder,
        )
        b1_baseline = _accepted_b1_baseline_refs(
            case_id=case_id,
            b1_case=b1_case,
            research=research,
            research_path=research_path,
            research_ref=research_ref,
            audit_ref=b1_audit_ref,
            audit=b1_audit,
            full_snapshot_ref=source_refs["full_snapshot"],
            source_refs=source_refs,
            roots=roots,
            decoder=b1_snapshot_decoder,
        )

        variant_sources = {
            "baseline": (b1_baseline["vmd_ref"], b1_baseline["plan_ref"], source_refs["full_snapshot"], "b1_accepted_baseline", []),
            "keys_only": (b3_solo.get("candidate_vmd_ref"), b3_solo.get("plan_ref"), b3_solo.get("input_ref"), "b3_standalone_reference", b3_solo.get("curve_checks", [])),
            "events_only": (b2_case.get("candidate_vmd_ref"), b2_case.get("plan_ref"), b2_case.get("input_ref"), "b2_event_reference", []),
            "events_and_keys": (b3_combined.get("candidate_vmd_ref"), b3_combined.get("plan_ref"), b3_combined.get("input_ref"), "b3_combined_reference", b3_combined.get("curve_checks", [])),
        }
        _b2_baseline_path, b2_baseline_ref = _resolve_ref(
            b2_case.get("baseline_vmd_ref"), name=f"{case_id} B2 baseline VMD",
            declaring_file=b2_results_path, roots=roots,
        )
        if (
            b2_baseline_ref["sha256"] != b1_baseline["vmd_ref"]["sha256"]
            or b2_baseline_ref["bytes"] != b1_baseline["vmd_ref"]["bytes"]
        ):
            raise CleanupQualityError(f"B2 baseline VMD differs from accepted B1 baseline: {case_id}")
        variants: dict[str, object] = {}
        for variant, (vmd_value, plan_value, input_value, origin, curve_checks) in variant_sources.items():
            vmd_path, vmd_ref = _resolve_ref(
                vmd_value, name=f"{case_id}/{variant} VMD", declaring_file=combined_path, roots=roots,
            )
            plan_path, plan_ref = _resolve_ref(
                plan_value, name=f"{case_id}/{variant} plan", declaring_file=combined_path, roots=roots,
            )
            input_path, input_ref = _resolve_ref(
                input_value, name=f"{case_id}/{variant} input", declaring_file=combined_path, roots=roots,
            )
            variants[variant] = {
                "origin": origin,
                "state": "upstream_reference_only",
                "candidate_vmd_ref": vmd_ref,
                "plan_ref": plan_ref,
                "input_ref": input_ref,
                "upstream_readback": "passed" if variant in {"baseline", "keys_only", "events_and_keys"} else "B4_readback_not_performed",
                "curve_checks": curve_checks,
            }
        cases.append({
            "case_id": case_id,
            "input_mode": b1_case.get("input_mode"),
            "base_plan_digest": base_plan_digest,
            "source_refs": source_refs,
            "b1_baseline": b1_baseline,
            "variants": variants,
        })

    profile_config_refs: dict[str, dict[str, object]] | None = None
    if profile_config_directory is not None:
        profile_config_refs, roots = _profile_config_bundle(
            profile_config_directory,
            cases=cases,
            roots=roots,
        )

    resolved_output = output_root.resolve(strict=False)
    if resolved_output.exists():
        raise CleanupQualityError("B4 comparison output root already exists")
    if any(resolved_output == root or resolved_output.is_relative_to(root) or root.is_relative_to(resolved_output) for root in roots):
        raise CleanupQualityError("B4 comparison output root overlaps its read roots")
    output_read_roots = tuple(dict.fromkeys((*roots, resolved_output)))
    document: dict[str, object] = {
        "schema_id": COMPARISON_SCHEMA,
        "read_roots": [str(path) for path in output_read_roots],
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "origin": "upstream_evidence_seed",
        "g33_03": "established",
        "b1_refs": {
            "contract": contract_ref,
            "audit": b1_audit_ref,
            "research": research_ref,
            "event_comparison": comparison_ref,
        },
        "b3_audit_ref": b3_audit_ref,
        "b2_refs": {"audit": b2_audit_ref, "results": b2_results_ref},
        "policies": {"event": event_policy.to_dict(), "key": policy.to_dict()},
        "upstream_states": {
            "b2_application_result": b2_results.get("application_result"),
            "b3_standalone_state": b3_audit.get("standalone_state"),
            "b3_combined_state": b3_audit.get("combined_state"),
        },
        "runtime_lock": _source_lock(repository_root),
        "profile_config_bundle": profile_config_refs,
        "case_ids": list(CASE_IDS),
        "cases": cases,
        "b4_state": "prepared_for_candidate_sessions",
        "technical_state": "not_performed",
        "live_state": "not_performed",
        "gui_state": "not_performed",
        "quality_state": "not_performed",
        "issues": [],
        "insufficient": [
            "B4 shared consumer replay and individual/delivery readback have not been performed",
            "TA/VO candidate GUI sessions have not been recorded",
            "GUI and MMD quality evidence have not been supplied",
        ],
    }
    output_root.mkdir(parents=True, exist_ok=False)
    manifest_path = output_root / "comparison.json"
    payload = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False).encode("utf-8") + b"\n"
    try:
        with manifest_path.open("xb") as stream:
            stream.write(payload)
    except OSError as error:
        raise CleanupQualityInsufficient(f"cannot create B4 comparison manifest: {manifest_path}") from error
    return manifest_path, document


def _verify_manifest(path: Path, repository_root: Path) -> tuple[dict[str, Any], tuple[Path, ...]]:
    manifest_path = path.resolve(strict=True)
    manifest = _load_json(manifest_path)
    roots = _read_roots(manifest.get("read_roots"), manifest_path)
    manifest_fields = {
        "schema_id", "read_roots", "created_at_utc", "origin", "g33_03",
        "b1_refs", "b3_audit_ref", "b2_refs", "policies", "upstream_states",
        "runtime_lock", "profile_config_bundle", "case_ids", "cases", "b4_state", "technical_state",
        "live_state", "gui_state", "quality_state", "issues", "insufficient",
    }
    if set(manifest) != manifest_fields or manifest.get("origin") != "upstream_evidence_seed":
        raise CleanupQualityError("B4 comparison seed fields or origin are invalid")
    if manifest.get("schema_id") != COMPARISON_SCHEMA or not _within(manifest_path, roots):
        raise CleanupQualityError("B4 comparison schema or root binding is invalid")
    _verify_profile_config_bundle(
        manifest.get("profile_config_bundle"),
        cases=manifest.get("cases") if type(manifest.get("cases")) is list else [],
        declaring_file=manifest_path,
        roots=roots,
    )
    if manifest.get("g33_03") != "established" or manifest.get("b4_state") != "prepared_for_candidate_sessions":
        raise CleanupQualityInsufficient("B4 comparison is not prepared from an established G33-03 audit")
    if manifest.get("technical_state") != "not_performed":
        raise CleanupQualityError("comparison seed cannot claim B4 technical validation without replay evidence")
    if (
        manifest.get("live_state") != "not_performed"
        or manifest.get("gui_state") != "not_performed"
        or manifest.get("quality_state") != "not_performed"
        or manifest.get("issues") != []
        or type(manifest.get("insufficient")) is not list
        or not manifest.get("insufficient")
    ):
        raise CleanupQualityError("comparison seed state fields are inconsistent")
    if manifest.get("case_ids") != list(CASE_IDS):
        raise CleanupQualityError("B4 comparison case matrix differs from the locked eight cases")
    lock = manifest.get("runtime_lock")
    if type(lock) is not list or len(lock) != len(RUNTIME_LOCK_PATHS):
        raise CleanupQualityError("B4 runtime lock is incomplete")
    locked: dict[str, dict[str, object]] = {}
    for row in lock:
        if type(row) is not dict or set(row) != {"path", "sha256", "bytes"}:
            raise CleanupQualityError("B4 runtime lock row is malformed")
        relative = row["path"]
        if type(relative) is not str or relative in locked:
            raise CleanupQualityError("B4 runtime lock contains an invalid or duplicate path")
        locked[relative] = row
    if tuple(locked) != RUNTIME_LOCK_PATHS:
        raise CleanupQualityError("B4 runtime lock path set differs from the implementation contract")
    current_lock = _source_lock(repository_root)
    if current_lock != lock:
        raise CleanupQualityError("B4 runtime source changed after comparison preparation")

    b1_refs = manifest.get("b1_refs")
    b2_refs = manifest.get("b2_refs")
    if type(b1_refs) is not dict or set(b1_refs) != {
        "contract", "audit", "research", "event_comparison"
    }:
        raise CleanupQualityError("B4 comparison B1 references are malformed")
    if type(b2_refs) is not dict or set(b2_refs) != {"audit", "results"}:
        raise CleanupQualityError("B4 comparison B2 references are malformed")
    for name, value in (*b1_refs.items(), *b2_refs.items()):
        verify_cleanup_artifact_reference(
            CleanupArtifactReference.from_dict(value), roots
        )
    b1_audit_path = Path(CleanupArtifactReference.from_dict(b1_refs["audit"]).path)
    b1_audit_doc = _load_json(b1_audit_path)
    research_path = Path(CleanupArtifactReference.from_dict(b1_refs["research"]).path)
    research = _load_json(research_path)
    research_ref = _file_ref(research_path)
    research_input_ref_record = CleanupArtifactReference.from_dict(
        research.get("input_ref")
    ).to_dict()
    audit_research_path, audit_research_ref = _resolve_ref(
        b1_audit_doc.get("input_refs", {}).get("research")
        if type(b1_audit_doc.get("input_refs")) is dict else None,
        name="B1 audit research input", declaring_file=b1_audit_path, roots=roots,
    )
    if (
        audit_research_path != research_path
        or audit_research_ref != research_ref
    ):
        raise CleanupQualityError("B1 audit, research, and input manifest references disagree")
    b1_acceptance = b1_audit_doc.get("acceptance")
    b1_gates = b1_audit_doc.get("gates")
    gate_states = {
        row.get("gate_id"): row.get("status")
        for row in b1_gates if type(row) is dict
    } if type(b1_gates) is list else {}
    if (
        b1_audit_doc.get("schema_id") != "ms33-b1-contract-check/v1"
        or type(b1_acceptance) is not dict
        or b1_acceptance.get("b1") != "complete"
        or b1_acceptance.get("G33-01") != "established"
        or b1_acceptance.get("G33-01K") != "established"
        or gate_states.get("G33-00") != "established"
        or gate_states.get("G33-01") != "established"
        or gate_states.get("G33-01K") != "established"
        or b1_audit_doc.get("exit_code") != 0
        or b1_audit_doc.get("issues") != []
        or b1_audit_doc.get("insufficient") != []
        or research.get("schema_id") != "ms33-b1-research/v1"
        or research.get("status") != "complete"
    ):
        raise CleanupQualityInsufficient("B1 audit and research no longer establish an accepted baseline")
    b3_audit_ref = CleanupArtifactReference.from_dict(manifest.get("b3_audit_ref"))
    b3_audit_path = verify_cleanup_artifact_reference(b3_audit_ref, roots)
    b3_audit = _load_json(b3_audit_path)
    if (
        b3_audit.get("schema_id") != "ms33-b3-check/v1"
        or b3_audit.get("g33_03") != "established"
        or b3_audit.get("exit_code") != 0
        or b3_audit.get("standalone_state") != "accepted"
        or b3_audit.get("combined_state") != "accepted"
        or b3_audit.get("issues") != []
        or b3_audit.get("insufficient") != []
    ):
        raise CleanupQualityInsufficient("B3 audit no longer establishes G33-03")
    b3_roots = _merge_roots(roots, _read_roots(b3_audit.get("read_roots"), b3_audit_path))
    b3_lock_path, _ = _resolve_ref(
        b3_audit.get("lock_ref"), name="B3 lock", declaring_file=b3_audit_path,
        roots=b3_roots,
    )
    b3_checker = _load_b3_checker(repository_root)
    lock_doc, contract, _audit, _research, _lock_roots, key_policy = b3_checker._read_lock(b3_lock_path)
    if lock_doc.get("b1_refs") is None:
        raise CleanupQualityError("B3 lock has no complete B1 reference set")
    if key_policy.to_dict() != manifest.get("policies", {}).get("key"):
        raise CleanupQualityError("B4 key policy differs from the G33-03 locked policy")
    contract_ref = CleanupArtifactReference.from_dict(b1_refs["contract"])
    comparison_ref = CleanupArtifactReference.from_dict(b1_refs["event_comparison"])
    contract_digest = _file_ref(Path(contract_ref.path))["sha256"]
    comparison_digest = _file_ref(Path(comparison_ref.path))["sha256"]
    event_policy = build_event_cleanup_policy(
        contract,
        contract_digest=contract_digest,
        comparison_digest=comparison_digest,
    )
    if event_policy.to_dict() != manifest.get("policies", {}).get("event"):
        raise CleanupQualityError("B4 event policy differs from the adopted B1 contract")

    b3_lock_refs = lock_doc.get("b1_refs")
    for manifest_name, lock_name in (
        ("contract", "contract"), ("audit", "audit"), ("research", "research"),
    ):
        _expected_path, expected_ref = _resolve_ref(
            b3_lock_refs.get(lock_name), name=f"B3 locked B1 {lock_name}",
            declaring_file=b3_lock_path, roots=b3_roots,
        )
        if b1_refs[manifest_name] != expected_ref:
            raise CleanupQualityError(f"B4 {manifest_name} reference differs from the current B3 lock")
    event_contract = contract.get("event_contract")
    if type(event_contract) is not dict:
        raise CleanupQualityError("B1 event contract is missing from the adopted contract")
    _event_comparison_path, event_comparison_ref = _resolve_ref(
        event_contract.get("comparison_ref"), name="B1 event comparison",
        declaring_file=Path(CleanupArtifactReference.from_dict(b1_refs["contract"]).path),
        roots=b3_roots,
    )
    if b1_refs["event_comparison"] != event_comparison_ref:
        raise CleanupQualityError("B4 event comparison reference differs from the adopted B1 contract")

    research_cases = _case_map(research.get("cases"), label="B1 research cases")
    b1_snapshot_decoder = _load_b1_snapshot_decoder(repository_root)

    b3_standalone_path, _ = _resolve_ref(
        b3_audit.get("standalone_results_ref"), name="B3 standalone results",
        declaring_file=b3_audit_path, roots=b3_roots,
    )
    b3_combined_path, _ = _resolve_ref(
        b3_audit.get("combined_results_ref"), name="B3 combined results",
        declaring_file=b3_audit_path, roots=b3_roots,
    )
    b3_standalone = _load_json(b3_standalone_path)
    b3_combined = _load_json(b3_combined_path)
    if (
        b3_standalone.get("schema_id") != "ms33-b3-results/v1"
        or b3_standalone.get("technical_state") != "valid"
        or b3_standalone.get("valid_case_count") != len(CASE_IDS)
        or b3_combined.get("schema_id") != "ms33-b3-results/v1"
        or b3_combined.get("technical_state") != "valid"
        or b3_combined.get("valid_case_count") != len(CASE_IDS)
    ):
        raise CleanupQualityInsufficient("B3 standalone/combined result set is no longer valid")
    b3_raw_b2_refs = b3_combined.get("b2_refs")
    if type(b3_raw_b2_refs) is not dict or set(b3_raw_b2_refs) != {"audit", "results"}:
        raise CleanupQualityError("B3 combined results have malformed B2 references")
    for ref_name in ("audit", "results"):
        _b3_b2_path, b3_b2_ref = _resolve_ref(
            b3_raw_b2_refs[ref_name], name=f"B3 combined B2 {ref_name}",
            declaring_file=b3_combined_path, roots=b3_roots,
        )
        if b3_b2_ref != b2_refs[ref_name]:
            raise CleanupQualityError(f"B4 B2 {ref_name} reference differs from B3 combined results")
    b3_standalone_cases = _case_map(b3_standalone.get("cases"), label="B3 standalone cases")
    b3_combined_cases = _case_map(b3_combined.get("cases"), label="B3 combined cases")
    for case_id in CASE_IDS:
        for variant, case_result in (
            ("keys_only", b3_standalone_cases[case_id]),
            ("events_and_keys", b3_combined_cases[case_id]),
        ):
            if (
                case_result.get("technical_state") != "valid"
                or case_result.get("readback_status") != "passed"
                or case_result.get("issues") != []
            ):
                raise CleanupQualityInsufficient(f"B3 {variant} result is not valid for {case_id}")
    b2_results_path, b2_results_actual = _resolve_ref(
        b2_refs["results"], name="B2 results", declaring_file=b3_combined_path, roots=b3_roots,
    )
    b2_audit_path, b2_audit_actual = _resolve_ref(
        b2_refs["audit"], name="B2 audit", declaring_file=b3_combined_path, roots=b3_roots,
    )
    if b2_audit_actual != manifest["b2_refs"]["audit"] or b2_results_actual != manifest["b2_refs"]["results"]:
        raise CleanupQualityError("B4 B2 references differ from their current artifacts")
    b2_audit = _load_json(b2_audit_path)
    _b2_results_from_audit, b2_audit_results_ref = _resolve_ref(
        b2_audit.get("results_ref"), name="B2 audit results", declaring_file=b2_audit_path,
        roots=b3_roots,
    )
    if (
        b2_audit.get("schema_id") != "ms33-b2-check/v1"
        or b2_audit.get("g33_02") != "established"
        or b2_audit.get("exit_code") != 0
        or b2_audit_results_ref != b2_results_actual
        or b2_audit.get("issues") != []
        or b2_audit.get("insufficient") != []
    ):
        raise CleanupQualityInsufficient("B2 audit no longer establishes G33-02")
    b2_results = _load_json(b2_results_path)
    if (
        b2_results.get("schema_id") != "ms33-b2-results/v1"
        or b2_audit.get("application_result") != b2_results.get("application_result")
    ):
        raise CleanupQualityInsufficient("B2 result set no longer establishes all eight cases")
    b2_cases = _case_map(b2_results.get("cases"), label="B2 cases")
    if any(row.get("technical_state") != "valid" for row in b2_cases.values()):
        raise CleanupQualityInsufficient("B2 result set no longer establishes all eight cases")
    if b2_results.get("application_result") == "no_applicable_candidates":
        for case_id, b2_case in b2_cases.items():
            _baseline_path, baseline_ref = _resolve_ref(
                b2_case.get("baseline_vmd_ref"), name=f"B2 {case_id} baseline VMD",
                declaring_file=b2_results_path, roots=b3_roots,
            )
            _candidate_path, candidate_ref = _resolve_ref(
                b2_case.get("candidate_vmd_ref"), name=f"B2 {case_id} no-applicable VMD",
                declaring_file=b2_results_path, roots=b3_roots,
            )
            if baseline_ref["sha256"] != candidate_ref["sha256"] or baseline_ref["bytes"] != candidate_ref["bytes"]:
                raise CleanupQualityError(f"B2 no-applicable result is not an exact pass-through: {case_id}")
    expected_upstream_states = {
        "b2_application_result": b2_results.get("application_result"),
        "b3_standalone_state": b3_audit.get("standalone_state"),
        "b3_combined_state": b3_audit.get("combined_state"),
    }
    if manifest.get("upstream_states") != expected_upstream_states:
        raise CleanupQualityError("B4 upstream state summary differs from current B2/B3 evidence")

    case_rows = manifest.get("cases")
    case_map = _case_map(case_rows, label="B4 comparison cases")
    for case_id in CASE_IDS:
        case = case_map[case_id]
        if set(case) != {"case_id", "input_mode", "base_plan_digest", "source_refs", "b1_baseline", "variants"}:
            raise CleanupQualityError(f"B4 case fields are invalid: {case_id}")
        b1_case = research_cases[case_id]
        if case.get("input_mode") != b1_case.get("input_mode"):
            raise CleanupQualityError(f"B4 case input mode differs from B1 research: {case_id}")
        raw_sources = case.get("source_refs")
        if type(raw_sources) is not dict or set(raw_sources) != {
            "analysis_trace", "analysis_wav", "full_snapshot", "source_audio", "source_text"
        }:
            raise CleanupQualityError(f"B4 case source refs are invalid: {case_id}")
        expected_sources = b1_case.get("source_refs")
        if type(expected_sources) is not dict or set(expected_sources) != set(raw_sources):
            raise CleanupQualityError(f"B1 research source reference set is invalid: {case_id}")
        source_paths: dict[str, Path] = {}
        for role, value in raw_sources.items():
            if value is not None:
                actual_source = CleanupArtifactReference.from_dict(value)
                source_paths[role] = verify_cleanup_artifact_reference(actual_source, roots)
                _source_path, expected_source = _resolve_ref(
                    expected_sources[role], name=f"B1 {case_id} {role}",
                    declaring_file=research_path, roots=b3_roots,
                )
                if actual_source.to_dict() != expected_source:
                    raise CleanupQualityError(f"B4 source reference differs from B1 research: {case_id}/{role}")
            elif (
                role != "source_text"
                or case.get("input_mode") != "voice_only"
                or expected_sources[role] is not None
            ):
                raise CleanupQualityError(f"B4 source reference was omitted: {case_id}/{role}")
        expected_base_plan_digest = _locked_b1_base_plan_digest(
            b1_case=b1_case,
            full_snapshot_path=source_paths["full_snapshot"],
            case_id=case_id,
            decoder=b1_snapshot_decoder,
        )
        if case.get("base_plan_digest") != expected_base_plan_digest:
            raise CleanupQualityError(f"B4 base plan digest differs from the B1 full snapshot: {case_id}")
        expected_b1_baseline = _accepted_b1_baseline_refs(
            case_id=case_id,
            b1_case=b1_case,
            research=research,
            research_path=research_path,
            research_ref=research_ref,
            audit=b1_audit_doc,
            audit_ref=_file_ref(b1_audit_path),
            full_snapshot_ref=case["source_refs"]["full_snapshot"],
            source_refs=case["source_refs"],
            roots=b3_roots,
            decoder=b1_snapshot_decoder,
        )
        if expected_b1_baseline["research_input_ref_record"] != research_input_ref_record:
            raise CleanupQualityError(f"B4 research input reference record differs from accepted research: {case_id}")
        _validate_b1_baseline_binding(
            case.get("b1_baseline"), expected_b1_baseline, case_id=case_id,
        )
        variants = case.get("variants")
        if type(variants) is not dict or set(variants) != set(VARIANTS):
            raise CleanupQualityError(f"B4 case variant set is invalid: {case_id}")
        for variant in VARIANTS:
            row = variants[variant]
            if (
                type(row) is not dict
                or set(row) != {
                    "origin", "state", "candidate_vmd_ref", "plan_ref", "input_ref",
                    "upstream_readback", "curve_checks",
                }
                or row.get("state") != "upstream_reference_only"
            ):
                raise CleanupQualityError(f"B4 variant record is malformed: {case_id}/{variant}")
            expected_origin = {
                "baseline": "b1_accepted_baseline",
                "keys_only": "b3_standalone_reference",
                "events_only": "b2_event_reference",
                "events_and_keys": "b3_combined_reference",
            }[variant]
            if row.get("origin") != expected_origin:
                raise CleanupQualityError(f"B4 variant origin is invalid: {case_id}/{variant}")
            if variant == "baseline":
                expected_variant_refs = {
                    "candidate_vmd_ref": expected_b1_baseline["vmd_ref"],
                    "plan_ref": expected_b1_baseline["plan_ref"],
                    "input_ref": expected_sources["full_snapshot"],
                }
                expected_readback = "passed"
                expected_curve_checks = []
            else:
                expected_case = {
                    "keys_only": b3_standalone_cases[case_id],
                    "events_only": b2_cases[case_id],
                    "events_and_keys": b3_combined_cases[case_id],
                }[variant]
                expected_fields = ("candidate_vmd_ref", "plan_ref", "input_ref")
                expected_variant_refs = {}
                for field, upstream_field in zip(
                    ("candidate_vmd_ref", "plan_ref", "input_ref"), expected_fields
                ):
                    _expected_path, expected_ref = _resolve_ref(
                        expected_case.get(upstream_field),
                        name=f"{case_id}/{variant} upstream {upstream_field}",
                        declaring_file=b3_combined_path,
                        roots=b3_roots,
                    )
                    expected_variant_refs[field] = expected_ref
                expected_readback = "passed" if variant in {"keys_only", "events_and_keys"} else "B4_readback_not_performed"
                expected_curve_checks = expected_case.get("curve_checks", [])
            for field, expected_ref in expected_variant_refs.items():
                if row.get(field) != expected_ref:
                    raise CleanupQualityError(f"B4 variant reference differs from its accepted source: {case_id}/{variant}/{field}")
            if row.get("upstream_readback") != expected_readback or row.get("curve_checks") != expected_curve_checks:
                raise CleanupQualityError(f"B4 variant evidence summary differs from upstream issuer: {case_id}/{variant}")
            for field in ("candidate_vmd_ref", "plan_ref", "input_ref"):
                verify_cleanup_artifact_reference(
                    CleanupArtifactReference.from_dict(row.get(field)), roots
                )
    return manifest, roots


def _read_optional_report(
    path: Path, schema_id: str,
) -> tuple[dict[str, Any], dict[str, object], tuple[Path, ...]]:
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise CleanupQualityInsufficient(f"required report is unavailable: {path}") from error
    report = _load_json(resolved)
    roots = _read_roots(report.get("read_roots"), resolved)
    if report.get("schema_id") != schema_id or not _within(resolved, roots):
        raise CleanupQualityError(f"report schema or read_roots are invalid: {resolved}")
    return report, _file_ref(resolved), roots


def _verify_report_comparison(
    report: dict[str, Any], report_roots: tuple[Path, ...], comparison_path: Path, *, label: str,
) -> None:
    _path, reference = _resolve_ref(
        report.get("comparison_ref"), name=f"{label} comparison", declaring_file=Path(report["_declaring_file"]),
        roots=report_roots,
    )
    if reference != _file_ref(comparison_path):
        raise CleanupQualityError(f"{label} is bound to a different B4 comparison manifest")


def _locked_case_source_references(case: dict[str, Any]) -> dict[str, CleanupArtifactReference]:
    source_refs = case.get("source_refs")
    baseline = case.get("b1_baseline")
    if type(source_refs) is not dict or type(baseline) is not dict:
        raise CleanupQualityError("B4 case source references are malformed")
    expected = {
        role: CleanupArtifactReference.from_dict(reference)
        for role, reference in source_refs.items()
        if reference is not None
    }
    baseline_roles = {
        "b1_audit": "audit_ref",
        "b1_research": "research_ref",
        "baseline_plan": "plan_ref",
        "baseline_readback": "readback_ref",
        "baseline_vmd": "vmd_ref",
        "capture_manifest": "capture_manifest_ref",
        "historical_reference_vmd": "historical_reference_vmd_ref",
    }
    for role, field in baseline_roles.items():
        expected[role] = CleanupArtifactReference.from_dict(baseline.get(field))
    return expected


def _case_source_references_match(
    actual: object, case: dict[str, Any],
) -> bool:
    return type(actual) is dict and actual == _locked_case_source_references(case)


def _strict_curve_identity(manifest: dict[str, Any]) -> bool:
    cases = manifest.get("cases")
    if type(cases) is not list or not cases:
        return False
    for case in cases:
        variants = case.get("variants") if type(case) is dict else None
        if type(variants) is not dict:
            return False
        for variant in ("keys_only", "events_and_keys"):
            checks = variants.get(variant, {}).get("curve_checks") if type(variants.get(variant)) is dict else None
            if type(checks) is not list or not checks:
                return False
            if any(type(check) is not dict or check.get("state") != "equal" for check in checks):
                return False
    return True


def _required_standard_quality_pairs(manifest: dict[str, Any]) -> set[tuple[str, str]]:
    required: set[tuple[str, str]] = set()
    event_policy = manifest.get("policies", {}).get("event", {})
    real_cases = event_policy.get("real_cases")
    event_case_ids: set[str] = set()
    malformed_scope = type(real_cases) is not list
    for item in real_cases if type(real_cases) is list else ():
        case_id = item if type(item) is str else item.get("case_id") if type(item) is dict else None
        if case_id not in CASE_IDS:
            malformed_scope = True
        else:
            event_case_ids.add(case_id)
    allowed_changes = event_policy.get("allowed_changes")
    if type(allowed_changes) is not list:
        malformed_scope = True
    if malformed_scope or (allowed_changes and not event_case_ids):
        event_case_ids = set(CASE_IDS)
    for case_id in event_case_ids:
        required.add((case_id, "events_only"))
        required.add((case_id, "events_and_keys"))

    cases = manifest.get("cases")
    if type(cases) is not list:
        return required | {(case_id, variant) for case_id in CASE_IDS for variant in ("keys_only", "events_and_keys")}
    seen_case_ids: set[str] = set()
    for case in cases:
        if type(case) is not dict or case.get("case_id") not in CASE_IDS:
            return required | {(case_id, variant) for case_id in CASE_IDS for variant in ("keys_only", "events_and_keys")}
        case_id = case["case_id"]
        seen_case_ids.add(case_id)
        variants = case.get("variants")
        if type(variants) is not dict:
            required.update((case_id, variant) for variant in ("keys_only", "events_and_keys"))
            continue
        for variant in ("keys_only", "events_and_keys"):
            row = variants.get(variant)
            checks = row.get("curve_checks") if type(row) is dict else None
            if type(checks) is not list or not checks or any(
                type(check) is not dict or check.get("state") != "equal" for check in checks
            ):
                required.add((case_id, variant))
    if seen_case_ids != set(CASE_IDS):
        required.update((case_id, variant) for case_id in set(CASE_IDS) - seen_case_ids for variant in ("keys_only", "events_and_keys"))
    return required


def _standard_quality_coverage_complete(
    quality_items: object,
    required_pairs: set[tuple[str, str]],
) -> bool:
    if not required_pairs:
        return True
    if type(quality_items) is not list or any(type(item) is not dict for item in quality_items):
        return False
    coverage = {
        (item.get("model"), item.get("case_id"), item.get("variant"))
        for item in quality_items
        if type(item.get("model")) is str and item.get("model")
    }
    for case_id, variant in required_pairs:
        candidate_models = {
            model for model, item_case, item_variant in coverage
            if item_case == case_id and item_variant == variant
        }
        baseline_models = {
            model for model, item_case, item_variant in coverage
            if item_case == case_id and item_variant == "baseline"
        }
        if not candidate_models.intersection(baseline_models):
            return False
    return True


def _verify_technical_report(
    path: Path,
    *,
    comparison_path: Path,
    manifest: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, object], tuple[Path, ...], dict[tuple[str, str], dict[str, Any]]]:
    report, reference, roots = _read_optional_report(path, "ms33-b4-technical-report/v1")
    report["_declaring_file"] = str(path.resolve(strict=True))
    _verify_report_comparison(report, roots, comparison_path, label="technical report")
    expected_top_fields = {
        "schema_id", "read_roots", "created_at_utc", "origin", "state",
        "comparison_ref", "items",
    }
    if (
        set(report) - {"_declaring_file"} != expected_top_fields
        or report.get("origin") != "automated_consumer_replay"
        or report.get("state") != "valid"
        or type(report.get("created_at_utc")) is not str
        or type(report.get("items")) is not list
        or len(report["items"]) != len(CASE_IDS) * len(VARIANTS)
    ):
        raise CleanupQualityError("B4 technical report header or 8-case by 4-variant matrix is invalid")

    case_map = {row["case_id"]: row for row in manifest["cases"]}
    result: dict[tuple[str, str], dict[str, Any]] = {}
    expected_contract_refs = tuple(
        CleanupArtifactReference.from_dict(manifest["b1_refs"][name])
        for name in ("contract", "audit", "research", "event_comparison")
    )
    expected_b3_audit_ref = CleanupArtifactReference.from_dict(manifest["b3_audit_ref"])
    for item in report["items"]:
        expected_item_fields = {
            "case_id", "variant", "state", "request", "source_refs",
            "plan_ref", "input_ref", "candidate_vmd_ref", "candidate_wav_ref",
            "identity", "consumer_checks", "save_readbacks",
        }
        if type(item) is not dict or set(item) != expected_item_fields:
            raise CleanupQualityError("B4 technical report contains a malformed matrix item")
        case_id, variant = item.get("case_id"), item.get("variant")
        key = (case_id, variant)
        if case_id not in case_map or variant not in VARIANTS or key in result:
            raise CleanupQualityError("B4 technical report matrix has an unknown or duplicate case/variant")
        case = case_map[case_id]
        upstream_variant = case["variants"][variant]
        if item.get("state") != "valid" or item.get("source_refs") != case["source_refs"]:
            raise CleanupQualityError(f"B4 technical report source or state differs for {case_id}/{variant}")
        request = CleanupEvaluationRequest.from_dict(item.get("request"))
        if (
            request.case_id != case_id
            or request.variant != variant
            or request.event_policy.to_dict() != manifest["policies"]["event"]
            or request.key_policy.to_dict() != manifest["policies"]["key"]
            or request.b1_contract_refs != expected_contract_refs
            or request.b3_audit_ref != expected_b3_audit_ref
            or not _case_source_references_match(dict(request.case_source_refs), case)
        ):
            raise CleanupQualityError(f"B4 technical request differs from its locked case: {case_id}/{variant}")

        for field in ("plan_ref", "input_ref"):
            actual = CleanupArtifactReference.from_dict(item.get(field))
            expected = CleanupArtifactReference.from_dict(upstream_variant[field])
            if actual != expected:
                raise CleanupQualityError(f"B4 technical {field} differs from upstream: {case_id}/{variant}")
            verify_cleanup_artifact_reference(actual, roots)
        candidate_vmd_ref = CleanupArtifactReference.from_dict(item.get("candidate_vmd_ref"))
        candidate_wav_ref = CleanupArtifactReference.from_dict(item.get("candidate_wav_ref"))
        verify_cleanup_artifact_reference(candidate_vmd_ref, roots)
        verify_cleanup_artifact_reference(candidate_wav_ref, roots)

        plan_path, _ = _resolve_ref(
            upstream_variant["plan_ref"],
            name=f"{case_id}/{variant} expected plan",
            declaring_file=comparison_path,
            roots=_read_roots(manifest.get("read_roots"), comparison_path),
        )
        expected_plan = _load_json(plan_path)
        identity = item.get("identity")
        if (
            type(identity) is not dict
            or set(identity) != {"binding_digest", "wire_digest"}
            or any(
                type(identity.get(name)) is not str
                or len(identity[name]) != 64
                or any(character not in "0123456789abcdef" for character in identity[name])
                for name in ("binding_digest", "wire_digest")
            )
            or identity.get("wire_digest") != _locked_plan_wire_digest(expected_plan)
        ):
            raise CleanupQualityError(f"B4 technical identity differs from the locked plan: {case_id}/{variant}")

        consumers = item.get("consumer_checks")
        if type(consumers) is not dict or set(consumers) != {"preview", "diagnostics"}:
            raise CleanupQualityError(f"B4 technical consumer checks are incomplete: {case_id}/{variant}")
        for consumer_name, consumer in consumers.items():
            if (
                type(consumer) is not dict
                or set(consumer) != {"state", "binding_digest", "wire_digest"}
                or consumer.get("state") != "passed"
                or consumer.get("binding_digest") != identity["binding_digest"]
                or consumer.get("wire_digest") != identity["wire_digest"]
            ):
                raise CleanupQualityError(
                    f"B4 {consumer_name} is not bound to the final wire: {case_id}/{variant}"
                )

        saves = item.get("save_readbacks")
        if type(saves) is not dict or set(saves) != {"individual", "delivery"}:
            raise CleanupQualityError(f"B4 technical save readbacks are incomplete: {case_id}/{variant}")
        for save_name, save in saves.items():
            required_save_fields = {"state", "wire_digest", "vmd_ref", "readback_ref"}
            if save_name == "delivery":
                required_save_fields.add("mmd_wav_ref")
            if (
                type(save) is not dict
                or set(save) != required_save_fields
                or save.get("state") != "passed"
                or save.get("wire_digest") != identity["wire_digest"]
            ):
                raise CleanupQualityError(f"B4 {save_name} readback is not valid: {case_id}/{variant}")
            save_vmd_ref = CleanupArtifactReference.from_dict(save.get("vmd_ref"))
            verify_cleanup_artifact_reference(save_vmd_ref, roots)
            readback_ref = CleanupArtifactReference.from_dict(save.get("readback_ref"))
            readback_path = verify_cleanup_artifact_reference(readback_ref, roots)
            readback = _load_json(readback_path)
            if (
                readback.get("schema_id") != "ms33-b4-vmd-readback/v1"
                or readback.get("state") != "passed"
                or readback.get("vmd_ref") != save_vmd_ref.to_dict()
                or readback.get("wire_digest") != identity["wire_digest"]
            ):
                raise CleanupQualityError(f"B4 {save_name} readback artifact is inconsistent: {case_id}/{variant}")
            if save_name == "individual" and save_vmd_ref != candidate_vmd_ref:
                raise CleanupQualityError(f"B4 individual save differs from its candidate: {case_id}/{variant}")
            if save_name == "delivery":
                delivery_wav_ref = CleanupArtifactReference.from_dict(save.get("mmd_wav_ref"))
                verify_cleanup_artifact_reference(delivery_wav_ref, roots)
                if delivery_wav_ref != candidate_wav_ref:
                    raise CleanupQualityError(f"B4 delivery WAV differs from its candidate: {case_id}/{variant}")
        result[key] = item
    expected_matrix = {(case_id, variant) for case_id in CASE_IDS for variant in VARIANTS}
    if set(result) != expected_matrix:
        raise CleanupQualityError("B4 technical report does not contain every locked case/variant")
    return report, reference, roots, result


def _same_artifact_content(
    left: CleanupArtifactReference,
    right: CleanupArtifactReference,
) -> bool:
    return left.sha256 == right.sha256 and left.bytes == right.bytes


def _locked_plan_wire_digest(plan: dict[str, Any]) -> object:
    """Read wire digests from both candidate and B1 closure plan shapes."""
    digest = plan.get("wire_digest")
    if digest is not None:
        return digest
    closure_plan = plan.get("closure_plan")
    if type(closure_plan) is dict:
        return closure_plan.get("wire_digest")
    return None


def _verify_b4c_artifact_set(
    path: Path,
    *,
    technical_roots: tuple[Path, ...],
    technical_items: dict[tuple[str, str], dict[str, Any]],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    try:
        index_set_path = path.resolve(strict=True)
    except OSError as error:
        raise CleanupQualityInsufficient(f"B4C artifact index set is unavailable: {path}") from error
    if not _within(index_set_path, technical_roots):
        raise CleanupQualityError("B4C artifact index set escapes the technical replay roots")
    index_set = _load_json(index_set_path)
    if set(index_set) != {"schema_id", "artifacts"} or index_set.get("schema_id") != "ms33-b4c-artifact-index-set/v1":
        raise CleanupQualityError("B4C artifact index set schema is invalid")
    artifacts = index_set.get("artifacts")
    if type(artifacts) is not list:
        raise CleanupQualityError("B4C artifact index set entries are invalid")

    reviewed_rows: list[dict[str, object]] = []
    seen_cases: set[str] = set()
    for artifact_ref in artifacts:
        artifact_index_path, artifact_index_ref = _resolve_ref(
            artifact_ref,
            name="B4C case artifact index",
            declaring_file=index_set_path,
            roots=technical_roots,
        )
        artifact_index = _load_json(artifact_index_path)
        expected_index_fields = {
            "baseline_vmd_ref", "candidate_policy_id", "candidate_validation_ref",
            "candidate_vmd_ref", "case_id", "paired_mmd_wav_ref", "quality_record_ref",
            "schema_id", "state",
        }
        if (
            set(artifact_index) != expected_index_fields
            or artifact_index.get("schema_id") != "ms33-b4c-artifact-index/v1"
            or artifact_index.get("case_id") not in CASE_IDS
            or artifact_index.get("case_id") in seen_cases
            or artifact_index.get("state") not in {
                "candidate_only_mmd_review_required", "candidate_only_mmd_review_passed",
            }
            or type(artifact_index.get("candidate_policy_id")) is not str
            or not artifact_index.get("candidate_policy_id")
        ):
            raise CleanupQualityError("B4C case artifact index is malformed or duplicated")
        case_id = artifact_index["case_id"]
        seen_cases.add(case_id)
        baseline_ref = CleanupArtifactReference.from_dict(artifact_index.get("baseline_vmd_ref"))
        candidate_ref = CleanupArtifactReference.from_dict(artifact_index.get("candidate_vmd_ref"))
        paired_wav_ref = CleanupArtifactReference.from_dict(artifact_index.get("paired_mmd_wav_ref"))
        validation_path, validation_ref = _resolve_ref(
            artifact_index.get("candidate_validation_ref"),
            name=f"B4C validation {case_id}",
            declaring_file=artifact_index_path,
            roots=technical_roots,
        )
        quality_path, quality_ref = _resolve_ref(
            artifact_index.get("quality_record_ref"),
            name=f"B4C quality record {case_id}",
            declaring_file=artifact_index_path,
            roots=technical_roots,
        )
        verify_cleanup_artifact_reference(baseline_ref, technical_roots)
        verify_cleanup_artifact_reference(candidate_ref, technical_roots)
        verify_cleanup_artifact_reference(paired_wav_ref, technical_roots)
        technical_baseline = technical_items.get((case_id, "baseline"))
        if technical_baseline is None or (
            not _same_artifact_content(
                baseline_ref,
                CleanupArtifactReference.from_dict(technical_baseline["candidate_vmd_ref"]),
            )
            or not _same_artifact_content(
                paired_wav_ref,
                CleanupArtifactReference.from_dict(technical_baseline["candidate_wav_ref"]),
            )
        ):
            raise CleanupQualityError(f"B4C candidate does not use the locked B4 baseline and paired WAV: {case_id}")

        validation = _load_json(validation_path)
        quality = _load_json(quality_path)
        try:
            validate_vowel_quality_record(quality)
        except B4CVowelQualityError as error:
            raise CleanupQualityError(f"B4C quality record is invalid: {case_id}") from error
        quality_vmd = quality.get("vmd")
        quality_validation = quality.get("candidate_validation")
        if (
            quality.get("schema_id") != B4C_QUALITY_SCHEMA
            or quality.get("case_id") != case_id
            or quality.get("candidate_policy_id") != artifact_index["candidate_policy_id"]
            or quality.get("state") != "candidate_only"
            or type(quality_vmd) is not dict
            or quality_vmd.get("baseline") != baseline_ref.to_dict()
            or quality_vmd.get("candidate") != candidate_ref.to_dict()
            or type(quality_validation) is not dict
            or type(validation) is not dict
            or validation.get("state") != "passed"
            or validation.get("candidate_policy_id") != artifact_index["candidate_policy_id"]
            or validation.get("baseline_vmd_ref") != baseline_ref.to_dict()
            or validation.get("candidate_vmd_ref") != candidate_ref.to_dict()
            or validation.get("paired_mmd_wav_ref") != paired_wav_ref.to_dict()
            or quality_validation.get("state") != "passed"
        ):
            raise CleanupQualityError(f"B4C candidate and quality record are not bound to the locked case: {case_id}")
        review = quality.get("mmd_review")
        if type(review) is not dict or review.get("state") not in {"passed", "not_performed"}:
            raise CleanupQualityError(f"B4C MMD review status is invalid: {case_id}")
        reviewed_frames: list[int] = []
        if review.get("state") == "passed":
            raw_frames = review.get("reviewed_frames")
            if (
                review.get("required") is not True
                or review.get("reviewer") != "user"
                or review.get("model_target") != "Tda式初音ミク"
                or review.get("candidate_vmd_sha256") != candidate_ref.sha256
                or review.get("paired_mmd_wav_sha256") != paired_wav_ref.sha256
                or type(review.get("reviewed_on")) is not str
                or type(review.get("result")) is not str
                or not review.get("result")
                or type(review.get("user_observation")) is not str
                or not review.get("user_observation")
                or type(raw_frames) is not list
                or not raw_frames
                or any(
                    type(row) is not dict
                    or isinstance(row.get("frame"), bool)
                    or not isinstance(row.get("frame"), int)
                    or row.get("frame") < 0
                    or type(row.get("morph")) is not str
                    or not row.get("morph")
                    or row.get("result") != "opened_and_closed_correctly"
                    for row in raw_frames
                )
            ):
                raise CleanupQualityError(f"B4C MMD review is not bound to the exact candidate and observed frames: {case_id}")
            reviewed_frames = [row["frame"] for row in raw_frames]
            if artifact_index.get("state") != "candidate_only_mmd_review_passed":
                raise CleanupQualityError(f"B4C artifact index does not record its passed MMD review: {case_id}")
        elif artifact_index.get("state") != "candidate_only_mmd_review_required":
            raise CleanupQualityError(f"B4C artifact index claims a missing MMD review: {case_id}")

        reviewed_rows.append({
            "case_id": case_id,
            "state": review["state"],
            "model": review.get("model_target"),
            "reviewed_frames": reviewed_frames,
            "candidate_policy_id": artifact_index["candidate_policy_id"],
            "candidate_vmd_ref": candidate_ref.to_dict(),
            "paired_mmd_wav_ref": paired_wav_ref.to_dict(),
            "candidate_validation_ref": validation_ref,
            "quality_record_ref": quality_ref,
            "artifact_index_ref": artifact_index_ref,
            "result": review.get("result"),
        })
    return _file_ref(index_set_path), reviewed_rows


def audit_comparison_manifest(
    *,
    comparison_path: Path,
    output_root: Path,
    repository_root: Path,
    live_evidence_paths: tuple[Path, ...] = (),
    gui_report_path: Path | None = None,
    quality_report_path: Path | None = None,
    b4c_artifact_index_path: Path | None = None,
    technical_report_path: Path | None = None,
    test_summary_paths: tuple[Path, ...] = (),
) -> tuple[Path, dict[str, object], int]:
    manifest, source_roots = _verify_manifest(comparison_path, repository_root)
    live_refs: list[dict[str, object]] = []
    gui_ref: dict[str, object] | None = None
    quality_ref: dict[str, object] | None = None
    test_refs: list[dict[str, object]] = []
    issues: list[str] = []
    insufficient: list[str] = []
    live_documents: list[dict[str, Any]] = []
    valid_live_modes: set[str] = set()
    valid_live_sessions: set[str] = set()
    comparison_path = comparison_path.resolve(strict=True)
    technical_document: dict[str, Any] | None = None
    technical_ref: dict[str, object] | None = None
    technical_roots: tuple[Path, ...] = ()
    technical_items: dict[tuple[str, str], dict[str, Any]] = {}
    b4c_artifact_index_set_ref: dict[str, object] | None = None
    b4c_quality_evidence: list[dict[str, object]] = []
    if technical_report_path is not None:
        technical_document, technical_ref, technical_roots, technical_items = _verify_technical_report(
            technical_report_path,
            comparison_path=comparison_path,
            manifest=manifest,
        )
    if b4c_artifact_index_path is not None:
        if technical_document is None:
            raise CleanupQualityInsufficient("B4C evidence requires a complete B4 technical replay report")
        b4c_artifact_index_set_ref, b4c_quality_evidence = _verify_b4c_artifact_set(
            b4c_artifact_index_path,
            technical_roots=technical_roots,
            technical_items=technical_items,
        )
    for path in live_evidence_paths:
        report, ref, report_roots = _read_optional_report(path, "ms33-b4-live/v1")
        report["_declaring_file"] = str(path.resolve(strict=True))
        _verify_report_comparison(report, report_roots, comparison_path, label="live evidence")
        if (
            report.get("origin") != "live"
            or report.get("state") != "valid"
            or report.get("case_id") not in CASE_IDS
            or report.get("variant") not in VARIANTS
            or type(report.get("session_id")) is not str
            or not report.get("session_id")
            or type(report.get("request_digest")) is not str
            or len(report.get("request_digest", "")) != 64
        ):
            issues.append(f"live evidence is not a valid live session: {path}")
            continue
        try:
            request = CleanupEvaluationRequest.from_dict(report.get("request"))
        except CleanupEvaluationError:
            issues.append(f"live evidence request is malformed or has an invalid digest: {path}")
            continue
        expected_contract_refs = tuple(
            CleanupArtifactReference.from_dict(manifest["b1_refs"][name])
            for name in ("contract", "audit", "research", "event_comparison")
        )
        if (
            request.case_id != report["case_id"]
            or request.variant != report["variant"]
            or request.evaluation_session_id != report["session_id"]
            or request.request_digest != report["request_digest"]
            or request.event_policy.to_dict() != manifest["policies"]["event"]
            or request.key_policy.to_dict() != manifest["policies"]["key"]
            or request.b1_contract_refs != expected_contract_refs
            or request.b3_audit_ref != CleanupArtifactReference.from_dict(manifest["b3_audit_ref"])
        ):
            issues.append(f"live evidence request differs from the locked candidate: {path}")
            continue
        case = next((row for row in manifest["cases"] if row["case_id"] == report["case_id"]), None)
        source_refs = report.get("source_refs")
        identity = report.get("identity")
        consumers = report.get("consumer_checks")
        saves = report.get("save_readbacks")
        if case is None or type(source_refs) is not dict or set(source_refs) != set(case["source_refs"]):
            issues.append(f"live evidence source refs do not match its locked B1 case: {path}")
            continue
        variant_entry = case["variants"].get(report["variant"])
        if type(variant_entry) is not dict:
            issues.append(f"live evidence variant is missing from its locked case: {path}")
            continue
        technical_item = technical_items.get((report["case_id"], report["variant"]))
        if technical_item is None:
            issues.append(f"live evidence has no matching automated B4 replay: {path}")
            continue
        expected_vmd_ref = CleanupArtifactReference.from_dict(technical_item["candidate_vmd_ref"])
        expected_session_sources = {
            role: reference
            for role, reference in case["source_refs"].items()
            if reference is not None
        }
        try:
            candidate_vmd_ref = CleanupArtifactReference.from_dict(report.get("candidate_vmd_ref"))
            verify_cleanup_artifact_reference(candidate_vmd_ref, report_roots)
            if candidate_vmd_ref != expected_vmd_ref:
                raise CleanupEvaluationError("live candidate VMD differs from its locked variant")
            session_manifest_ref = CleanupArtifactReference.from_dict(
                report.get("session_manifest_ref")
            )
            session_manifest_path = verify_cleanup_artifact_reference(
                session_manifest_ref, report_roots
            )
            session_manifest = _load_json(session_manifest_path)
            session_request = session_manifest.get("request")
            session_sources = session_manifest.get("locked_case_sources")
            if (
                session_manifest.get("schema_id") != "ms33-b4-candidate-session/v1"
                or session_manifest.get("origin") != "candidate_launcher"
                or session_manifest.get("case_id") != report["case_id"]
                or session_manifest.get("variant") != report["variant"]
                or session_manifest.get("comparison_ref") != _file_ref(comparison_path)
                or type(session_request) is not dict
                or session_request.get("request_digest") != report["request_digest"]
                or session_sources != expected_session_sources
            ):
                raise CleanupEvaluationError("live evidence does not match its candidate session manifest")
        except (CleanupEvaluationError, CleanupQualityError, CleanupQualityInsufficient, OSError, ValueError):
            issues.append(f"live evidence lacks a matching candidate VMD and launched session manifest: {path}")
            continue
        source_match = True
        for role, expected in case["source_refs"].items():
            actual = source_refs.get(role)
            if expected is None:
                if actual is not None:
                    source_match = False
                continue
            try:
                actual_ref = CleanupArtifactReference.from_dict(actual)
                verify_cleanup_artifact_reference(actual_ref, report_roots)
                source_match = source_match and actual_ref.to_dict() == expected
            except (CleanupEvaluationError, OSError, ValueError):
                source_match = False
        digest_fields_valid = (
            type(identity) is dict
            and all(
                type(identity.get(name)) is str
                and len(identity[name]) == 64
                and all(character in "0123456789abcdef" for character in identity[name])
                for name in ("cleanup_input_digest", "binding_digest", "wire_digest")
            )
        )
        consumer_valid = (
            type(consumers) is dict
            and all(
                type(consumers.get(name)) is dict
                and consumers[name].get("state") == "passed"
                and consumers[name].get("binding_digest") == identity.get("binding_digest")
                and consumers[name].get("wire_digest") == identity.get("wire_digest")
                for name in ("preview", "diagnostics")
            )
        ) if digest_fields_valid else False
        save_refs_valid = False
        if type(saves) is dict and set(saves) == {"individual", "delivery"}:
            try:
                save_refs_valid = all(
                    CleanupArtifactReference.from_dict(saves[name].get("vmd_ref"))
                    == expected_vmd_ref
                    for name in ("individual", "delivery")
                    if type(saves[name]) is dict
                ) and all(type(saves[name]) is dict for name in ("individual", "delivery"))
            except (CleanupEvaluationError, TypeError, ValueError):
                save_refs_valid = False
        save_valid = (
            type(saves) is dict
            and set(saves) == {"individual", "delivery"}
            and save_refs_valid
            and all(
                type(saves[name]) is dict
                and saves[name].get("state") == "passed"
                and saves[name].get("wire_digest") == identity.get("wire_digest")
                for name in ("individual", "delivery")
            )
        ) if digest_fields_valid else False
        if not source_match or not digest_fields_valid or not consumer_valid or not save_valid:
            issues.append(f"live evidence lacks matching source, consumer binding, or both save readbacks: {path}")
            continue
        if report["session_id"] in valid_live_sessions:
            issues.append("live evidence reuses a candidate session ID")
            continue
        valid_live_sessions.add(report["session_id"])
        valid_live_modes.add("ta" if report["case_id"].endswith("-ta") else "vo")
        live_documents.append(report)
        live_refs.append(ref)
    live_state = "accepted" if valid_live_modes == {"ta", "vo"} else "pending"
    gui_document = None
    gui_roots: tuple[Path, ...] = ()
    if gui_report_path is not None:
        gui_document, gui_ref, gui_roots = _read_optional_report(gui_report_path, "ms33-b4-gui-report/v1")
        gui_document["_declaring_file"] = str(gui_report_path.resolve(strict=True))
        _verify_report_comparison(gui_document, gui_roots, comparison_path, label="GUI report")
    quality_document = None
    quality_roots: tuple[Path, ...] = ()
    if quality_report_path is not None:
        quality_document, quality_ref, quality_roots = _read_optional_report(
            quality_report_path, "ms33-b4-quality-report/v1"
        )
        quality_document["_declaring_file"] = str(quality_report_path.resolve(strict=True))
        _verify_report_comparison(quality_document, quality_roots, comparison_path, label="quality report")
    test_documents: list[dict[str, Any]] = []
    test_source_locks_valid: list[bool] = []
    test_target_reports_valid: list[bool] = []
    covered_test_targets: set[str] = set()
    expected_test_sources = {
        row["path"]: row for row in manifest["runtime_lock"]
    }
    expected_runner_hash = expected_test_sources["tools/run-tests.ps1"]["sha256"]
    for path in test_summary_paths:
        try:
            summary_path = path.resolve(strict=True)
        except OSError as error:
            raise CleanupQualityInsufficient(f"test summary is unavailable: {path}") from error
        report = _load_json(summary_path)
        ref = _file_ref(summary_path)
        targets = _normalized_test_targets(report.get("targets"))
        targets_valid = report.get("mode") == "TestPaths" and targets is not None
        if targets_valid:
            covered_test_targets.update(targets)
        else:
            issues.append(f"test summary does not declare valid limited test targets: {path}")
        test_target_reports_valid.append(targets_valid)
        if (
            type(report.get("pytest_exit_code")) is not int or report.get("pytest_exit_code") != 0
            or type(report.get("runner_exit_code")) is not int or report.get("runner_exit_code") != 0
        ):
            issues.append(f"test run did not pass both exit codes: {path}")
        if report.get("user_data_differences") != [] or report.get("cleanup_result") != "removed":
            issues.append(f"test run changed user data or left runner work: {path}")
        source_lock_valid = True
        for field in ("source_hashes_before", "source_hashes_after"):
            rows = report.get(field)
            if type(rows) is not list or any(type(row) is not dict for row in rows):
                source_lock_valid = False
                continue
            observed: dict[str, dict[str, object]] = {}
            for row in rows:
                if set(row) != {"path", "bytes", "sha256"} or type(row.get("path")) is not str:
                    source_lock_valid = False
                    continue
                if row["path"] in observed:
                    source_lock_valid = False
                observed[row["path"]] = row
            if any(observed.get(relative) != expected for relative, expected in expected_test_sources.items()):
                source_lock_valid = False
        if report.get("runner_sha256") != expected_runner_hash:
            source_lock_valid = False
        if not source_lock_valid:
            issues.append(f"test run did not hash the current B4 runtime before and after execution: {path}")
        test_source_locks_valid.append(source_lock_valid)
        test_documents.append(report)
        test_refs.append(ref)

    coverage_map: dict[str, list[str]] = {}
    gui_case_modes: dict[str, set[str]] = {}
    if gui_document is not None:
        items = gui_document.get("items")
        if (
            gui_document.get("reviewer_kind") not in {"user", "codex"}
            or type(gui_document.get("reviewer")) is not str
            or not gui_document.get("reviewer")
            or type(gui_document.get("created_at_utc")) is not str
            or type(items) is not list
            or any(type(item) is not dict for item in items)
        ):
            issues.append("GUI report items are malformed")
        else:
            for item in items:
                item_id, state = item.get("item_id"), item.get("state")
                if (
                    type(item_id) is not str or item_id not in {f"GUI{number:02d}" for number in range(1, 7)}
                    or state not in {"passed", "not_applicable", "failed", "pending", "not_performed"}
                    or item.get("source_kind") not in {"live", "fixture"}
                    or type(item.get("case_id")) is not str
                    or type(item.get("session_id")) is not str
                    or not item.get("session_id")
                    or type(item.get("expected")) is not str
                    or type(item.get("observed")) is not str
                    or not item.get("observed")
                ):
                    issues.append("GUI report contains an invalid item result")
                    continue
                if item_id == "GUI01" and item.get("source_kind") != "live":
                    issues.append("GUI01 requires an actual candidate GUI session")
                if item_id == "GUI01" and item.get("case_id") not in CASE_IDS:
                    issues.append("GUI01 requires a locked TA or VO case")
                if item_id in {"GUI02", "GUI03"} and item.get("source_kind") != "fixture":
                    issues.append(f"{item_id} requires the independent fixture session")
                if item_id in {"GUI04", "GUI05", "GUI06"} and item.get("source_kind") != "live":
                    issues.append(f"{item_id} requires an actual candidate GUI session")
                if item_id in {"GUI04", "GUI05", "GUI06"} and item.get("case_id") not in CASE_IDS:
                    issues.append(f"{item_id} requires a locked TA or VO case")
                coverage_map.setdefault(item_id, []).append(state)
                if item_id == "GUI01" and item.get("case_id") in CASE_IDS:
                    gui_case_modes.setdefault(item_id, set()).add(
                        "ta" if item["case_id"].endswith("-ta") else "vo"
                    )
    required_gui = {f"GUI{number:02d}" for number in range(1, 7)}
    gui_complete = bool(gui_document is not None) and required_gui.issubset(coverage_map) and all(
        state == "passed"
        for item_id in required_gui
        for state in coverage_map.get(item_id, ())
    ) and gui_case_modes.get("GUI01") == {"ta", "vo"}

    quality_decision = None if quality_document is None else quality_document.get("decision")
    if quality_decision not in {None, "accepted", "rejected", "pending", "not_evaluable", "not_applicable"}:
        issues.append("quality report decision is invalid")
        quality_decision = "not_evaluable"
    if quality_document is not None and quality_decision is not None:
        expected_policy_digests = {
            "event": manifest["policies"]["event"].get("policy_digest"),
            "key": manifest["policies"]["key"].get("policy_digest"),
        }
        if quality_document.get("policy_digests") != expected_policy_digests:
            issues.append("quality report policy digests differ from the locked comparison")
            quality_decision = "pending"
        if quality_document.get("reviewer_kind") != "user":
            issues.append("quality decision must be recorded as a user decision")
            quality_decision = "pending"
    if quality_decision == "accepted" and quality_document is not None:
        quality_items = quality_document.get("items")
        if (
            quality_document.get("reviewer_kind") != "user"
            or type(quality_document.get("reviewer")) is not str
            or not quality_document.get("reviewer")
            or type(quality_items) is not list
            or not quality_items
        ):
            issues.append("quality acceptance must be a user decision")
            quality_decision = "pending"
        else:
            for item in quality_items:
                if type(item) is not dict or item.get("state") not in {"accepted", "not_applicable"}:
                    issues.append("quality report contains an unresolved comparison item")
                    quality_decision = "pending"
                    continue
                if item.get("case_id") not in CASE_IDS or item.get("variant") not in VARIANTS:
                    issues.append("quality report item does not identify a locked case and variant")
                    quality_decision = "pending"
                    continue
                if (
                    type(item.get("model")) is not str or not item.get("model")
                    or type(item.get("frames")) is not list or not item.get("frames")
                    or any(isinstance(frame, bool) or not isinstance(frame, int) or frame < 0 for frame in item.get("frames", []))
                    or type(item.get("criterion")) is not str or not item.get("criterion")
                    or type(item.get("observation")) is not str or not item.get("observation")
                ):
                    issues.append("quality report item lacks model, frame, criterion, or observation details")
                    quality_decision = "pending"
                for field in ("vmd_ref", "wav_ref"):
                    try:
                        item_ref = CleanupArtifactReference.from_dict(item.get(field))
                        verify_cleanup_artifact_reference(item_ref, quality_roots)
                        if field == "vmd_ref":
                            technical_item = technical_items.get((item["case_id"], item["variant"]))
                            if technical_item is None or item_ref != CleanupArtifactReference.from_dict(
                                technical_item["candidate_vmd_ref"]
                            ):
                                raise CleanupEvaluationError(
                                    "quality VMD differs from its automated case and variant replay"
                                )
                        else:
                            technical_item = technical_items.get((item["case_id"], item["variant"]))
                            if technical_item is None or item_ref != CleanupArtifactReference.from_dict(
                                technical_item["candidate_wav_ref"]
                            ):
                                raise CleanupEvaluationError(
                                    "quality WAV differs from its automated case and variant replay"
                                )
                    except (CleanupEvaluationError, OSError, ValueError):
                        issues.append(f"quality report {field} is missing, changed, outside its read_roots, or not bound to its locked case")
                        quality_decision = "pending"
            if quality_decision == "accepted" and not _standard_quality_coverage_complete(
                quality_items,
                _required_standard_quality_pairs(manifest),
            ):
                issues.append("quality report does not cover each curve-changing case with its baseline on the same model")
                quality_decision = "pending"
    if quality_decision == "not_applicable" and quality_document is not None:
        basis = quality_document.get("not_applicable_basis")
        policy = manifest.get("policies", {}).get("event", {})
        empty_event_scope = (
            manifest.get("upstream_states", {}).get("b2_application_result") == "no_applicable_candidates"
            and policy.get("real_cases") == []
            and policy.get("allowed_changes") == []
        )
        identical_curves = _strict_curve_identity(manifest)
        if basis == "empty_event_scope":
            if not empty_event_scope:
                issues.append("not_applicable empty-event basis is not supported by B1/B2 evidence")
                quality_decision = "pending"
        elif basis == "strict_curve_identity":
            if not identical_curves:
                issues.append("not_applicable curve basis lacks strict equality evidence")
                quality_decision = "pending"
        else:
            issues.append("not_applicable quality report lacks an accepted basis")
            quality_decision = "pending"

    required_standard_quality_pairs = _required_standard_quality_pairs(manifest)
    if required_standard_quality_pairs and (
        quality_document is None or quality_decision != "accepted"
    ):
        quality_decision = "pending"
    elif not required_standard_quality_pairs and quality_decision is None:
        quality_decision = "not_applicable"
    if b4c_quality_evidence:
        if not all(row.get("state") == "passed" for row in b4c_quality_evidence):
            quality_decision = "pending"
        elif quality_decision in {"accepted", "not_applicable"}:
            quality_decision = "accepted"
        else:
            quality_decision = "pending"

    technical_state = "accepted" if len(technical_items) == len(CASE_IDS) * len(VARIANTS) else "pending"
    gui_state = "accepted" if gui_complete else "pending"
    quality_state = (
        "accepted" if quality_decision == "accepted"
        else "rejected" if quality_decision == "rejected"
        else "not_applicable" if quality_decision == "not_applicable"
        else "pending"
    )
    passed_gui = {
        item_id
        for item_id, states in coverage_map.items()
        if states and all(state == "passed" for state in states)
    }
    missing_test_targets = sorted(
        set(REQUIRED_B4B_TEST_PATHS) - covered_test_targets
    )
    tests_target_coverage_valid = not missing_test_targets
    tests_valid = bool(test_documents) and all(
        type(report.get("pytest_exit_code")) is int
        and report.get("pytest_exit_code") == 0
        and type(report.get("runner_exit_code")) is int
        and report.get("runner_exit_code") == 0
        and report.get("user_data_differences") == []
        and report.get("cleanup_result") == "removed"
        for report in test_documents
    ) and all(test_source_locks_valid) and all(test_target_reports_valid) and tests_target_coverage_valid
    ac_results: dict[str, str] = {
        "B4-AC01": "established",
        "B4-AC02": "established" if technical_state == "accepted" else "not_yet_established",
        "B4-AC03": "established" if technical_state == "accepted" else "not_yet_established",
        "B4-AC04": "established" if {"GUI02", "GUI03", "GUI04", "GUI05"}.issubset(passed_gui) else "not_yet_established",
        "B4-AC05": "established" if technical_state == "accepted" and live_state == "accepted" else "not_yet_established",
        "B4-AC06": "established" if technical_state == "accepted" and live_state == "accepted" and tests_valid else "not_yet_established",
        "B4-AC07": "established" if gui_complete else "not_yet_established",
        "B4-AC08": "established" if technical_state == "accepted" and quality_state in {"accepted", "not_applicable"} else "not_yet_established",
        "B4-AC09": "not_yet_established",
    }
    if technical_state != "accepted":
        insufficient.append("a complete, artifact-bound B4 technical replay report is missing")
    if live_state != "accepted":
        insufficient.append("live TA and VO candidate sessions with matched Preview, diagnostics, and both save readbacks are incomplete")
    if gui_state != "accepted":
        insufficient.append("GUI01-GUI06 itemized evidence is incomplete")
    if quality_state == "pending":
        insufficient.append("user MMD quality decision or justified not-applicable report is missing")
    if not tests_valid:
        insufficient.append("a successful required regression-test summary is missing")
    if not tests_target_coverage_valid:
        insufficient.append("required B4 regression-test targets are missing from the supplied summaries")
    ac_results["B4-AC09"] = (
        "established"
        if all(ac_results[f"B4-AC{number:02d}"] == "established" for number in range(1, 9))
        else "not_yet_established"
    )
    g33_04 = (
        "established"
        if all(ac_results[f"B4-AC{number:02d}"] == "established" for number in range(1, 10))
        and not issues
        else "not_established"
    )
    exit_code = 0 if g33_04 == "established" else 1 if issues else 2
    output = output_root.resolve(strict=False)
    if output.exists() or any(output == root or output.is_relative_to(root) or root.is_relative_to(output) for root in source_roots):
        raise CleanupQualityError("B4 audit output root exists or overlaps its input roots")
    output_roots = tuple(dict.fromkeys((*source_roots, output)))
    audit = {
        "schema_id": AUDIT_SCHEMA,
        "read_roots": [str(path) for path in output_roots],
        "comparison_ref": _file_ref(comparison_path),
        "technical_report_ref": technical_ref,
        "live_evidence_refs": live_refs,
        "gui_report_ref": gui_ref,
        "quality_report_ref": quality_ref,
        "b4c_artifact_index_set_ref": b4c_artifact_index_set_ref,
        "b4c_quality_evidence": b4c_quality_evidence,
        "test_summary_refs": test_refs,
        "technical_state": technical_state,
        "live_state": live_state,
        "gui_state": gui_state,
        "quality_state": quality_state,
        "g33_04": g33_04,
        "ac_results": ac_results,
        "test_coverage": {
            "run_count": len(test_documents),
            "passed_run_count": sum(1 for row in test_documents if row.get("pytest_exit_code") == 0 and row.get("runner_exit_code") == 0),
            "required_paths": list(REQUIRED_B4B_TEST_PATHS),
            "covered_paths": sorted(covered_test_targets),
            "missing_paths": missing_test_targets,
        },
        "quality_scope": {
            "required_standard_case_variants": [
                {"case_id": case_id, "variant": variant}
                for case_id, variant in sorted(required_standard_quality_pairs)
            ],
            "b4c_reviewed_case_ids": [
                row["case_id"] for row in b4c_quality_evidence if row.get("state") == "passed"
            ],
        },
        "technical_case_count": len(technical_items),
        "issues": issues,
        "insufficient": insufficient,
        "exit_code": exit_code,
    }
    output.mkdir(parents=True, exist_ok=False)
    audit_path = output / "audit.json"
    payload = json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False).encode("utf-8") + b"\n"
    try:
        with audit_path.open("xb") as stream:
            stream.write(payload)
    except OSError as error:
        raise CleanupQualityInsufficient(f"cannot create B4 audit: {audit_path}") from error
    return audit_path, audit, exit_code


__all__ = [
    "AUDIT_SCHEMA",
    "CASE_IDS",
    "COMPARISON_SCHEMA",
    "CleanupQualityError",
    "CleanupQualityInsufficient",
    "B4B_TEST_PATHS",
    "REQUIRED_B4_TEST_PATHS",
    "REQUIRED_B4B_TEST_PATHS",
    "RUNTIME_LOCK_PATHS",
    "VARIANTS",
    "audit_comparison_manifest",
    "prepare_comparison_manifest",
]
