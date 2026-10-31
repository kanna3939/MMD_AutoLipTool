"""Isolated MS33-B4C vowel trace and review-only wire candidate.

This module does not participate in the normal output path. It creates an
auditable, local quality artifact and a separately named candidate VMD from an
already validated B4 output. The adopted MS32-B4B policy is never changed.
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
from collections.abc import Mapping, Sequence
from typing import Any

from src.core.canonical_morph_value import canonicalize_morph_value
from src.core.final_morph_shadow import WireReadbackPoint, read_morph_vmd
from src.core.text_processing import VOWELS
from src.vmd_writer import VMD_FPS


SCHEMA_ID = "ms33-b4c-vowel-quality/v1"
CANDIDATE_POLICY_ID = "ms33-b4c-short-vowel-wire-pulse/v1"
MAX_ACTIVE_MORPHS = 2


class B4CVowelQualityError(ValueError):
    """Raised when a B4C trace or isolated candidate cannot be verified."""


def _json_value(value: Any) -> Any:
    if value is None or type(value) in {str, bool, int}:
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {
            name: _json_value(getattr(value, name))
            for name in value.__dataclass_fields__
        }
    return None


def _get(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _require_sha256(value: object, field: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise B4CVowelQualityError(f"{field} must be a lowercase SHA-256")
    return value


def analysis_text_identity(text: str) -> dict[str, object]:
    if type(text) is not str:
        raise B4CVowelQualityError("analysis text must be text")
    return {
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "character_count": len(text),
    }


def _semantic_values(
    points: Sequence[WireReadbackPoint],
    output_mapping: Mapping[str, str],
) -> dict[tuple[int, str], float]:
    name_to_vowel = {name: vowel for vowel, name in output_mapping.items()}
    values: dict[tuple[int, str], float] = {}
    for point in points:
        vowel = name_to_vowel.get(point.morph_name)
        if vowel is None:
            raise B4CVowelQualityError(
                f"VMD contains an unmapped output morph: {point.morph_name!r}"
            )
        key = (point.frame_no, vowel)
        if key in values:
            raise B4CVowelQualityError("VMD readback contains duplicate semantic keys")
        values[key] = float(point.value)
    return values


def _curve_at(values: Mapping[tuple[int, str], float], vowel: str, frame: float) -> float:
    keys = sorted((key_frame, value) for (key_frame, key_vowel), value in values.items() if key_vowel == vowel)
    if not keys:
        return 0.0
    if frame < keys[0][0] or frame > keys[-1][0]:
        return 0.0
    for key_frame, value in keys:
        if frame == key_frame:
            return value
    for (left_frame, left_value), (right_frame, right_value) in zip(keys, keys[1:]):
        if left_frame < frame < right_frame:
            proportion = (frame - left_frame) / (right_frame - left_frame)
            return left_value + (right_value - left_value) * proportion
    return 0.0


def _wire_active_count(values: Mapping[tuple[int, str], float], frame: float) -> int:
    return sum(_curve_at(values, vowel, frame) > 0.0 for vowel in VOWELS)


def _curve_probe_frames(
    *value_maps: Mapping[tuple[int, str], float],
    extra_frames: Sequence[float] = (),
) -> tuple[float, ...]:
    """Return every wire key-frame endpoint and each piecewise interval midpoint."""
    breakpoints = {
        float(frame)
        for values in value_maps
        for frame, _vowel in values
    }
    breakpoints.update(float(frame) for frame in extra_frames)
    ordered = sorted(breakpoints)
    probes = set(ordered)
    probes.update((left + right) / 2.0 for left, right in zip(ordered, ordered[1:]))
    return tuple(sorted(probes))


def _active_morph_limit_exceeded(
    candidate: Mapping[tuple[int, str], float],
    baseline: Mapping[tuple[int, str], float],
    max_active_morphs: int,
) -> bool:
    return any(
        _wire_active_count(candidate, frame) > max_active_morphs
        and _wire_active_count(candidate, frame) > _wire_active_count(baseline, frame)
        for frame in _curve_probe_frames(candidate, baseline)
    )


def _silence_core_curve_changed(
    baseline: Mapping[tuple[int, str], float],
    candidate: Mapping[tuple[int, str], float],
    silence_core_frame_ranges: Sequence[Sequence[int]],
) -> bool:
    ranges: list[tuple[int, int]] = []
    boundaries: list[float] = []
    for item in silence_core_frame_ranges:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise B4CVowelQualityError("silence-core candidate contract is malformed")
        start_frame, end_frame = int(item[0]), int(item[1])
        if end_frame < start_frame:
            raise B4CVowelQualityError("silence-core candidate range is reversed")
        ranges.append((start_frame, end_frame))
        boundaries.extend((float(start_frame), float(end_frame)))
    probes = _curve_probe_frames(baseline, candidate, extra_frames=boundaries)
    return any(
        start_frame <= frame < end_frame
        and any(
            _curve_at(baseline, vowel, frame) != _curve_at(candidate, vowel, frame)
            for vowel in VOWELS
        )
        for start_frame, end_frame in ranges
        for frame in probes
    )


def build_short_event_wire_candidate(
    *,
    timeline: Sequence[Any],
    observations: Sequence[Any],
    source_events: Sequence[Any],
    event_silence_admissions: Sequence[Any],
    silence_core_frame_ranges: Sequence[Sequence[int]],
    required_zero_frames: Sequence[Sequence[Any]],
    wire_points: Sequence[WireReadbackPoint],
    output_mapping: Mapping[str, str],
    source_duration_frames: int,
    max_active_morphs: int = MAX_ACTIVE_MORPHS,
) -> tuple[list[tuple[int, str, float]], list[dict[str, Any]]]:
    """Return an opt-in short-event candidate and explicit decisions.

    A candidate is limited to a source-positive event shorter than one frame
    whose own rounded wire position remains zero. It may be a member of a
    same-vowel envelope, but the event itself must have a token identity and
    must not be a long-vowel continuation. The pulse is placed one frame after
    its source peak when needed to make a two-morph transition possible.
    """
    if not isinstance(source_duration_frames, int) or source_duration_frames < 0:
        raise B4CVowelQualityError("source duration must be a non-negative frame count")
    if not isinstance(max_active_morphs, int) or max_active_morphs < 1:
        raise B4CVowelQualityError("active morph limit must be positive")
    mapping = dict(output_mapping)
    if tuple(mapping) != VOWELS or any(type(name) is not str or not name for name in mapping.values()):
        raise B4CVowelQualityError("output mapping must contain the five vowels in fixed order")

    values = _semantic_values(wire_points, mapping)
    baseline_values = dict(values)
    events = {int(_get(item, "base_event_index", index)): item for index, item in enumerate(source_events)}
    observations_by_index = {
        int(_get(item, "event_index", index)): item for index, item in enumerate(observations)
    }
    admissions_by_index = {
        int(_get(item, "event_index", index)): item
        for index, item in enumerate(event_silence_admissions)
    }
    timeline_by_index = {index: item for index, item in enumerate(timeline)}
    required = {
        (int(item[0]), str(item[1]))
        for item in required_zero_frames
        if isinstance(item, (tuple, list)) and len(item) == 2
    }
    core_ranges = tuple(tuple(int(part) for part in item) for item in silence_core_frame_ranges)

    decisions: list[dict[str, Any]] = []
    ordered_events = sorted(events.items())
    for event_index, source_event in ordered_events:
        point = timeline_by_index.get(event_index)
        if point is None:
            continue
        vowel = str(_get(source_event, "vowel", _get(point, "vowel", "")))
        peak_value = float(_get(source_event, "peak_value", _get(point, "peak_value", 0.0)) or 0.0)
        start_sec = float(_get(point, "start_sec", 0.0) or 0.0)
        end_sec = float(_get(point, "end_sec", start_sec) or start_sec)
        time_sec = float(_get(point, "time_sec", start_sec) or start_sec)
        width_frames = max(0.0, end_sec - start_sec) * VMD_FPS
        token_index = _get(point, "vowel_token_index", _get(source_event, "vowel_token_index"))
        peak_frame = int(_get(source_event, "peak_frame", round(time_sec * VMD_FPS)))
        observation = observations_by_index.get(event_index)
        admission = admissions_by_index.get(event_index)
        observation_reason = _get(observation, "reason") if observation is not None else None
        local_peak = _get(observation, "local_peak") if observation is not None else None
        rms_values = tuple(_get(observation, "rms_window_values", ()) or ()) if observation is not None else ()
        decision: dict[str, Any] = {
            "event_index": event_index,
            "token_index": token_index,
            "vowel": vowel,
            "source_peak_value": peak_value,
            "acoustic_local_peak": local_peak,
            "acoustic_rms_window_values": list(rms_values),
            "observation_zero_reason": observation_reason,
            "silence_core_overlap": bool(_get(admission, "base_event_silence_core_overlap", False)),
            "manual_adjustment_applied": bool(_get(admission, "manual_adjustment_applied", False)),
            "boundary_only": bool(_get(admission, "boundary_only", False)),
            "duration_frames": width_frames,
            "source_peak_frame": peak_frame,
            "group_event_indices": list(_get(source_event, "group_event_indices", (event_index,)) or (event_index,)),
            "candidate_state": "not_applicable",
            "reason": None,
            "selected_frame": None,
            "candidate_peak_value": None,
            "candidate_attempts": [],
        }
        if vowel not in VOWELS or token_index is None:
            decision.update(candidate_state="not_applied", reason="token_identity_unavailable")
        elif peak_value <= 0.0:
            decision.update(candidate_state="not_applied", reason="source_peak_zero")
        elif bool(_get(source_event, "is_long_vowel_continuation", False)) or _get(source_event, "long_vowel_role"):
            decision.update(candidate_state="not_applied", reason="long_vowel_protected")
        elif width_frames >= 1.0:
            decision.update(candidate_state="not_applied", reason="event_not_subframe")
        elif admission is None:
            decision.update(candidate_state="not_applied", reason="event_provenance_unavailable")
        elif observation is None:
            decision.update(candidate_state="not_applied", reason="acoustic_observation_unavailable")
        elif bool(_get(admission, "manual_adjustment_applied", False)):
            decision.update(candidate_state="not_applied", reason="manual_adjustment_protected")
        elif bool(_get(admission, "base_event_silence_core_overlap", False)):
            decision.update(candidate_state="not_applied", reason="silence_core_overlap")
        elif _get(admission, "boundary_only", False) or _get(admission, "boundary_action", "not_applicable") not in {None, "not_applicable"}:
            decision.update(candidate_state="not_applied", reason="boundary_event_protected")
        elif _get(source_event, "origin", "automatic") in {"manual", "unknown"}:
            decision.update(candidate_state="not_applied", reason="manual_or_unknown_protected")
        elif (
            local_peak is None
            or float(local_peak) <= 0.0
        ) and not any(float(value) > 0.0 for value in rms_values):
            decision.update(candidate_state="not_applied", reason="positive_acoustic_evidence_unavailable")
        else:
            target_peak = float(peak_value) * width_frames / 2.0
            target_peak = canonicalize_morph_value(target_peak).scalar
            if target_peak <= 0.0:
                decision.update(candidate_state="not_applied", reason="area_preserving_peak_not_representable")
            elif _curve_at(values, vowel, float(peak_frame)) > 0.0:
                decision.update(candidate_state="not_applied", reason="source_peak_already_represented_on_wire")
            else:
                candidate = None
                blocked_reason = "no_legal_one_frame_support"
                # Prefer the nearest legal frame. A +1 shift permits a small
                # overlap with the following vowel at rapid transitions.
                for frame in sorted({peak_frame - 1, peak_frame, peak_frame + 1}, key=lambda item: (abs(item - peak_frame), item)):
                    start_frame, end_frame = frame - 1, frame + 1
                    if start_frame < 0 or end_frame > source_duration_frames:
                        continue
                    if any(start <= frame < end for start, end in core_ranges):
                        blocked_reason = "silence_core_peak_protected"
                        decision["candidate_attempts"].append({
                            "frame": frame,
                            "support_frames": [start_frame, end_frame],
                            "state": "not_applied",
                            "reason": blocked_reason,
                        })
                        continue
                    if (frame, vowel) in required:
                        blocked_reason = "required_zero_peak_protected"
                        decision["candidate_attempts"].append({
                            "frame": frame,
                            "support_frames": [start_frame, end_frame],
                            "state": "not_applied",
                            "reason": blocked_reason,
                        })
                        continue
                    if any(
                        _curve_at(values, vowel, float(probe)) > 0.0
                        for probe in (start_frame, end_frame)
                    ):
                        blocked_reason = "same_morph_support_collision"
                        decision["candidate_attempts"].append({
                            "frame": frame,
                            "support_frames": [start_frame, end_frame],
                            "state": "not_applied",
                            "reason": blocked_reason,
                        })
                        continue
                    if _curve_at(values, vowel, float(frame)) > 0.0:
                        blocked_reason = "wire_already_positive_at_candidate_frame"
                        decision["candidate_attempts"].append({
                            "frame": frame,
                            "support_frames": [start_frame, end_frame],
                            "state": "not_applied",
                            "reason": blocked_reason,
                        })
                        continue
                    trial = dict(values)
                    trial[(start_frame, vowel)] = 0.0
                    trial[(frame, vowel)] = target_peak
                    trial[(end_frame, vowel)] = 0.0
                    if _silence_core_curve_changed(
                        baseline_values,
                        trial,
                        silence_core_frame_ranges,
                    ):
                        blocked_reason = "silence_core_curve_protected"
                        decision["candidate_attempts"].append({
                            "frame": frame,
                            "support_frames": [start_frame, end_frame],
                            "state": "not_applied",
                            "reason": blocked_reason,
                        })
                        continue
                    if _active_morph_limit_exceeded(trial, baseline_values, max_active_morphs):
                        blocked_reason = "active_morph_limit"
                        decision["candidate_attempts"].append({
                            "frame": frame,
                            "support_frames": [start_frame, end_frame],
                            "state": "not_applied",
                            "reason": blocked_reason,
                        })
                        continue
                    candidate = (trial, frame, start_frame, end_frame)
                    decision["candidate_attempts"].append({
                        "frame": frame,
                        "support_frames": [start_frame, end_frame],
                        "state": "applied",
                        "reason": "candidate_peak_outside_protected_zero_frames",
                    })
                    break
                if candidate is None:
                    decision.update(candidate_state="not_applied", reason=blocked_reason)
                else:
                    values, frame, start_frame, end_frame = candidate
                    decision.update(
                        candidate_state="applied",
                        reason="source_positive_subframe_event_wire_collapsed",
                        selected_frame=frame,
                        support_frames=[start_frame, end_frame],
                        candidate_peak_value=target_peak,
                    )
        decisions.append(decision)

    output_names = set(mapping.values())
    candidate_points = [
        (frame, mapping[vowel], value)
        for (frame, vowel), value in values.items()
        if vowel in VOWELS and mapping[vowel] in output_names
    ]
    candidate_points.sort(key=lambda item: (item[0], tuple(mapping.values()).index(item[1])))
    # Candidate construction is deterministic and may not alter a positive
    # source key or any unapproved morph.
    for key, before in baseline_values.items():
        after = values.get(key, 0.0)
        if before > 0.0 and after != before:
            raise B4CVowelQualityError("candidate changed an existing positive wire key")
    return candidate_points, decisions


def validate_short_event_wire_candidate(
    *,
    baseline_points: Sequence[WireReadbackPoint],
    candidate_points: Sequence[WireReadbackPoint],
    expected_points: Sequence[tuple[int, str, float]],
    output_mapping: Mapping[str, str],
    decisions: Sequence[Mapping[str, Any]],
    required_zero_frames: Sequence[Sequence[Any]] = (),
    silence_core_frame_ranges: Sequence[Sequence[int]] = (),
    max_active_morphs: int = MAX_ACTIVE_MORPHS,
) -> dict[str, Any]:
    """Independently verify the candidate VMD readback against its key list."""
    semantic_mapping = dict(output_mapping)
    base = _semantic_values(baseline_points, semantic_mapping)
    actual = _semantic_values(candidate_points, semantic_mapping)
    expected: dict[tuple[int, str], float] = {}
    reverse = {name: vowel for vowel, name in semantic_mapping.items()}
    for frame, name, value in expected_points:
        vowel = reverse.get(name)
        if vowel is None:
            raise B4CVowelQualityError("candidate expectation contains an unmapped morph")
        key = (int(frame), vowel)
        if key in expected:
            raise B4CVowelQualityError("candidate expectation contains duplicate keys")
        canonical = canonicalize_morph_value(value)
        expected[key] = struct.unpack(
            "<f", bytes.fromhex(canonical.binary32_hex)
        )[0]
    if actual != expected:
        raise B4CVowelQualityError("candidate VMD readback differs from the issued keys")
    for (frame, vowel), value in base.items():
        if value > 0.0 and actual.get((frame, vowel), 0.0) != value:
            raise B4CVowelQualityError("candidate changed an existing positive wire key")
    missing = object()
    changed_keys = {
        key
        for key in set(base) | set(actual)
        if base.get(key, missing) != actual.get(key, missing)
    }
    allowed_keys = {
        (int(frame), str(vowel))
        for item in decisions
        if item.get("candidate_state") == "applied"
        for frame, vowel in (
            (item.get("selected_frame") - 1, item.get("vowel")),
            (item.get("selected_frame"), item.get("vowel")),
            (item.get("selected_frame") + 1, item.get("vowel")),
        )
    }
    if not changed_keys <= allowed_keys:
        raise B4CVowelQualityError("candidate changed keys outside approved event support")
    for item in required_zero_frames:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise B4CVowelQualityError("required-zero candidate contract is malformed")
        frame, vowel = int(item[0]), str(item[1])
        if vowel not in VOWELS:
            raise B4CVowelQualityError("required-zero candidate morph is unsupported")
        if _curve_at(base, vowel, float(frame)) != _curve_at(actual, vowel, float(frame)):
            raise B4CVowelQualityError("candidate changed a required-zero wire frame")
    if _silence_core_curve_changed(base, actual, silence_core_frame_ranges):
        raise B4CVowelQualityError("candidate changed a silence-core wire curve")
    probe_frames = _curve_probe_frames(actual, base)
    active_counts = [_wire_active_count(actual, frame) for frame in probe_frames]
    if _active_morph_limit_exceeded(actual, base, max_active_morphs):
        raise B4CVowelQualityError("candidate increases an existing active morph-limit exception")
    return {
        "state": "passed",
        "candidate_key_count": len(actual),
        "changed_key_count": len(changed_keys),
        "maximum_active_morphs": max(active_counts, default=0),
        "candidate_policy_id": CANDIDATE_POLICY_ID,
    }


def build_vowel_quality_record(
    *,
    case_id: str,
    run_id: str,
    input_mode: str,
    transcript_text: str,
    transcript_source: str,
    transcript_origin: str,
    recorded_analysis_text: Mapping[str, Any] | None,
    source_identity: Mapping[str, Any],
    converted_vowels: Sequence[str],
    timeline: Sequence[Any],
    observations: Sequence[Any],
    anchors: Sequence[Any],
    source_events: Sequence[Any],
    event_silence_admissions: Sequence[Any],
    silence_core_frame_ranges: Sequence[Sequence[int]],
    required_zero_frames: Sequence[Sequence[Any]],
    reference_text: str | None,
    baseline_vmd_ref: Mapping[str, Any],
    candidate_vmd_ref: Mapping[str, Any],
    baseline_points: Sequence[WireReadbackPoint],
    candidate_points: Sequence[WireReadbackPoint],
    output_mapping: Mapping[str, str],
    candidate_decisions: Sequence[Mapping[str, Any]],
    candidate_validation: Mapping[str, Any],
    reference_vowels: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Build the self-contained B4C quality record for an isolated replay."""
    if input_mode not in {"voice_only", "text_audio"}:
        raise B4CVowelQualityError("input mode is unsupported")
    current_identity = analysis_text_identity(transcript_text)
    recorded = None if recorded_analysis_text is None else {
        "sha256": recorded_analysis_text.get("sha256"),
        "character_count": recorded_analysis_text.get("character_count"),
    }
    if recorded is not None:
        _require_sha256(recorded.get("sha256"), "recorded analysis_text.sha256")
    transcript_match = (
        "unavailable"
        if recorded is None
        else "matched"
        if recorded == current_identity
        else "unmatched"
    )
    if any(vowel not in VOWELS for vowel in converted_vowels):
        raise B4CVowelQualityError("converted vowel sequence contains an unsupported vowel")
    event_by_token: dict[int, list[tuple[int, Any]]] = {}
    for event_index, point in enumerate(timeline):
        token_index = _get(point, "vowel_token_index")
        if isinstance(token_index, int) and not isinstance(token_index, bool):
            event_by_token.setdefault(token_index, []).append((event_index, point))
    observations_by_index = {
        int(_get(item, "event_index", index)): item for index, item in enumerate(observations)
    }
    source_by_index = {
        int(_get(item, "base_event_index", index)): item for index, item in enumerate(source_events)
    }
    admissions_by_index = {
        int(_get(item, "event_index", index)): item for index, item in enumerate(event_silence_admissions)
    }
    decisions_by_index = {
        int(item["event_index"]): item
        for item in candidate_decisions
        if isinstance(item, Mapping) and isinstance(item.get("event_index"), int)
    }
    baseline_by_semantic = _semantic_values(baseline_points, output_mapping)
    candidate_by_semantic = _semantic_values(candidate_points, output_mapping)
    token_records: list[dict[str, Any]] = []
    for token_index, vowel in enumerate(converted_vowels):
        matches = event_by_token.get(token_index, [])
        event_rows = []
        for event_index, point in matches:
            source_event = source_by_index.get(event_index)
            admission = admissions_by_index.get(event_index)
            observation = observations_by_index.get(event_index)
            decision = decisions_by_index.get(event_index)
            start_sec = _get(point, "start_sec")
            end_sec = _get(point, "end_sec")
            time_sec = _get(point, "time_sec")
            start_frame = max(0, math.floor(float(start_sec) * VMD_FPS) - 1) if start_sec is not None else None
            end_frame = math.ceil(float(end_sec) * VMD_FPS) + 1 if end_sec is not None else None
            anchor_matches = [
                anchor_index
                for anchor_index, anchor in enumerate(anchors)
                if start_sec is not None
                and end_sec is not None
                and float(_get(anchor, "start_sec", math.inf)) <= float(end_sec)
                and float(_get(anchor, "end_sec", -math.inf)) >= float(start_sec)
            ]
            baseline_wire_keys = [
                {"frame": frame, "value": value}
                for (frame, semantic), value in sorted(baseline_by_semantic.items())
                if semantic == vowel and start_frame is not None and end_frame is not None and start_frame <= frame <= end_frame
            ]
            candidate_wire_keys = [
                {"frame": frame, "value": value}
                for (frame, semantic), value in sorted(candidate_by_semantic.items())
                if semantic == vowel and start_frame is not None and end_frame is not None and start_frame <= frame <= end_frame
            ]
            has_positive_candidate_key = any(item["value"] > 0.0 for item in candidate_wire_keys)
            wire_state = (
                "positive"
                if has_positive_candidate_key
                else "zero"
                if candidate_wire_keys
                else "unmapped"
            )
            zero_reason = None
            if wire_state != "positive":
                zero_reason = (
                    decision.get("reason")
                    if decision is not None and decision.get("candidate_state") != "applied"
                    else _get(observation, "reason")
                    if observation is not None and _get(observation, "reason")
                    else "source_peak_zero"
                    if source_event is not None and float(_get(source_event, "peak_value", 0.0) or 0.0) <= 0.0
                    else "silence_core_overlap"
                    if admission is not None and bool(_get(admission, "base_event_silence_core_overlap", False))
                    else "wire_key_unavailable"
                    if wire_state == "unmapped"
                    else "no_positive_wire_key_in_token_window"
                )
            event_rows.append({
                "event_index": event_index,
                "source_event": _json_value(source_event),
                "timeline": _json_value(point),
                "observation": _json_value(observation),
                "silence_admission": _json_value(admission),
                "candidate_decision": _json_value(decision),
                "anchor_time_overlap_candidates": anchor_matches,
                "wire_frame_window": [start_frame, end_frame],
                "baseline_wire_keys": baseline_wire_keys,
                "candidate_wire_keys": candidate_wire_keys,
                "wire_state": wire_state,
                "zero_reason": zero_reason,
            })
        event_reason = None if event_rows else "token_without_timeline_event"
        token_wire_state = (
            "positive"
            if any(row["wire_state"] == "positive" for row in event_rows)
            else "zero"
            if event_rows and any(row["wire_state"] == "zero" for row in event_rows)
            else "unmapped"
        )
        token_wire_reason = None if token_wire_state == "positive" else (
            event_reason
            if not event_rows
            else next(
                (row["zero_reason"] for row in event_rows if row["zero_reason"]),
                "wire_key_unavailable",
            )
        )
        token_records.append({
            "token_index": token_index,
            "vowel": vowel,
            "is_long_vowel_continuation": bool(
                any(_get(row.get("timeline"), "is_long_vowel_continuation", False) for row in event_rows)
            ),
            "event_state": "mapped" if event_rows else "unmapped",
            "unmapped_reason": event_reason,
            "wire_state": token_wire_state,
            "wire_reason": token_wire_reason,
            "events": event_rows,
        })

    reference_identity = None
    if reference_text is not None:
        reference_identity = {
            **analysis_text_identity(reference_text),
            "converted_vowel_string": "".join(reference_vowels or ()),
            "source_kind": "reference_text",
        }
    record = {
        "schema_id": SCHEMA_ID,
        "candidate_policy_id": CANDIDATE_POLICY_ID,
        "case_id": case_id,
        "run_id": run_id,
        "state": "candidate_only",
        "input_mode": input_mode,
        "source_identity": _json_value(source_identity),
        "transcript": {
            "text": transcript_text,
            "source": transcript_source,
            "origin": transcript_origin,
            **current_identity,
            "historical_identity": recorded,
            "historical_match": transcript_match,
            "historical_token_mapping": "confirmed" if transcript_match == "matched" else "unconfirmed",
        },
        "reference_text": reference_identity,
        "converted_vowel_string": "".join(converted_vowels),
        "token_count": len(converted_vowels),
        "token_records": token_records,
        "anchors": [_json_value(anchor) for anchor in anchors],
        "vmd": {
            "baseline": _json_value(baseline_vmd_ref),
            "candidate": _json_value(candidate_vmd_ref),
            "baseline_wire_key_count": len(baseline_points),
            "candidate_wire_key_count": len(candidate_points),
            "mapping": dict(output_mapping),
        },
        "candidate_decisions": [_json_value(item) for item in candidate_decisions],
        "candidate_validation": _json_value(candidate_validation),
        "protection_contract": {
            "required_zero_frames": [_json_value(item) for item in required_zero_frames],
            "silence_core_frame_ranges": [_json_value(item) for item in silence_core_frame_ranges],
            "silence_core_range_semantics": "half_open",
        },
        "mmd_review": {
            "required": True,
            "model_target": "Tda式初音ミク",
            "state": "not_performed",
        },
    }
    validate_vowel_quality_record(record)
    return record


def validate_vowel_quality_record(record: Mapping[str, Any]) -> None:
    if not isinstance(record, Mapping) or record.get("schema_id") != SCHEMA_ID:
        raise B4CVowelQualityError("B4C quality record schema is invalid")
    transcript = record.get("transcript")
    if not isinstance(transcript, Mapping):
        raise B4CVowelQualityError("B4C transcript record is missing")
    text = transcript.get("text")
    if type(text) is not str:
        raise B4CVowelQualityError("B4C transcript text is missing")
    identity = analysis_text_identity(text)
    if transcript.get("sha256") != identity["sha256"] or transcript.get("character_count") != identity["character_count"]:
        raise B4CVowelQualityError("B4C transcript identity differs from its text")
    _require_sha256(identity["sha256"], "transcript.sha256")
    historical = transcript.get("historical_identity")
    historical_match = transcript.get("historical_match")
    if historical is None:
        if historical_match != "unavailable" or transcript.get("historical_token_mapping") != "unconfirmed":
            raise B4CVowelQualityError("unavailable historical transcript identity is misclassified")
    else:
        _require_sha256(_get(historical, "sha256"), "historical transcript.sha256")
        expected_match = "matched" if historical == identity else "unmatched"
        if historical_match != expected_match:
            raise B4CVowelQualityError("historical transcript comparison is inconsistent")
        expected_mapping = "confirmed" if expected_match == "matched" else "unconfirmed"
        if transcript.get("historical_token_mapping") != expected_mapping:
            raise B4CVowelQualityError("historical token mapping state is inconsistent")
    vowel_string = record.get("converted_vowel_string")
    tokens = record.get("token_records")
    if type(vowel_string) is not str or type(tokens) is not list:
        raise B4CVowelQualityError("B4C token mapping is missing")
    if "".join(str(item.get("vowel")) for item in tokens) != vowel_string:
        raise B4CVowelQualityError("B4C token records differ from the converted vowel string")
    for index, item in enumerate(tokens):
        if type(item) is not dict or item.get("token_index") != index:
            raise B4CVowelQualityError("B4C token indexes are not contiguous")
        if item.get("event_state") == "unmapped" and not item.get("unmapped_reason"):
            raise B4CVowelQualityError("unmapped B4C token has no reason")
        if item.get("event_state") not in {"mapped", "unmapped"}:
            raise B4CVowelQualityError("B4C token event state is invalid")
        if item.get("wire_state") not in {"positive", "zero", "unmapped"}:
            raise B4CVowelQualityError("B4C token wire state is invalid")
        if item.get("wire_state") != "positive" and not item.get("wire_reason"):
            raise B4CVowelQualityError("zero or unmapped B4C token has no wire reason")
        if item.get("wire_state") == "positive" and not any(
            event.get("wire_state") == "positive" for event in item.get("events", ())
        ):
            raise B4CVowelQualityError("positive B4C token has no positive event wire key")
    candidate_validation = record.get("candidate_validation")
    if not isinstance(candidate_validation, Mapping) or candidate_validation.get("state") != "passed":
        raise B4CVowelQualityError("B4C candidate readback has not passed validation")


def write_wire_candidate(
    *,
    output_path: str,
    baseline_model_name: str,
    candidate_points: Sequence[tuple[int, str, float]],
    output_names: Sequence[str],
) -> None:
    """Write an isolated candidate VMD using the existing morph-only writer."""
    from src.vmd_writer.writer import write_morph_frames_vmd

    write_morph_frames_vmd(
        output_path,
        candidate_points,
        model_name=baseline_model_name,
        output_morph_names=output_names,
    )


__all__ = [
    "B4CVowelQualityError",
    "CANDIDATE_POLICY_ID",
    "SCHEMA_ID",
    "analysis_text_identity",
    "build_short_event_wire_candidate",
    "build_vowel_quality_record",
    "validate_short_event_wire_candidate",
    "validate_vowel_quality_record",
    "write_wire_candidate",
]
