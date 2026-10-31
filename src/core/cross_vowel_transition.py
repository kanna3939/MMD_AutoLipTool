"""Explicit MS32 cross-vowel transition policy and deterministic resolver."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, fields, is_dataclass, replace
from typing import Any, Mapping, Sequence

from src.core.effective_shape_plan import EffectiveShape, ShapeControlPoint
from src.core.transition_acoustic import (
    TransitionAcousticSnapshot,
    measure_acoustic_window,
    read_transition_acoustic_snapshot,
)

TRANSITION_POLICY_SCHEMA = "cross-vowel-transition-policy/v1"
TRANSITION_POLICY_ID = "ms32-cross-vowel-transition/evaluation-v1"
B1_CONTRACT_SHA256 = "8e4dd1c928167640d39bcf75ce5b84220ea2ae643c67c416c34e6fc851a8e155"
TRANSITION_POLICY_V2 = "ms32-cross-vowel-transition/evaluation-v2"
B4B_CONTRACT_SHA256 = hashlib.sha256(
    b"ms32-b4b/v2;fps=30;active=2;release=3;short=1;shift=1;support=2;area=triangle;"
    b"search=component-minimum;admission=source-before-zero-validation;"
    b"closure=guard-before-positive-start;protection=core-manual-automatic"
).hexdigest()
TRANSITION_LINEAGE_KINDS = frozenset({"live_analysis", "replayed_capture"})
TRANSITION_REASONS = frozenset(
    {
        "same_vowel",
        "non_adjacent_events",
        "event_not_automatic",
        "manual_or_unknown_owner",
        "role_not_eligible",
        "unresolved_owner",
        "existing_handoff",
        "silence_core_overlap",
        "independent_required_zero",
        "acoustic_snapshot_invalid",
        "rms_unobserved",
        "zero_duration_window",
        "zero_sample_window",
        "incomplete_rms_coverage",
        "rms_at_or_below_diagnostic_threshold",
        "continuity_below_threshold",
        "structural_start_zero_missing",
        "structural_start_zero_ambiguous",
        "start_zero_has_independent_owner",
        "candidate_start_capacity_insufficient",
        "previous_fall_capacity_insufficient",
        "next_rise_capacity_insufficient",
        "candidate_window_in_silence_core",
        "source_event_geometry_invalid",
        "candidate_overlap_not_increased",
        "continuous_overlap_width_delta_exceeded",
        "positive_integer_frame_delta_exceeded",
        "neighbor_transition_conflict",
    }
)


class TransitionContractError(ValueError):
    """A transition policy, lineage, or resolution violates its contract."""


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TransitionContractError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise TransitionContractError(f"{name} must be a finite number")
    return result


def _int(value: object, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise TransitionContractError(f"{name} must be an integer >= {minimum}")
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _canonical_value(value: object) -> Any:
    if value is None or type(value) in {str, bool, int}:
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TransitionContractError("non-finite value in transition snapshot")
        return {"binary64": value.hex()}
    if isinstance(value, (tuple, list)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _canonical_value(value[key]) for key in sorted(value)}
    if is_dataclass(value):
        return {item.name: _canonical_value(getattr(value, item.name)) for item in fields(value)}
    raise TransitionContractError(f"unsupported transition snapshot value: {type(value).__name__}")


def effective_shapes_digest(shapes: Sequence[EffectiveShape]) -> str:
    return _digest({"shapes": [_canonical_value(shape) for shape in shapes]})


def transition_effective_snapshot_json(
    resolution: "TransitionResolution",
    *,
    baseline_effective_digest: str,
) -> str:
    if not _is_sha256(baseline_effective_digest):
        raise TransitionContractError("baseline effective plan digest must be SHA-256")
    payload = {
        "schema_id": "ms32-transition-effective-snapshot/v2" if resolution.schedule is not None else "ms32-transition-effective-snapshot/v1",
        "baseline_effective_digest": baseline_effective_digest,
        "policy_digest": resolution.policy_digest,
        "acoustic_digest": resolution.acoustic_digest,
        "baseline_shapes_digest": resolution.baseline_shapes_digest,
        "resolution_digest": resolution.resolution_digest,
        "resolved_shapes_digest": effective_shapes_digest(resolution.resolved_shapes),
        "resolved_shapes": [_canonical_value(shape) for shape in resolution.resolved_shapes],
    }
    if resolution.schedule is not None:
        payload["schedule"] = _canonical_value(resolution.schedule)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True, slots=True)
class TransitionPolicySnapshot:
    policy_id: str
    b1_contract_sha256: str
    scope: str
    fps: int
    rms_window_ms: float
    rms_hop_ms: float
    rms_smoothing_frames: int
    diagnostic_threshold_rms: float
    minimum_local_peak_ratio: float
    maximum_continuous_overlap_width_delta_frames: float
    maximum_positive_integer_overlap_frame_count_delta: int
    maximum_structural_start_advance_frames: int
    curve_family: str
    maximum_active_morphs: int | None = None
    maximum_release_frames: int | None = None
    short_event_threshold_frames: float | None = None
    short_peak_shift_limit_frames: int | None = None
    short_pulse_support_frames: int | None = None
    short_amplitude_mode: str | None = None

    def __post_init__(self) -> None:
        v2 = self.policy_id == TRANSITION_POLICY_V2
        if self.policy_id not in {TRANSITION_POLICY_ID, TRANSITION_POLICY_V2}:
            raise TransitionContractError("unknown transition policy id")
        if not _is_sha256(self.b1_contract_sha256):
            raise TransitionContractError("B1 contract digest must be lowercase SHA-256")
        if self.scope != "adopted_for_core_evaluation":
            raise TransitionContractError("transition policy scope is not adopted for core evaluation")
        _int(self.fps, "fps", minimum=1)
        _int(self.rms_smoothing_frames, "rms_smoothing_frames", minimum=1)
        _int(
            self.maximum_positive_integer_overlap_frame_count_delta,
            "maximum_positive_integer_overlap_frame_count_delta",
        )
        _int(self.maximum_structural_start_advance_frames, "maximum_structural_start_advance_frames")
        for field_name in (
            "rms_window_ms",
            "rms_hop_ms",
            "diagnostic_threshold_rms",
            "minimum_local_peak_ratio",
            "maximum_continuous_overlap_width_delta_frames",
        ):
            if _number(getattr(self, field_name), field_name) < 0.0:
                raise TransitionContractError(f"{field_name} must be non-negative")
        expected_curve = "piecewise_linear_bounded_vowel_schedule" if v2 else "piecewise_linear_next_start_zero_advance"
        if self.curve_family != expected_curve:
            raise TransitionContractError("unknown transition curve family")
        if self.b1_contract_sha256 != (B4B_CONTRACT_SHA256 if v2 else B1_CONTRACT_SHA256):
            raise TransitionContractError("transition policy is bound to a different B1 contract")
        if (
            self.fps != 30
            or self.rms_window_ms != 25.0
            or self.rms_hop_ms != 10.0
            or self.rms_smoothing_frames != 3
            or self.diagnostic_threshold_rms != 0.01
            or self.minimum_local_peak_ratio != 0.81
            or self.maximum_continuous_overlap_width_delta_frames != 1.0
            or self.maximum_positive_integer_overlap_frame_count_delta != 1
            or self.maximum_structural_start_advance_frames != 1
        ):
            raise TransitionContractError("transition policy parameters differ from the B1 lock")
        extra = (self.maximum_active_morphs, self.maximum_release_frames,
                 self.short_event_threshold_frames, self.short_peak_shift_limit_frames,
                 self.short_pulse_support_frames, self.short_amplitude_mode)
        if extra != ((2, 3, 1.0, 1, 2, "triangle_area_preserving") if v2 else (None,) * 6):
            raise TransitionContractError("schedule parameters differ from the versioned contract")
        if v2 and any(type(x) is not int for x in (self.maximum_active_morphs, self.maximum_release_frames,
                                                  self.short_peak_shift_limit_frames, self.short_pulse_support_frames)):
            raise TransitionContractError("schedule frame/count parameters must be integers")
        if v2:
            _number(self.short_event_threshold_frames, "short_event_threshold_frames")

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_id": "cross-vowel-transition-policy/v2" if self.policy_id == TRANSITION_POLICY_V2 else TRANSITION_POLICY_SCHEMA,
            "policy_id": self.policy_id,
            "b1_contract_sha256": self.b1_contract_sha256,
            "scope": self.scope,
            "fps": self.fps,
            "rms_window_ms": self.rms_window_ms,
            "rms_hop_ms": self.rms_hop_ms,
            "rms_smoothing_frames": self.rms_smoothing_frames,
            "diagnostic_threshold_rms": self.diagnostic_threshold_rms,
            "minimum_local_peak_ratio": self.minimum_local_peak_ratio,
            "maximum_continuous_overlap_width_delta_frames": self.maximum_continuous_overlap_width_delta_frames,
            "maximum_positive_integer_overlap_frame_count_delta": self.maximum_positive_integer_overlap_frame_count_delta,
            "maximum_structural_start_advance_frames": self.maximum_structural_start_advance_frames,
            "curve_family": self.curve_family,
        }
        if self.policy_id == TRANSITION_POLICY_V2:
            for name in ("maximum_active_morphs", "maximum_release_frames", "short_event_threshold_frames",
                         "short_peak_shift_limit_frames", "short_pulse_support_frames", "short_amplitude_mode"):
                payload[name] = getattr(self, name)
        return {**payload, "policy_digest": _digest(payload)}

    @property
    def policy_digest(self) -> str:
        return self.to_dict()["policy_digest"]


def build_adopted_transition_policy() -> TransitionPolicySnapshot:
    """Return the B1-adopted evaluation policy; never reads research files."""
    return TransitionPolicySnapshot(
        policy_id=TRANSITION_POLICY_ID,
        b1_contract_sha256=B1_CONTRACT_SHA256,
        scope="adopted_for_core_evaluation",
        fps=30,
        rms_window_ms=25.0,
        rms_hop_ms=10.0,
        rms_smoothing_frames=3,
        diagnostic_threshold_rms=0.01,
        minimum_local_peak_ratio=0.81,
        maximum_continuous_overlap_width_delta_frames=1.0,
        maximum_positive_integer_overlap_frame_count_delta=1,
        maximum_structural_start_advance_frames=1,
        curve_family="piecewise_linear_next_start_zero_advance",
    )


def read_transition_policy(data: str | bytes | Mapping[str, Any]) -> TransitionPolicySnapshot:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise TransitionContractError(f"duplicate policy key: {key}")
            result[key] = value
        return result

    if isinstance(data, (str, bytes)):
        try:
            raw = json.loads(data, object_pairs_hook=reject_duplicates)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise TransitionContractError("invalid transition policy JSON") from error
    else:
        raw = dict(data)
    expected_fields = {
        "schema_id", "policy_id", "b1_contract_sha256", "scope", "fps", "rms_window_ms",
        "rms_hop_ms", "rms_smoothing_frames", "diagnostic_threshold_rms", "minimum_local_peak_ratio",
        "maximum_continuous_overlap_width_delta_frames", "maximum_positive_integer_overlap_frame_count_delta",
        "maximum_structural_start_advance_frames", "curve_family", "policy_digest",
    }
    v2 = isinstance(raw, dict) and raw.get("schema_id") == "cross-vowel-transition-policy/v2"
    extra_names = ("maximum_active_morphs", "maximum_release_frames", "short_event_threshold_frames",
                   "short_peak_shift_limit_frames", "short_pulse_support_frames", "short_amplitude_mode")
    if v2:
        expected_fields.update(extra_names)
    if type(raw) is not dict or set(raw) != expected_fields or raw["schema_id"] not in {TRANSITION_POLICY_SCHEMA, "cross-vowel-transition-policy/v2"}:
        raise TransitionContractError("transition policy fields do not match the strict schema")
    policy = TransitionPolicySnapshot(
        policy_id=raw["policy_id"],
        b1_contract_sha256=raw["b1_contract_sha256"],
        scope=raw["scope"],
        fps=raw["fps"],
        rms_window_ms=raw["rms_window_ms"],
        rms_hop_ms=raw["rms_hop_ms"],
        rms_smoothing_frames=raw["rms_smoothing_frames"],
        diagnostic_threshold_rms=raw["diagnostic_threshold_rms"],
        minimum_local_peak_ratio=raw["minimum_local_peak_ratio"],
        maximum_continuous_overlap_width_delta_frames=raw["maximum_continuous_overlap_width_delta_frames"],
        maximum_positive_integer_overlap_frame_count_delta=raw["maximum_positive_integer_overlap_frame_count_delta"],
        maximum_structural_start_advance_frames=raw["maximum_structural_start_advance_frames"],
        curve_family=raw["curve_family"],
        **({name: raw[name] for name in extra_names} if v2 else {}),
    )
    if v2 != (policy.policy_id == TRANSITION_POLICY_V2):
        raise TransitionContractError("policy schema and version differ")
    if raw["policy_digest"] != policy.policy_digest:
        raise TransitionContractError("transition policy digest mismatch")
    return policy


def build_bounded_transition_policy() -> TransitionPolicySnapshot:
    """Explicit B4B candidate; does not change the production default."""
    return replace(build_adopted_transition_policy(), policy_id=TRANSITION_POLICY_V2,
                   b1_contract_sha256=B4B_CONTRACT_SHA256,
                   curve_family="piecewise_linear_bounded_vowel_schedule",
                   maximum_active_morphs=2, maximum_release_frames=3,
                   short_event_threshold_frames=1.0, short_peak_shift_limit_frames=1,
                   short_pulse_support_frames=2, short_amplitude_mode="triangle_area_preserving")


@dataclass(frozen=True, slots=True)
class TransitionSourceLineage:
    source_kind: str
    origin_kind: str
    origin_identity: str
    run_id: str
    analysis_generation: str
    input_mode: str
    analysis_wav_sha256: str
    policy_digest: str
    parameter_digest: str
    acoustic_evidence_digest: str
    base_plan_digest: str
    manual_revision: int
    manual_snapshot_digest: str
    effective_plan_digest: str
    resolved_profile_id: str
    output_mapping: tuple[tuple[str, str], ...]
    pair_identity: str
    capture_manifest_sha256: str | None = None
    original_source_sha256: str | None = None
    original_runtime_sha256: str | None = None
    current_runtime_sha256: str | None = None
    compatibility_proof_digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "output_mapping", tuple(tuple(pair) for pair in self.output_mapping))
        if self.source_kind not in TRANSITION_LINEAGE_KINDS:
            raise TransitionContractError("unknown transition source kind")
        for name in (
            "origin_kind", "origin_identity", "run_id", "analysis_generation", "input_mode",
            "resolved_profile_id", "pair_identity"
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise TransitionContractError(f"{name} must be a non-empty string")
        for name in (
            "analysis_wav_sha256", "policy_digest", "parameter_digest", "acoustic_evidence_digest",
            "base_plan_digest", "manual_snapshot_digest", "effective_plan_digest",
        ):
            if not _is_sha256(getattr(self, name)):
                raise TransitionContractError(f"{name} must be lowercase SHA-256")
        _int(self.manual_revision, "manual_revision")
        if not self.output_mapping or any(
            len(pair) != 2 or not all(isinstance(value, str) and value for value in pair)
            for pair in self.output_mapping
        ):
            raise TransitionContractError("output_mapping must contain named pairs")
        if len(set(source for source, _target in self.output_mapping)) != len(self.output_mapping):
            raise TransitionContractError("output_mapping source names must be unique")
        replay_fields = (
            self.capture_manifest_sha256,
            self.original_source_sha256,
            self.original_runtime_sha256,
            self.current_runtime_sha256,
            self.compatibility_proof_digest,
        )
        if self.source_kind == "live_analysis" and any(value is not None for value in replay_fields):
            raise TransitionContractError("live lineage cannot contain replay compatibility fields")
        if self.source_kind == "replayed_capture" and not all(_is_sha256(value) for value in replay_fields):
            raise TransitionContractError("replayed capture lineage requires complete compatibility evidence")

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "source_kind": self.source_kind,
            "origin_kind": self.origin_kind,
            "origin_identity": self.origin_identity,
            "run_id": self.run_id,
            "analysis_generation": self.analysis_generation,
            "input_mode": self.input_mode,
            "analysis_wav_sha256": self.analysis_wav_sha256,
            "policy_digest": self.policy_digest,
            "parameter_digest": self.parameter_digest,
            "acoustic_evidence_digest": self.acoustic_evidence_digest,
            "base_plan_digest": self.base_plan_digest,
            "manual_revision": self.manual_revision,
            "manual_snapshot_digest": self.manual_snapshot_digest,
            "effective_plan_digest": self.effective_plan_digest,
            "resolved_profile_id": self.resolved_profile_id,
            "output_mapping": [list(pair) for pair in self.output_mapping],
            "pair_identity": self.pair_identity,
            "capture_manifest_sha256": self.capture_manifest_sha256,
            "original_source_sha256": self.original_source_sha256,
            "original_runtime_sha256": self.original_runtime_sha256,
            "current_runtime_sha256": self.current_runtime_sha256,
            "compatibility_proof_digest": self.compatibility_proof_digest,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.canonical_payload()
        if self.source_kind == "live_analysis":
            for replay_field in (
                "capture_manifest_sha256", "original_source_sha256", "original_runtime_sha256",
                "current_runtime_sha256", "compatibility_proof_digest",
            ):
                payload.pop(replay_field)
        return {"schema_id": "transition-source-lineage/v1", **payload, "lineage_digest": self.lineage_digest}

    @property
    def lineage_digest(self) -> str:
        return _digest(self.canonical_payload())


def read_transition_source_lineage(data: str | bytes | Mapping[str, Any]) -> TransitionSourceLineage:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise TransitionContractError(f"duplicate lineage key: {key}")
            result[key] = value
        return result

    if isinstance(data, (str, bytes)):
        try:
            raw = json.loads(data, object_pairs_hook=reject_duplicates)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise TransitionContractError("invalid transition source lineage JSON") from error
    else:
        raw = dict(data)
    if isinstance(raw, dict) and raw.get("schema_id") == "transition-source-lineage/v2":
        from src.core.bounded_transition import read_bounded_capture_lineage
        return read_bounded_capture_lineage(raw)
    if type(raw) is not dict or raw.get("schema_id") != "transition-source-lineage/v1":
        raise TransitionContractError("unknown transition source lineage schema")
    kind = raw.get("source_kind")
    base_fields = {
        "schema_id", "source_kind", "origin_kind", "origin_identity", "analysis_wav_sha256",
        "run_id", "analysis_generation", "input_mode",
        "policy_digest", "parameter_digest", "acoustic_evidence_digest", "base_plan_digest",
        "manual_revision", "manual_snapshot_digest", "effective_plan_digest", "resolved_profile_id",
        "output_mapping", "pair_identity", "lineage_digest",
    }
    replay_fields = {
        "capture_manifest_sha256", "original_source_sha256", "original_runtime_sha256",
        "current_runtime_sha256", "compatibility_proof_digest",
    }
    expected = base_fields if kind == "live_analysis" else base_fields | replay_fields
    if set(raw) != expected:
        raise TransitionContractError("lineage fields do not match the kind-specific strict schema")
    if type(raw["output_mapping"]) is not list or any(
        type(item) is not list or len(item) != 2 for item in raw["output_mapping"]
    ):
        raise TransitionContractError("output_mapping must be an array of pairs")
    lineage = TransitionSourceLineage(
        source_kind=kind,
        origin_kind=raw["origin_kind"],
        origin_identity=raw["origin_identity"],
        run_id=raw["run_id"],
        analysis_generation=raw["analysis_generation"],
        input_mode=raw["input_mode"],
        analysis_wav_sha256=raw["analysis_wav_sha256"],
        policy_digest=raw["policy_digest"],
        parameter_digest=raw["parameter_digest"],
        acoustic_evidence_digest=raw["acoustic_evidence_digest"],
        base_plan_digest=raw["base_plan_digest"],
        manual_revision=raw["manual_revision"],
        manual_snapshot_digest=raw["manual_snapshot_digest"],
        effective_plan_digest=raw["effective_plan_digest"],
        resolved_profile_id=raw["resolved_profile_id"],
        output_mapping=tuple(tuple(item) for item in raw["output_mapping"]),
        pair_identity=raw["pair_identity"],
        capture_manifest_sha256=raw.get("capture_manifest_sha256"),
        original_source_sha256=raw.get("original_source_sha256"),
        original_runtime_sha256=raw.get("original_runtime_sha256"),
        current_runtime_sha256=raw.get("current_runtime_sha256"),
        compatibility_proof_digest=raw.get("compatibility_proof_digest"),
    )
    if raw["lineage_digest"] != lineage.lineage_digest:
        raise TransitionContractError("transition source lineage digest mismatch")
    return lineage


@dataclass(frozen=True, slots=True)
class TransitionInputSnapshot:
    run_id: str
    analysis_generation: str
    manual_revision: int
    input_mode: str
    analysis_wav_sha256: str
    base_plan_digest: str
    policy: TransitionPolicySnapshot
    acoustic: TransitionAcousticSnapshot

    def __post_init__(self) -> None:
        for name in ("run_id", "analysis_generation", "input_mode"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise TransitionContractError(f"{name} must be a non-empty string")
        _int(self.manual_revision, "manual_revision")
        if not _is_sha256(self.analysis_wav_sha256) or not _is_sha256(self.base_plan_digest):
            raise TransitionContractError("analysis WAV and base plan identities must be SHA-256")
        if self.acoustic.analysis_wav_sha256 != self.analysis_wav_sha256:
            raise TransitionContractError("acoustic snapshot is bound to a different analysis WAV")
        if self.acoustic.state == "invalid":
            raise TransitionContractError("invalid acoustic snapshot cannot issue transition input")
        if self.policy.b1_contract_sha256 != (B4B_CONTRACT_SHA256 if self.policy.policy_id == TRANSITION_POLICY_V2 else B1_CONTRACT_SHA256):
            raise TransitionContractError("transition input policy is not bound to adopted B1 contract")

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema_id": "transition-input-snapshot/v2" if self.policy.policy_id == TRANSITION_POLICY_V2 else "transition-input-snapshot/v1",
            "run_id": self.run_id,
            "analysis_generation": self.analysis_generation,
            "manual_revision": self.manual_revision,
            "input_mode": self.input_mode,
            "analysis_wav_sha256": self.analysis_wav_sha256,
            "base_plan_digest": self.base_plan_digest,
            "policy": self.policy.to_dict(),
            "acoustic": self.acoustic.to_dict(),
        }

    @property
    def input_digest(self) -> str:
        return _digest(self.canonical_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.canonical_payload()
        return {**payload, "input_digest": _digest(payload)}


def read_transition_input_snapshot(data: str | bytes | Mapping[str, Any]) -> TransitionInputSnapshot:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise TransitionContractError(f"duplicate transition input key: {key}")
            result[key] = value
        return result

    if isinstance(data, (str, bytes)):
        try:
            raw = json.loads(data, object_pairs_hook=reject_duplicates)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise TransitionContractError("invalid transition input JSON") from error
    else:
        raw = dict(data)
    fields = {
        "schema_id", "run_id", "analysis_generation", "manual_revision", "input_mode",
        "analysis_wav_sha256", "base_plan_digest", "policy", "acoustic", "input_digest",
    }
    if type(raw) is not dict or set(raw) != fields or raw["schema_id"] not in {"transition-input-snapshot/v1", "transition-input-snapshot/v2"}:
        raise TransitionContractError("transition input fields do not match the strict schema")
    policy = read_transition_policy(raw["policy"])
    acoustic = read_transition_acoustic_snapshot(raw["acoustic"])
    snapshot = TransitionInputSnapshot(
        run_id=raw["run_id"],
        analysis_generation=raw["analysis_generation"],
        manual_revision=raw["manual_revision"],
        input_mode=raw["input_mode"],
        analysis_wav_sha256=raw["analysis_wav_sha256"],
        base_plan_digest=raw["base_plan_digest"],
        policy=policy,
        acoustic=acoustic,
    )
    if raw["schema_id"] != snapshot.canonical_payload()["schema_id"]:
        raise TransitionContractError("transition input schema and policy differ")
    if raw["input_digest"] != snapshot.input_digest:
        raise TransitionContractError("transition input digest mismatch")
    return snapshot


@dataclass(frozen=True, slots=True)
class TransitionPairInput:
    previous_event_index: int
    next_event_index: int
    previous_vowel: str
    next_vowel: str
    previous_morph: str
    next_morph: str
    previous_shape_index: int
    next_shape_index: int
    previous_event_peak_frame: int
    previous_event_terminal_frame: int
    next_event_start_frame: int
    next_event_peak_frame: int
    previous_same_morph_terminal_frame: int | None
    acoustic_window_start_sec: float
    acoustic_window_end_sec: float
    event_kind: str
    automatic: bool
    manual_or_unknown_owner: bool
    ownership_resolved: bool
    existing_handoff: bool
    core_overlap: bool
    independent_required_zero: bool
    target_required_zero_frames: tuple[int, ...]
    silence_core_frame_ranges: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        _int(self.previous_event_index, "previous_event_index")
        _int(self.next_event_index, "next_event_index")
        _int(self.previous_shape_index, "previous_shape_index")
        _int(self.next_shape_index, "next_shape_index")
        for name in (
            "previous_event_peak_frame", "previous_event_terminal_frame", "next_event_start_frame", "next_event_peak_frame"
        ):
            _int(getattr(self, name), name)
        if self.previous_same_morph_terminal_frame is not None:
            _int(self.previous_same_morph_terminal_frame, "previous_same_morph_terminal_frame")
        for name in (
            "previous_vowel", "next_vowel", "previous_morph", "next_morph"
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise TransitionContractError(f"{name} must be a non-empty string")
        if self.event_kind not in {"normal", "group", "long_vowel", "boundary_only"}:
            raise TransitionContractError("unknown transition event kind")
        for name in ("automatic", "manual_or_unknown_owner", "ownership_resolved", "existing_handoff", "core_overlap", "independent_required_zero"):
            if type(getattr(self, name)) is not bool:
                raise TransitionContractError(f"{name} must be boolean")
        object.__setattr__(self, "target_required_zero_frames", tuple(self.target_required_zero_frames))
        object.__setattr__(self, "silence_core_frame_ranges", tuple(tuple(item) for item in self.silence_core_frame_ranges))
        for frame in self.target_required_zero_frames:
            _int(frame, "target_required_zero_frames[]")
        for start, end in self.silence_core_frame_ranges:
            _int(start, "silence_core_frame_ranges.start")
            _int(end, "silence_core_frame_ranges.end")
            if end < start:
                raise TransitionContractError("silence core range is reversed")
        _number(self.acoustic_window_start_sec, "acoustic_window_start_sec")
        _number(self.acoustic_window_end_sec, "acoustic_window_end_sec")


@dataclass(frozen=True, slots=True)
class TransitionDecision:
    previous_event_index: int
    next_event_index: int
    previous_morph: str
    next_morph: str
    state: str
    reason: str | None
    baseline_start_frame: int
    candidate_start_frame: int
    start_advance_frames: int
    baseline_overlap_width_frames: float
    candidate_overlap_width_frames: float
    overlap_width_delta_frames: float
    baseline_positive_integer_frames: tuple[int, ...]
    candidate_positive_integer_frames: tuple[int, ...]
    local_peak_ratio: float | None


@dataclass(frozen=True, slots=True)
class TransitionResolution:
    policy_digest: str
    acoustic_digest: str
    baseline_shapes_digest: str
    decisions: tuple[TransitionDecision, ...]
    resolved_shapes: tuple[EffectiveShape, ...]
    schedule: object | None = None

    @property
    def resolution_digest(self) -> str:
        payload = {
            "policy_digest": self.policy_digest,
            "acoustic_digest": self.acoustic_digest,
            "baseline_shapes_digest": self.baseline_shapes_digest,
            "decisions": [
                {
                    "previous_event_index": item.previous_event_index,
                    "next_event_index": item.next_event_index,
                    "previous_morph": item.previous_morph,
                    "next_morph": item.next_morph,
                    "state": item.state,
                    "reason": item.reason,
                    "baseline_start_frame": item.baseline_start_frame,
                    "candidate_start_frame": item.candidate_start_frame,
                    "start_advance_frames": item.start_advance_frames,
                    "baseline_overlap_width_frames": item.baseline_overlap_width_frames,
                    "candidate_overlap_width_frames": item.candidate_overlap_width_frames,
                    "overlap_width_delta_frames": item.overlap_width_delta_frames,
                    "baseline_positive_integer_frames": list(item.baseline_positive_integer_frames),
                    "candidate_positive_integer_frames": list(item.candidate_positive_integer_frames),
                    "local_peak_ratio": item.local_peak_ratio,
                }
                for item in self.decisions
            ],
            "resolved_shapes": [
                {
                    "vowel": shape.vowel,
                    "shape_kind": shape.shape_kind,
                    "points": [[point.frame_no, point.value, point.point_kind] for point in shape.control_points],
                }
                for shape in self.resolved_shapes
            ],
        }
        if self.schedule is not None:
            payload["schedule"] = _canonical_value(self.schedule)
        return _digest(payload)


@dataclass(frozen=True, slots=True)
class TransitionValidationResult:
    state: str
    issues: tuple[str, ...]
    resolution_digest: str | None


@dataclass(frozen=True, slots=True)
class _PairProposal:
    pair: TransitionPairInput
    decision: TransitionDecision
    target_shape: EffectiveShape | None
    candidate_points: tuple[ShapeControlPoint, ...] | None
    change_start: int
    change_end: int


def _shape_value(points: Sequence[ShapeControlPoint], frame: float) -> float | None:
    if not points or frame < points[0].frame_no or frame > points[-1].frame_no:
        return None
    for point in points:
        if frame == point.frame_no:
            return point.value
    for left, right in zip(points, points[1:]):
        if left.frame_no <= frame <= right.frame_no:
            if right.frame_no == left.frame_no:
                return right.value
            fraction = (frame - left.frame_no) / (right.frame_no - left.frame_no)
            return left.value + (right.value - left.value) * fraction
    return None


def _positive_overlap(
    left: Sequence[ShapeControlPoint],
    right: Sequence[ShapeControlPoint],
    *,
    start_frame: int,
    end_frame: int,
) -> tuple[float, tuple[int, ...]]:
    low = max(float(start_frame), float(left[0].frame_no), float(right[0].frame_no))
    high = min(float(end_frame), float(left[-1].frame_no), float(right[-1].frame_no))
    if high <= low:
        return 0.0, ()
    breaks = {low, high}
    for points in (left, right):
        for point in points:
            if low < point.frame_no < high:
                breaks.add(float(point.frame_no))
        for a, b in zip(points, points[1:]):
            if b.frame_no <= low or a.frame_no >= high or b.value == a.value:
                continue
            fraction = -a.value / (b.value - a.value)
            if 0.0 < fraction < 1.0:
                root = a.frame_no + (b.frame_no - a.frame_no) * fraction
                if low < root < high:
                    breaks.add(float(root))
    ordered = sorted(breaks)
    width = 0.0
    for start, end in zip(ordered, ordered[1:]):
        midpoint = (start + end) / 2.0
        left_value = _shape_value(left, midpoint)
        right_value = _shape_value(right, midpoint)
        if left_value is not None and right_value is not None and left_value > 0.0 and right_value > 0.0:
            width += end - start
    positive_frames = tuple(
        frame
        for frame in range(start_frame, end_frame + 1)
        if (_shape_value(left, float(frame)) or 0.0) > 0.0
        and (_shape_value(right, float(frame)) or 0.0) > 0.0
    )
    return width, positive_frames


def _inside_ranges(frame: int, ranges: Sequence[tuple[int, int]]) -> bool:
    return any(start <= frame <= end for start, end in ranges)


def _base_decision(pair: TransitionPairInput, reason: str) -> TransitionDecision:
    return TransitionDecision(
        previous_event_index=pair.previous_event_index,
        next_event_index=pair.next_event_index,
        previous_morph=pair.previous_morph,
        next_morph=pair.next_morph,
        state="not_applicable",
        reason=reason,
        baseline_start_frame=pair.next_event_start_frame,
        candidate_start_frame=pair.next_event_start_frame,
        start_advance_frames=0,
        baseline_overlap_width_frames=0.0,
        candidate_overlap_width_frames=0.0,
        overlap_width_delta_frames=0.0,
        baseline_positive_integer_frames=(),
        candidate_positive_integer_frames=(),
        local_peak_ratio=None,
    )


def _ineligibility_reason(pair: TransitionPairInput) -> str | None:
    if pair.next_event_index != pair.previous_event_index + 1:
        return "non_adjacent_events"
    if pair.previous_vowel == pair.next_vowel:
        return "same_vowel"
    if not pair.automatic:
        return "event_not_automatic"
    if pair.manual_or_unknown_owner:
        return "manual_or_unknown_owner"
    if pair.event_kind != "normal":
        return "role_not_eligible"
    if not pair.ownership_resolved:
        return "unresolved_owner"
    if pair.existing_handoff:
        return "existing_handoff"
    if pair.core_overlap:
        return "silence_core_overlap"
    if pair.independent_required_zero:
        return "independent_required_zero"
    return None


def _derive_proposal(
    policy: TransitionPolicySnapshot,
    acoustic: TransitionAcousticSnapshot,
    pair: TransitionPairInput,
    shapes: Sequence[EffectiveShape],
) -> _PairProposal:
    reason = _ineligibility_reason(pair)
    if reason is not None:
        return _PairProposal(pair, _base_decision(pair, reason), None, None, 0, -1)
    covered, local_ratio, acoustic_reason = measure_acoustic_window(
        acoustic,
        start_sec=pair.acoustic_window_start_sec,
        end_sec=pair.acoustic_window_end_sec,
    )
    if not covered:
        decision = replace(_base_decision(pair, acoustic_reason or "rms_unobserved"), local_peak_ratio=local_ratio)
        return _PairProposal(pair, decision, None, None, 0, -1)
    if pair.previous_shape_index >= len(shapes) or pair.next_shape_index >= len(shapes):
        decision = _base_decision(pair, "unresolved_owner")
        return _PairProposal(pair, decision, None, None, 0, -1)
    previous_shape = shapes[pair.previous_shape_index]
    next_shape = shapes[pair.next_shape_index]
    starts = [point for point in next_shape.control_points if point.point_kind == "start_zero"]
    if not starts:
        decision = _base_decision(pair, "structural_start_zero_missing")
        return _PairProposal(pair, decision, next_shape, None, 0, -1)
    if len(starts) != 1 or starts[0].frame_no != pair.next_event_start_frame:
        decision = _base_decision(pair, "structural_start_zero_ambiguous")
        return _PairProposal(pair, decision, next_shape, None, 0, -1)
    baseline_start = pair.next_event_start_frame
    if baseline_start in pair.target_required_zero_frames:
        decision = _base_decision(pair, "start_zero_has_independent_owner")
        return _PairProposal(pair, decision, next_shape, None, baseline_start - 1, baseline_start)
    if (
        pair.previous_event_peak_frame > pair.previous_event_terminal_frame
        or pair.next_event_start_frame > pair.next_event_peak_frame
    ):
        decision = _base_decision(pair, "source_event_geometry_invalid")
        return _PairProposal(pair, decision, next_shape, None, baseline_start - 1, baseline_start)
    lower_bound = max(
        pair.previous_event_peak_frame,
        pair.previous_same_morph_terminal_frame
        if pair.previous_same_morph_terminal_frame is not None
        else pair.previous_event_peak_frame,
    )
    start_capacity = max(0, baseline_start - lower_bound)
    if start_capacity < 1:
        decision = _base_decision(pair, "candidate_start_capacity_insufficient")
        return _PairProposal(pair, decision, next_shape, None, baseline_start - 1, baseline_start)
    previous_fall_capacity = max(0, pair.previous_event_terminal_frame - pair.previous_event_peak_frame)
    if previous_fall_capacity < 1:
        decision = _base_decision(pair, "previous_fall_capacity_insufficient")
        return _PairProposal(pair, decision, next_shape, None, baseline_start - 1, baseline_start)
    next_rise_capacity = max(0, pair.next_event_peak_frame - baseline_start)
    if next_rise_capacity < 1:
        decision = _base_decision(pair, "next_rise_capacity_insufficient")
        return _PairProposal(pair, decision, next_shape, None, baseline_start - 1, baseline_start)
    candidate_start = baseline_start - 1
    if _inside_ranges(candidate_start, pair.silence_core_frame_ranges):
        decision = _base_decision(pair, "candidate_window_in_silence_core")
        return _PairProposal(pair, decision, next_shape, None, candidate_start, baseline_start)
    available_frames = min(start_capacity, previous_fall_capacity, next_rise_capacity, 1)
    if available_frames != 1 or policy.maximum_structural_start_advance_frames != 1:
        decision = _base_decision(pair, "candidate_start_capacity_insufficient")
        return _PairProposal(pair, decision, next_shape, None, candidate_start, baseline_start)
    next_points = list(next_shape.control_points)
    start_index = next_points.index(starts[0])
    if start_index + 1 >= len(next_points) or next_points[start_index + 1].frame_no <= candidate_start:
        decision = _base_decision(pair, "source_event_geometry_invalid")
        return _PairProposal(pair, decision, next_shape, None, candidate_start, baseline_start)
    next_points.pop(start_index)
    if any(point.frame_no == candidate_start for point in next_points):
        decision = _base_decision(pair, "structural_start_zero_ambiguous")
        return _PairProposal(pair, decision, next_shape, None, candidate_start, baseline_start)
    next_points.append(ShapeControlPoint(candidate_start, 0.0, "start_zero"))
    next_points.sort(key=lambda point: point.frame_no)
    if any(left.frame_no >= right.frame_no for left, right in zip(next_points, next_points[1:])):
        decision = _base_decision(pair, "structural_start_zero_ambiguous")
        return _PairProposal(pair, decision, next_shape, None, candidate_start, baseline_start)
    baseline_width, baseline_frames = _positive_overlap(
        previous_shape.control_points,
        next_shape.control_points,
        start_frame=pair.previous_event_peak_frame,
        end_frame=pair.next_event_peak_frame,
    )
    candidate_width, candidate_frames = _positive_overlap(
        previous_shape.control_points,
        next_points,
        start_frame=pair.previous_event_peak_frame,
        end_frame=pair.next_event_peak_frame,
    )
    width_delta = candidate_width - baseline_width
    frame_delta = len(candidate_frames) - len(baseline_frames)
    if width_delta <= 1e-9:
        reason = "candidate_overlap_not_increased"
    elif width_delta > policy.maximum_continuous_overlap_width_delta_frames + 1e-9:
        reason = "continuous_overlap_width_delta_exceeded"
    elif frame_delta > policy.maximum_positive_integer_overlap_frame_count_delta:
        reason = "positive_integer_frame_delta_exceeded"
    else:
        reason = None
    decision = TransitionDecision(
        previous_event_index=pair.previous_event_index,
        next_event_index=pair.next_event_index,
        previous_morph=pair.previous_morph,
        next_morph=pair.next_morph,
        state="applied" if reason is None else "not_applicable",
        reason=reason,
        baseline_start_frame=baseline_start,
        candidate_start_frame=candidate_start if reason is None else baseline_start,
        start_advance_frames=1 if reason is None else 0,
        baseline_overlap_width_frames=baseline_width,
        candidate_overlap_width_frames=candidate_width if reason is None else baseline_width,
        overlap_width_delta_frames=width_delta if reason is None else 0.0,
        baseline_positive_integer_frames=baseline_frames,
        candidate_positive_integer_frames=candidate_frames if reason is None else baseline_frames,
        local_peak_ratio=local_ratio,
    )
    return _PairProposal(
        pair,
        decision,
        next_shape,
        tuple(next_points) if reason is None else None,
        candidate_start,
        baseline_start,
    )


def resolve_cross_vowel_transition(
    *,
    policy: TransitionPolicySnapshot,
    acoustic_snapshot: TransitionAcousticSnapshot,
    pairs: Sequence[TransitionPairInput],
    shapes: Sequence[EffectiveShape],
) -> TransitionResolution:
    """Resolve only explicitly supplied original-adjacency pair geometry."""
    proposals = [
        _derive_proposal(policy, acoustic_snapshot, pair, shapes)
        for pair in pairs
    ]
    conflicts: set[int] = set()
    for left_index, left in enumerate(proposals):
        if left.candidate_points is None:
            continue
        for right_index in range(left_index + 1, len(proposals)):
            right = proposals[right_index]
            if right.candidate_points is None or left.pair.next_morph != right.pair.next_morph:
                continue
            if max(left.change_start, right.change_start) <= min(left.change_end, right.change_end):
                conflicts.update((left_index, right_index))
    resolved = list(shapes)
    decisions: list[TransitionDecision] = []
    for index, proposal in enumerate(proposals):
        decision = proposal.decision
        if index in conflicts:
            decision = replace(
                decision,
                state="not_applicable",
                reason="neighbor_transition_conflict",
                candidate_start_frame=decision.baseline_start_frame,
                start_advance_frames=0,
                candidate_overlap_width_frames=decision.baseline_overlap_width_frames,
                overlap_width_delta_frames=0.0,
                candidate_positive_integer_frames=decision.baseline_positive_integer_frames,
            )
        elif proposal.candidate_points is not None and proposal.target_shape is not None:
            resolved[proposal.pair.next_shape_index] = replace(
                proposal.target_shape,
                control_points=proposal.candidate_points,
            )
        decisions.append(decision)
    return TransitionResolution(
        policy_digest=policy.policy_digest,
        acoustic_digest=acoustic_snapshot.content_digest,
        baseline_shapes_digest=effective_shapes_digest(shapes),
        decisions=tuple(decisions),
        resolved_shapes=tuple(resolved),
    )


def _independent_expected_proposal(
    policy: TransitionPolicySnapshot,
    acoustic: TransitionAcousticSnapshot,
    pair: TransitionPairInput,
    shapes: Sequence[EffectiveShape],
) -> _PairProposal:
    """Validator oracle; intentionally does not call the producer's resolver."""
    reason: str | None = None
    if pair.next_event_index != pair.previous_event_index + 1:
        reason = "non_adjacent_events"
    elif pair.previous_vowel == pair.next_vowel:
        reason = "same_vowel"
    elif not pair.automatic:
        reason = "event_not_automatic"
    elif pair.manual_or_unknown_owner:
        reason = "manual_or_unknown_owner"
    elif pair.event_kind != "normal":
        reason = "role_not_eligible"
    elif not pair.ownership_resolved:
        reason = "unresolved_owner"
    elif pair.existing_handoff:
        reason = "existing_handoff"
    elif pair.core_overlap:
        reason = "silence_core_overlap"
    elif pair.independent_required_zero:
        reason = "independent_required_zero"
    if reason is not None:
        return _PairProposal(pair, _base_decision(pair, reason), None, None, 0, -1)

    acoustic_ok, peak_ratio, acoustic_reason = measure_acoustic_window(
        acoustic,
        start_sec=pair.acoustic_window_start_sec,
        end_sec=pair.acoustic_window_end_sec,
    )
    if not acoustic_ok:
        return _PairProposal(
            pair,
            replace(_base_decision(pair, acoustic_reason or "rms_unobserved"), local_peak_ratio=peak_ratio),
            None,
            None,
            0,
            -1,
        )
    if not (0 <= pair.previous_shape_index < len(shapes)) or not (0 <= pair.next_shape_index < len(shapes)):
        return _PairProposal(pair, _base_decision(pair, "unresolved_owner"), None, None, 0, -1)

    previous = shapes[pair.previous_shape_index]
    target = shapes[pair.next_shape_index]
    zero_points = [point for point in target.control_points if point.point_kind == "start_zero"]
    if not zero_points:
        return _PairProposal(pair, _base_decision(pair, "structural_start_zero_missing"), target, None, 0, -1)
    if len(zero_points) != 1 or zero_points[0].frame_no != pair.next_event_start_frame:
        return _PairProposal(pair, _base_decision(pair, "structural_start_zero_ambiguous"), target, None, 0, -1)
    baseline_start = pair.next_event_start_frame
    candidate_start = baseline_start - 1
    if baseline_start in pair.target_required_zero_frames:
        return _PairProposal(pair, _base_decision(pair, "start_zero_has_independent_owner"), target, None, candidate_start, baseline_start)
    if pair.previous_event_peak_frame > pair.previous_event_terminal_frame or baseline_start > pair.next_event_peak_frame:
        return _PairProposal(pair, _base_decision(pair, "source_event_geometry_invalid"), target, None, candidate_start, baseline_start)

    earlier_terminal = pair.previous_same_morph_terminal_frame
    earliest_allowed = max(
        pair.previous_event_peak_frame,
        pair.previous_event_peak_frame if earlier_terminal is None else earlier_terminal,
    )
    start_capacity = baseline_start - earliest_allowed
    if start_capacity < 1:
        return _PairProposal(pair, _base_decision(pair, "candidate_start_capacity_insufficient"), target, None, candidate_start, baseline_start)
    fall_capacity = pair.previous_event_terminal_frame - pair.previous_event_peak_frame
    if fall_capacity < 1:
        return _PairProposal(pair, _base_decision(pair, "previous_fall_capacity_insufficient"), target, None, candidate_start, baseline_start)
    rise_capacity = pair.next_event_peak_frame - baseline_start
    if rise_capacity < 1:
        return _PairProposal(pair, _base_decision(pair, "next_rise_capacity_insufficient"), target, None, candidate_start, baseline_start)
    candidate_frames_outside_core = sum(
        1 for frame in range(candidate_start, baseline_start)
        if not _inside_ranges(frame, pair.silence_core_frame_ranges)
    )
    available = min(start_capacity, fall_capacity, rise_capacity, candidate_frames_outside_core)
    advance = min(policy.maximum_structural_start_advance_frames, available)
    if advance != 1:
        reason = "candidate_window_in_silence_core" if candidate_frames_outside_core == 0 else "candidate_start_capacity_insufficient"
        return _PairProposal(pair, _base_decision(pair, reason), target, None, candidate_start, baseline_start)

    target_points = list(target.control_points)
    zero_index = target_points.index(zero_points[0])
    target_points.pop(zero_index)
    if any(point.frame_no == candidate_start for point in target_points):
        return _PairProposal(pair, _base_decision(pair, "structural_start_zero_ambiguous"), target, None, candidate_start, baseline_start)
    target_points.append(ShapeControlPoint(candidate_start, 0.0, "start_zero"))
    target_points.sort(key=lambda point: point.frame_no)
    if any(left.frame_no >= right.frame_no for left, right in zip(target_points, target_points[1:])):
        return _PairProposal(pair, _base_decision(pair, "structural_start_zero_ambiguous"), target, None, candidate_start, baseline_start)

    baseline_width, baseline_frames = _positive_overlap(
        previous.control_points,
        target.control_points,
        start_frame=pair.previous_event_peak_frame,
        end_frame=pair.next_event_peak_frame,
    )
    candidate_width, candidate_frames = _positive_overlap(
        previous.control_points,
        target_points,
        start_frame=pair.previous_event_peak_frame,
        end_frame=pair.next_event_peak_frame,
    )
    delta = candidate_width - baseline_width
    positive_count_delta = len(candidate_frames) - len(baseline_frames)
    if delta <= 1e-9:
        reason = "candidate_overlap_not_increased"
    elif delta > policy.maximum_continuous_overlap_width_delta_frames + 1e-9:
        reason = "continuous_overlap_width_delta_exceeded"
    elif positive_count_delta > policy.maximum_positive_integer_overlap_frame_count_delta:
        reason = "positive_integer_frame_delta_exceeded"
    else:
        reason = None
    decision = TransitionDecision(
        previous_event_index=pair.previous_event_index,
        next_event_index=pair.next_event_index,
        previous_morph=pair.previous_morph,
        next_morph=pair.next_morph,
        state="applied" if reason is None else "not_applicable",
        reason=reason,
        baseline_start_frame=baseline_start,
        candidate_start_frame=candidate_start if reason is None else baseline_start,
        start_advance_frames=advance if reason is None else 0,
        baseline_overlap_width_frames=baseline_width,
        candidate_overlap_width_frames=candidate_width if reason is None else baseline_width,
        overlap_width_delta_frames=delta if reason is None else 0.0,
        baseline_positive_integer_frames=baseline_frames,
        candidate_positive_integer_frames=candidate_frames if reason is None else baseline_frames,
        local_peak_ratio=peak_ratio,
    )
    return _PairProposal(
        pair,
        decision,
        target,
        tuple(target_points) if reason is None else None,
        candidate_start,
        baseline_start,
    )


def validate_transition_resolution(
    *,
    policy: TransitionPolicySnapshot | None,
    acoustic_snapshot: TransitionAcousticSnapshot | None,
    pairs: Sequence[TransitionPairInput],
    baseline_shapes: Sequence[EffectiveShape],
    resolution: TransitionResolution | None,
) -> TransitionValidationResult:
    """Independently recompute applicability and the only permitted shape edits."""
    if policy is None or acoustic_snapshot is None or resolution is None:
        return TransitionValidationResult("unavailable", ("transition_validation_input_missing",), None)
    issues: list[str] = []
    if resolution.policy_digest != policy.policy_digest:
        issues.append("policy_digest_mismatch")
    if resolution.acoustic_digest != acoustic_snapshot.content_digest:
        issues.append("acoustic_digest_mismatch")
    if resolution.baseline_shapes_digest != effective_shapes_digest(baseline_shapes):
        issues.append("baseline_shapes_digest_mismatch")
    if len(resolution.decisions) != len(pairs):
        issues.append("transition_record_count_mismatch")
    if len(resolution.resolved_shapes) != len(baseline_shapes):
        issues.append("resolved_shape_count_mismatch")
    if issues:
        return TransitionValidationResult("invalid", tuple(issues), None)

    expected = [
        _independent_expected_proposal(policy, acoustic_snapshot, pair, baseline_shapes)
        for pair in pairs
    ]
    conflicting: set[int] = set()
    for left_index, left in enumerate(expected):
        if left.candidate_points is None:
            continue
        for right_index in range(left_index + 1, len(expected)):
            right = expected[right_index]
            if right.candidate_points is None or left.pair.next_morph != right.pair.next_morph:
                continue
            if max(left.change_start, right.change_start) <= min(left.change_end, right.change_end):
                conflicting.update((left_index, right_index))

    expected_shapes = list(baseline_shapes)
    expected_decisions: list[TransitionDecision] = []
    for index, proposal in enumerate(expected):
        decision = proposal.decision
        if index in conflicting:
            decision = replace(
                decision,
                state="not_applicable",
                reason="neighbor_transition_conflict",
                candidate_start_frame=decision.baseline_start_frame,
                start_advance_frames=0,
                candidate_overlap_width_frames=decision.baseline_overlap_width_frames,
                overlap_width_delta_frames=0.0,
                candidate_positive_integer_frames=decision.baseline_positive_integer_frames,
            )
        elif proposal.candidate_points is not None and proposal.target_shape is not None:
            expected_shapes[proposal.pair.next_shape_index] = replace(
                proposal.target_shape,
                control_points=proposal.candidate_points,
            )
        expected_decisions.append(decision)

    if resolution.decisions != tuple(expected_decisions):
        issues.append("transition_records_do_not_match_independent_expectation")
    if resolution.resolved_shapes != tuple(expected_shapes):
        issues.append("resolved_shapes_contain_unpermitted_changes")
    return TransitionValidationResult(
        "invalid" if issues else "valid",
        tuple(issues),
        resolution.resolution_digest if not issues else None,
    )


def build_transition_pairs_from_effective_plan(
    effective_plan: object,
    *,
    fps: int,
) -> tuple[TransitionPairInput, ...]:
    """Derive only original-order adjacent pairs from a resolved source plan."""
    _int(fps, "fps", minimum=1)
    base_events = tuple(getattr(effective_plan, "base_events", ()))
    effective_events = tuple(getattr(effective_plan, "effective_events", ()))
    shapes = tuple(getattr(effective_plan, "shapes", ()))
    admissions = {
        item.event_index: item
        for item in tuple(getattr(effective_plan, "event_silence_admissions", ()))
    }
    if not base_events or len(base_events) != len(effective_events):
        raise TransitionContractError("complete original and effective events are required")
    if tuple(getattr(item, "base_event_index", None) for item in base_events) != tuple(range(len(base_events))):
        raise TransitionContractError("base events are not in canonical original order")
    if tuple(getattr(item, "base_event_index", None) for item in effective_events) != tuple(range(len(effective_events))):
        raise TransitionContractError("effective events are not in canonical original order")

    def shapes_for_event(event_index: int) -> tuple[int, ...]:
        return tuple(
            index
            for index, shape in enumerate(shapes)
            if event_index in tuple(getattr(shape, "real_base_event_indices", ()))
        )

    def terminal_for_shape(shape: EffectiveShape) -> int:
        tail = getattr(shape, "resolved_tail", None)
        if tail is None:
            return shape.end_frame
        event_index = getattr(tail, "tail_base_event_index", None)
        matching = next(
            (item for item in effective_events if getattr(item, "base_event_index", None) == event_index),
            None,
        )
        if matching is None:
            return shape.end_frame
        return (
            int(getattr(matching, "end_frame"))
            + int(getattr(tail, "effective_hold_frames", 0))
            + int(getattr(tail, "effective_softness_frames", 0))
        )

    adjustment_snapshot = getattr(effective_plan, "canonical_adjustment_snapshot", None)
    manual_events = {
        item.base_event_index
        for item in tuple(getattr(adjustment_snapshot, "adjustments", ()))
        if not getattr(item, "is_empty", False)
    }
    manual_handoffs = {
        (item.source_base_event_index, item.target_base_event_index)
        for item in tuple(getattr(effective_plan, "manual_crossfades", ()))
    }
    normalization = getattr(effective_plan, "normalization_contract", None)
    structural_zero_keys = {
        (shape.vowel, point.frame_no)
        for shape in shapes
        for point in shape.control_points
        if point.point_kind in {"start_zero", "end_zero"} and point.value <= 1e-9
    }
    independent_required: set[tuple[str, int]] = set()
    for admission in admissions.values():
        for start, end in admission.required_zero_frame_ranges:
            independent_required.update((admission.vowel, frame) for frame in range(start, end))
        if admission.boundary_only and admission.boundary_frame is not None:
            independent_required.add((admission.vowel, admission.boundary_frame))
    for start, end in tuple(getattr(effective_plan, "silence_core_frame_ranges", ()) or ()):
        for shape in shapes:
            if shape.start_frame <= start <= shape.end_frame:
                independent_required.add((shape.vowel, start))
            if shape.start_frame <= end <= shape.end_frame:
                independent_required.add((shape.vowel, end))
    if normalization is not None:
        for semantic, frame in normalization.required_zero_frames:
            if (semantic, frame) not in structural_zero_keys:
                independent_required.add((semantic, frame))

    handoff_pairs = {
        (item.previous_non_zero_event_index, item.next_non_zero_event_index)
        for item in tuple(getattr(effective_plan, "observation_handoffs", ()))
        if item.enabled
    }
    result: list[TransitionPairInput] = []
    for previous_index, (previous_base, following_base) in enumerate(zip(base_events, base_events[1:])):
        next_index = previous_index + 1
        previous_event = effective_events[previous_index]
        following_event = effective_events[next_index]
        previous_shape_matches = shapes_for_event(previous_index)
        following_shape_matches = shapes_for_event(next_index)
        previous_shape_index = previous_shape_matches[0] if len(previous_shape_matches) == 1 else 0
        following_shape_index = following_shape_matches[0] if len(following_shape_matches) == 1 else 0
        previous_shape = shapes[previous_shape_index] if shapes else None
        following_shape = shapes[following_shape_index] if shapes else None
        previous_admission = admissions.get(previous_index)
        following_admission = admissions.get(next_index)
        long_event = bool(
            getattr(previous_event, "is_long_vowel_continuation", False)
            or getattr(following_event, "is_long_vowel_continuation", False)
            or getattr(previous_event, "long_vowel_role", None)
            or getattr(following_event, "long_vowel_role", None)
        )
        group_event = bool(
            previous_shape is not None and len(previous_shape.real_base_event_indices) > 1
            or following_shape is not None and len(following_shape.real_base_event_indices) > 1
        )
        boundary_only = bool(
            previous_admission is not None and previous_admission.boundary_only
            or following_admission is not None and following_admission.boundary_only
        )
        event_kind = "long_vowel" if long_event else "group" if group_event else "boundary_only" if boundary_only else "normal"
        next_start = following_shape.start_frame if following_shape is not None else int(getattr(following_event, "start_frame"))
        prior_same_morph_terminals = [
            terminal_for_shape(shape)
            for shape in shapes
            if shape.vowel == getattr(following_event, "vowel", None)
            and any(event_index < previous_index for event_index in shape.real_base_event_indices)
            and not (following_shape is not None and shape is following_shape)
        ]
        previous_terminal = int(getattr(previous_event, "end_frame"))
        previous_terminal_sec = float(getattr(previous_event, "end_sec", previous_terminal / fps))
        next_start_sec = float(
            getattr(following_base, "start_sec", int(getattr(following_base, "start_frame")) / fps)
        )
        acoustic_start = min(previous_terminal_sec, next_start_sec)
        acoustic_end = max(previous_terminal_sec, next_start_sec)
        manual_or_unknown = bool(
            previous_index in manual_events
            or next_index in manual_events
            or previous_admission is not None and previous_admission.manual_adjustment_applied
            or following_admission is not None and following_admission.manual_adjustment_applied
            or previous_shape is None
            or following_shape is None
            or previous_shape and not previous_shape.real_base_event_indices
            or following_shape and not following_shape.real_base_event_indices
        )
        owner_resolved = bool(
            len(previous_shape_matches) == 1
            and len(following_shape_matches) == 1
            and previous_shape is not None
            and following_shape is not None
            and previous_index in previous_shape.real_base_event_indices
            and next_index in following_shape.real_base_event_indices
        )
        existing_handoff = (
            (previous_index, next_index) in manual_handoffs
            or (previous_index, next_index) in handoff_pairs
        )
        core_overlap = bool(
            (previous_admission is not None and previous_admission.base_event_silence_core_overlap)
            or (following_admission is not None and following_admission.base_event_silence_core_overlap)
        )
        target_morph = str(getattr(following_event, "vowel"))
        target_required_zero_frames = tuple(
            frame for semantic, frame in independent_required if semantic == target_morph
        )
        core_ranges = tuple(getattr(effective_plan, "silence_core_frame_ranges", ()) or ())
        result.append(
            TransitionPairInput(
                previous_event_index=previous_index,
                next_event_index=next_index,
                previous_vowel=str(getattr(previous_event, "vowel")),
                next_vowel=target_morph,
                previous_morph=str(getattr(previous_event, "vowel")),
                next_morph=target_morph,
                previous_shape_index=previous_shape_index,
                next_shape_index=following_shape_index,
                previous_event_peak_frame=int(getattr(previous_event, "peak_frame")),
                previous_event_terminal_frame=previous_terminal,
                next_event_start_frame=next_start,
                next_event_peak_frame=int(getattr(following_event, "peak_frame")),
                previous_same_morph_terminal_frame=max(prior_same_morph_terminals) if prior_same_morph_terminals else None,
                acoustic_window_start_sec=acoustic_start,
                acoustic_window_end_sec=acoustic_end,
                event_kind=event_kind,
                automatic=bool(
                    (previous_admission is None or previous_admission.enabled)
                    and (following_admission is None or following_admission.enabled)
                    and not boundary_only
                ),
                manual_or_unknown_owner=manual_or_unknown,
                ownership_resolved=owner_resolved,
                existing_handoff=existing_handoff,
                core_overlap=core_overlap,
                independent_required_zero=(target_morph, next_start) in independent_required,
                target_required_zero_frames=target_required_zero_frames,
                silence_core_frame_ranges=core_ranges,
            )
        )
    return tuple(result)


def apply_transition_resolution_to_effective_plan(
    effective_plan: object,
    resolution: TransitionResolution,
) -> object:
    """Return a new effective plan with permitted start-zero changes reissued."""
    from dataclasses import replace as dataclass_replace

    from src.core.effective_shape_plan import _normalization_contract

    current_shapes = tuple(getattr(effective_plan, "shapes", ()))
    if effective_shapes_digest(current_shapes) != resolution.baseline_shapes_digest:
        raise TransitionContractError("transition resolution does not belong to this effective plan")
    resolved_shapes = resolution.resolved_shapes
    structural = {
        (shape.vowel, point.frame_no)
        for shape in current_shapes
        for point in shape.control_points
        if point.point_kind in {"start_zero", "end_zero"} and point.value <= 1e-9
    }
    independent: set[tuple[str, int]] = set()
    for admission in tuple(getattr(effective_plan, "event_silence_admissions", ())):
        for start, end in admission.required_zero_frame_ranges:
            independent.update((admission.vowel, frame) for frame in range(start, end))
        if admission.boundary_only and admission.boundary_frame is not None:
            independent.add((admission.vowel, admission.boundary_frame))
    for start, end in tuple(getattr(effective_plan, "silence_core_frame_ranges", ()) or ()):
        for shape in resolved_shapes:
            if shape.start_frame <= start <= shape.end_frame:
                independent.add((shape.vowel, start))
            if shape.start_frame <= end <= shape.end_frame:
                independent.add((shape.vowel, end))
    old_contract = getattr(effective_plan, "normalization_contract", None)
    if old_contract is not None:
        independent.update(
            (semantic, frame)
            for semantic, frame in old_contract.required_zero_frames
            if (semantic, frame) not in structural
        )
    normalization = _normalization_contract(
        resolved_shapes,
        additional_required_zero_frames=tuple(independent),
    )
    return dataclass_replace(
        effective_plan,
        shapes=resolved_shapes,
        normalization_contract=normalization,
    )

