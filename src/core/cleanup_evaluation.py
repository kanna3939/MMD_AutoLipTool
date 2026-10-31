"""Strict typed request contract for explicit MS33-B4 candidate evaluation."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Any

from src.core.event_cleanup import CleanupParameter, EventCleanupError, EventCleanupPolicy, validate_event_cleanup_policy
from src.core.final_morph_key_reduction_plan import KeyReductionPolicy

REQUEST_SCHEMA = "cleanup-evaluation-request/v1"
REQUEST_VARIANTS = ("baseline", "keys_only", "events_only", "events_and_keys")


class CleanupEvaluationError(ValueError):
    """Raised when a candidate request is malformed or has a bad digest."""


def _json_bytes(value: object) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise CleanupEvaluationError("request contains a non-canonical value") from error


def _digest(value: object) -> str:
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value.strip():
        raise CleanupEvaluationError(f"{name} must be non-empty text")
    return value


@dataclass(frozen=True, slots=True)
class CleanupArtifactReference:
    """Immutable path, content hash, and size for a locked B1/B3 evidence file."""

    path: str
    sha256: str
    bytes: int

    def __post_init__(self) -> None:
        _text(self.path, "artifact path")
        if not Path(self.path).is_absolute():
            raise CleanupEvaluationError("artifact path must be absolute")
        if (
            type(self.sha256) is not str
            or len(self.sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.sha256)
        ):
            raise CleanupEvaluationError("artifact sha256 must be lowercase SHA-256")
        if isinstance(self.bytes, bool) or not isinstance(self.bytes, int) or self.bytes < 0:
            raise CleanupEvaluationError("artifact bytes must be a non-negative integer")

    def to_dict(self) -> dict[str, object]:
        return {"path": self.path, "sha256": self.sha256, "bytes": self.bytes}

    @classmethod
    def from_dict(cls, value: object) -> "CleanupArtifactReference":
        if type(value) is not dict or set(value) != {"path", "sha256", "bytes"}:
            raise CleanupEvaluationError("artifact reference fields are invalid")
        return cls(path=value["path"], sha256=value["sha256"], bytes=value["bytes"])


def verify_cleanup_artifact_reference(
    reference: CleanupArtifactReference,
    read_roots: tuple[Path, ...],
) -> Path:
    """Verify one request ref without following it outside the manifest's roots."""
    if not isinstance(reference, CleanupArtifactReference):
        raise CleanupEvaluationError("artifact reference is invalid")
    if type(read_roots) is not tuple or not read_roots:
        raise CleanupEvaluationError("read_roots must be a non-empty tuple")
    try:
        path = Path(reference.path).resolve(strict=True)
    except OSError as error:
        raise CleanupEvaluationError("artifact reference is unavailable") from error
    roots: list[Path] = []
    for root in read_roots:
        if not isinstance(root, Path):
            raise CleanupEvaluationError("read_roots entries must be pathlib paths")
        try:
            resolved_root = root.resolve(strict=True)
        except OSError as error:
            raise CleanupEvaluationError("artifact read root is unavailable") from error
        if not resolved_root.is_dir():
            raise CleanupEvaluationError("artifact read roots must be directories")
        roots.append(resolved_root)
    if not any(path == root or path.is_relative_to(root) for root in roots):
        raise CleanupEvaluationError("artifact reference escapes declared read_roots")
    return verify_cleanup_artifact_content(reference)


def verify_cleanup_artifact_content(reference: CleanupArtifactReference) -> Path:
    """Verify a locked file's content when its root was already checked by the launcher."""
    if not isinstance(reference, CleanupArtifactReference):
        raise CleanupEvaluationError("artifact reference is invalid")
    path = Path(reference.path)
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise CleanupEvaluationError("artifact reference is unavailable") from error
    if not resolved.is_file():
        raise CleanupEvaluationError("artifact reference is not a file")
    try:
        before = resolved.stat()
        payload = resolved.read_bytes()
        after = resolved.stat()
    except OSError as error:
        raise CleanupEvaluationError("artifact reference cannot be read") from error
    identity_before = (
        getattr(before, "st_dev", None), getattr(before, "st_ino", None),
        getattr(before, "st_mtime_ns", None), before.st_size,
    )
    identity_after = (
        getattr(after, "st_dev", None), getattr(after, "st_ino", None),
        getattr(after, "st_mtime_ns", None), after.st_size,
    )
    if (
        identity_before != identity_after
        or len(payload) != reference.bytes
        or after.st_size != reference.bytes
        or hashlib.sha256(payload).hexdigest() != reference.sha256
    ):
        raise CleanupEvaluationError("artifact reference hash or size changed")
    return resolved


def _read_event_policy(value: object) -> EventCleanupPolicy:
    fields = {"schema_id", "contract_digest", "comparison_digest", "proposal_id", "parameters", "scope", "protections", "unknown_rules", "allowed_changes", "real_cases", "valid_low_controls", "policy_digest"}
    if type(value) is not dict or set(value) != fields:
        raise CleanupEvaluationError("event policy fields are invalid")
    if type(value["parameters"]) is not list or any(type(item) is not dict for item in value["parameters"]):
        raise CleanupEvaluationError("event policy parameters are invalid")
    for name in ("protections", "unknown_rules", "allowed_changes", "real_cases", "valid_low_controls"):
        if type(value[name]) is not list:
            raise CleanupEvaluationError(f"event policy {name} is invalid")
    try:
        policy = EventCleanupPolicy(
            contract_digest=value["contract_digest"], comparison_digest=value["comparison_digest"],
            proposal_id=value["proposal_id"], parameters=tuple(CleanupParameter(**row) for row in value["parameters"]),
            scope=value["scope"], protections=tuple(value["protections"]), unknown_rules=tuple(value["unknown_rules"]),
            allowed_changes=tuple(value["allowed_changes"]), real_cases=tuple(value["real_cases"]),
            valid_low_controls=tuple(value["valid_low_controls"]), policy_digest=value["policy_digest"], schema_id=value["schema_id"],
        )
        validate_event_cleanup_policy(policy)
    except (TypeError, EventCleanupError) as error:
        raise CleanupEvaluationError("event policy is invalid") from error
    return policy


def _read_key_policy(value: object) -> KeyReductionPolicy:
    fields = {"schema_id", "policy_id", "key_contract_digest", "protections", "curve_domains", "algorithm_id", "enabled", "policy_digest"}
    if type(value) is not dict or set(value) != fields:
        raise CleanupEvaluationError("key policy fields are invalid")
    if type(value["protections"]) is not list or type(value["curve_domains"]) is not list:
        raise CleanupEvaluationError("key policy arrays are invalid")
    try:
        return KeyReductionPolicy(
            policy_id=value["policy_id"], key_contract_digest=value["key_contract_digest"],
            protections=tuple(value["protections"]), curve_domains=tuple(value["curve_domains"]),
            algorithm_id=value["algorithm_id"], enabled=value["enabled"],
            policy_digest=value["policy_digest"], schema_id=value["schema_id"],
        )
    except (TypeError, ValueError) as error:
        raise CleanupEvaluationError("key policy is invalid") from error


def read_event_cleanup_policy(value: object) -> EventCleanupPolicy:
    return _read_event_policy(value)


def read_key_reduction_policy(value: object) -> KeyReductionPolicy:
    return _read_key_policy(value)


@dataclass(frozen=True, slots=True)
class CleanupEvaluationRequest:
    variant: str
    case_id: str
    event_policy: EventCleanupPolicy
    key_policy: KeyReductionPolicy
    b1_contract_refs: tuple[CleanupArtifactReference, ...]
    b3_audit_ref: CleanupArtifactReference
    evaluation_session_id: str
    request_digest: str
    case_source_refs: tuple[tuple[str, CleanupArtifactReference], ...] = ()
    schema_id: str = REQUEST_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != REQUEST_SCHEMA or self.variant not in REQUEST_VARIANTS:
            raise CleanupEvaluationError("request schema or variant is unsupported")
        _text(self.case_id, "case_id")
        if not isinstance(self.event_policy, EventCleanupPolicy) or not isinstance(self.key_policy, KeyReductionPolicy):
            raise CleanupEvaluationError("request policies have invalid types")
        try:
            validate_event_cleanup_policy(self.event_policy)
            self.key_policy.validate_integrity()
        except (EventCleanupError, ValueError) as error:
            raise CleanupEvaluationError("request policy integrity is invalid") from error
        if type(self.b1_contract_refs) is not tuple or not self.b1_contract_refs or any(
            not isinstance(reference, CleanupArtifactReference)
            for reference in self.b1_contract_refs
        ):
            raise CleanupEvaluationError("b1_contract_refs must be typed artifact references")
        if len({reference.path for reference in self.b1_contract_refs}) != len(self.b1_contract_refs):
            raise CleanupEvaluationError("B1 contract references contain duplicate paths")
        if not isinstance(self.b3_audit_ref, CleanupArtifactReference):
            raise CleanupEvaluationError("b3_audit_ref must be a typed artifact reference")
        if type(self.case_source_refs) is not tuple:
            raise CleanupEvaluationError("case_source_refs must be a tuple")
        source_roles = tuple(role for role, _reference in self.case_source_refs)
        allowed_source_roles = {
            "analysis_trace", "analysis_wav", "full_snapshot", "source_audio", "source_text",
            "capture_manifest", "historical_reference_vmd", "baseline_plan", "baseline_vmd",
            "baseline_readback", "b1_research", "b1_audit",
        }
        if (
            len(source_roles) != len(set(source_roles))
            or any(role not in allowed_source_roles for role in source_roles)
            or any(not isinstance(reference, CleanupArtifactReference) for _role, reference in self.case_source_refs)
        ):
            raise CleanupEvaluationError("case_source_refs are malformed")
        if re.fullmatch(r"ms33-b1-\d{2}-(?:ta|vo)", self.case_id):
            required_roles = {
                "analysis_trace", "analysis_wav", "full_snapshot", "source_audio",
                "capture_manifest", "baseline_plan", "baseline_vmd", "baseline_readback",
                "b1_research", "b1_audit",
            }
            if self.case_id.endswith("-ta"):
                required_roles.add("source_text")
            optional_roles = {"historical_reference_vmd"}
            if not required_roles <= set(source_roles) or set(source_roles) - required_roles - optional_roles:
                raise CleanupEvaluationError("locked B1 case must carry its complete source references")
        _text(self.evaluation_session_id, "evaluation_session_id")
        if type(self.request_digest) is not str or len(self.request_digest) != 64 or any(c not in "0123456789abcdef" for c in self.request_digest):
            raise CleanupEvaluationError("request_digest must be a lowercase SHA-256")
        if self.computed_digest() != self.request_digest:
            raise CleanupEvaluationError("request digest does not match its fields")

    def _payload(self, *, include_digest: bool) -> dict[str, object]:
        row: dict[str, object] = {
            "schema_id": self.schema_id, "variant": self.variant, "case_id": self.case_id,
            "event_policy": self.event_policy.to_dict(), "key_policy": self.key_policy.to_dict(),
            "b1_contract_refs": [item.to_dict() for item in self.b1_contract_refs],
            "b3_audit_ref": self.b3_audit_ref.to_dict(),
            "case_source_refs": [
                {"role": role, **reference.to_dict()}
                for role, reference in self.case_source_refs
            ],
            "evaluation_session_id": self.evaluation_session_id,
        }
        if include_digest:
            row["request_digest"] = self.request_digest
        return row

    def computed_digest(self) -> str:
        return _digest(self._payload(include_digest=False))

    def to_dict(self) -> dict[str, object]:
        return self._payload(include_digest=True)

    @classmethod
    def create(cls, *, variant: str, case_id: str, event_policy: EventCleanupPolicy, key_policy: KeyReductionPolicy, b1_contract_refs: tuple[CleanupArtifactReference, ...], b3_audit_ref: CleanupArtifactReference, evaluation_session_id: str, case_source_refs: tuple[tuple[str, CleanupArtifactReference], ...] = ()) -> "CleanupEvaluationRequest":
        values = {
            "schema_id": REQUEST_SCHEMA, "variant": variant, "case_id": case_id,
            "event_policy": event_policy.to_dict(), "key_policy": key_policy.to_dict(),
            "b1_contract_refs": [item.to_dict() for item in b1_contract_refs],
            "b3_audit_ref": b3_audit_ref.to_dict(),
            "case_source_refs": [
                {"role": role, **reference.to_dict()}
                for role, reference in case_source_refs
            ],
            "evaluation_session_id": evaluation_session_id,
        }
        return cls(
            variant=variant, case_id=case_id, event_policy=event_policy, key_policy=key_policy,
            b1_contract_refs=tuple(b1_contract_refs), b3_audit_ref=b3_audit_ref,
            evaluation_session_id=evaluation_session_id, request_digest=_digest(values),
            case_source_refs=tuple(case_source_refs),
        )

    @classmethod
    def from_dict(cls, value: object) -> "CleanupEvaluationRequest":
        fields = {"schema_id", "variant", "case_id", "event_policy", "key_policy", "b1_contract_refs", "b3_audit_ref", "case_source_refs", "evaluation_session_id", "request_digest"}
        if (
            type(value) is not dict
            or set(value) != fields
            or type(value["b1_contract_refs"]) is not list
            or type(value["case_source_refs"]) is not list
        ):
            raise CleanupEvaluationError("request fields are invalid")
        source_refs: list[tuple[str, CleanupArtifactReference]] = []
        for item in value["case_source_refs"]:
            if type(item) is not dict or set(item) != {"role", "path", "sha256", "bytes"}:
                raise CleanupEvaluationError("case source reference fields are invalid")
            source_refs.append((
                item["role"],
                CleanupArtifactReference.from_dict({
                    key: item[key] for key in ("path", "sha256", "bytes")
                }),
            ))
        return cls(
            schema_id=value["schema_id"], variant=value["variant"], case_id=value["case_id"],
            event_policy=_read_event_policy(value["event_policy"]), key_policy=_read_key_policy(value["key_policy"]),
            b1_contract_refs=tuple(
                CleanupArtifactReference.from_dict(item)
                for item in value["b1_contract_refs"]
            ),
            b3_audit_ref=CleanupArtifactReference.from_dict(value["b3_audit_ref"]),
            evaluation_session_id=value["evaluation_session_id"], request_digest=value["request_digest"],
            case_source_refs=tuple(source_refs),
        )


__all__ = [
    "CleanupArtifactReference",
    "CleanupEvaluationError",
    "CleanupEvaluationRequest",
    "REQUEST_SCHEMA",
    "REQUEST_VARIANTS",
    "read_event_cleanup_policy",
    "read_key_reduction_policy",
    "verify_cleanup_artifact_content",
    "verify_cleanup_artifact_reference",
]
