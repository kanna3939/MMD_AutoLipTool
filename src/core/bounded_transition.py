"""B4B issuer connecting source scheduling to the existing verified output path."""
from __future__ import annotations

from dataclasses import dataclass, replace, fields
import hashlib
from pathlib import Path

from src.core.cross_vowel_transition import (
    TRANSITION_POLICY_V2, TransitionResolution, TransitionSourceLineage,
    TransitionValidationResult, build_adopted_transition_policy,
    build_transition_pairs_from_effective_plan, resolve_cross_vowel_transition,
    validate_transition_resolution, transition_effective_snapshot_json,
    _positive_overlap,
)
from src.core.final_morph_capture import snapshot_digest
from src.core.final_morph_plan import (
    FinalMorphIdentityContext, effective_plan_snapshot_digest,
)
from src.core.short_vowel_schedule import (
    TransitionSourcePreparation, ScheduleResolution, prepare_transition_source,
    verify_preparation, schedule_vowels, validate_schedule, apply_schedule,
)


@dataclass(frozen=True)
class ScheduleClosureAdmission:
    preparation: TransitionSourcePreparation
    initial_resolution: TransitionResolution
    schedule: ScheduleResolution


@dataclass(frozen=True, slots=True)
class BoundedCaptureLineage(TransitionSourceLineage):
    """Replay admission bound to the actual frozen source, not a live run."""
    preparation_digest: str = ""
    legacy_baseline_status: str = "generated"

    def __post_init__(self):
        if self.source_kind != "replayed_capture" or self.compatibility_proof_digest is not None:
            raise ValueError("bounded replay cannot claim a legacy compatibility proof")
        for value in (self.capture_manifest_sha256,self.original_source_sha256,
                      self.current_runtime_sha256,self.preparation_digest):
            if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
                raise ValueError("bounded capture hashes are invalid")
        if self.legacy_baseline_status not in {"generated","not_generated"}:
            raise ValueError("unknown legacy baseline status")
        # Reuse all common live identity/mapping checks without replay-v1 fields.
        common={f.name:getattr(self,f.name) for f in fields(TransitionSourceLineage)}
        for name in ('capture_manifest_sha256','original_source_sha256','original_runtime_sha256',
                     'current_runtime_sha256','compatibility_proof_digest'):
            common[name]=None
        common['source_kind']='live_analysis'
        TransitionSourceLineage(**common)

    def canonical_payload(self):
        payload=TransitionSourceLineage.canonical_payload(self)
        payload.pop('compatibility_proof_digest')
        payload['preparation_digest']=self.preparation_digest
        payload['legacy_baseline_status']=self.legacy_baseline_status
        return payload

    def to_dict(self):
        return {'schema_id':'transition-source-lineage/v2',**self.canonical_payload(),
                'lineage_digest':self.lineage_digest}


def read_bounded_capture_lineage(raw):
    names={f.name for f in fields(BoundedCaptureLineage)}-{'compatibility_proof_digest'}
    if set(raw)!=names|{'schema_id','lineage_digest'}:
        raise ValueError("bounded capture lineage fields differ from schema")
    kwargs={name:raw[name] for name in names}
    kwargs['output_mapping']=tuple(tuple(p) for p in kwargs['output_mapping'])
    result=BoundedCaptureLineage(**kwargs)
    if result.lineage_digest!=raw['lineage_digest']:
        raise ValueError("bounded capture lineage digest mismatch")
    return result


def bounded_runtime_digest():
    from src.core.short_vowel_schedule import digest
    root=Path(__file__).resolve().parents[2]
    paths=('src/core/bounded_transition.py','src/core/short_vowel_schedule.py',
           'src/core/effective_shape_plan.py','src/core/cross_vowel_transition.py',
           'src/core/morph_closure.py','src/core/final_morph_transition_plan.py',
           'src/vmd_writer/final_morph_transition_adapter.py')
    return digest(tuple((name,hashlib.sha256((root/name).read_bytes()).hexdigest()) for name in paths))


def _bounded_pairs(plan):
    # v1 historically retained set iteration order in this field. Canonicalize
    # only the v2 source identity, preserving explicit v1 records and digests.
    return tuple(replace(p,target_required_zero_frames=tuple(sorted(p.target_required_zero_frames)))
                 for p in build_transition_pairs_from_effective_plan(plan,fps=30))


def _final_pair_decisions(preparation, initial, shapes, pairs):
    records=[]
    for d,pair in zip(initial.decisions,pairs,strict=True):
        if d.state!="applied":
            records.append(d)
            continue
        target=shapes[pair.next_shape_index]
        previous=shapes[pair.previous_shape_index]
        width,frames=_positive_overlap(previous.control_points,target.control_points,
            start_frame=pair.previous_event_peak_frame,end_frame=pair.next_event_peak_frame)
        survives=any(p.frame_no==d.candidate_start_frame and p.value==0 and p.point_kind=="start_zero"
                     for p in target.control_points)
        if (not survives or width<=d.baseline_overlap_width_frames
                or not set(d.baseline_positive_integer_frames).issubset(frames)):
            d=replace(d,state="not_applicable",reason="superseded_by_schedule",
                candidate_start_frame=d.baseline_start_frame,start_advance_frames=0,
                candidate_overlap_width_frames=d.baseline_overlap_width_frames,
                overlap_width_delta_frames=0.,candidate_positive_integer_frames=d.baseline_positive_integer_frames)
        else:
            d=replace(d,candidate_overlap_width_frames=width,
                overlap_width_delta_frames=width-d.baseline_overlap_width_frames,
                candidate_positive_integer_frames=frames)
        records.append(d)
    return tuple(records)


def verify_schedule_admission(admission):
    if not isinstance(admission, ScheduleClosureAdmission):
        raise ValueError("typed schedule admission required")
    p=admission.preparation
    verify_preparation(p)
    pairs=_bounded_pairs(p.unresolved_plan)
    validation=validate_transition_resolution(policy=build_adopted_transition_policy(),
        acoustic_snapshot=p.acoustic_snapshot,pairs=pairs,baseline_shapes=p.unresolved_plan.shapes,
        resolution=admission.initial_resolution)
    if validation.state!="valid":
        raise ValueError("initial crossfade is not independently valid")
    validate_schedule(p,admission.schedule,admission.initial_resolution.resolved_shapes)
    return apply_schedule(p,admission.schedule)


def bounded_baseline_points(resolved, mapping, guards):
    from src.core.final_morph_capture import build_capture_baseline
    from src.core.final_morph_closure_plan import SEMANTIC_VOWEL_ORDER
    baseline=build_capture_baseline(resolved,output_morph_names=tuple(name for _,name in mapping))
    points={(int(p['frame_no']),p['semantic_morph']):float.fromhex(p['value_hex'])
            for p in baseline['points']}
    for vowel,frame in guards:
        if points.get((frame,vowel),0.)!=0:
            raise ValueError("gap closure guard collides with a positive source point")
        points[(frame,vowel)]=0.
    return tuple((f,v,value) for (f,v),value in sorted(points.items(),
                 key=lambda pair:(pair[0][0],SEMANTIC_VOWEL_ORDER.index(pair[0][1]))))


def build_bounded_issuer(*, origin, base_input, adjustment_snapshot, input_snapshot,
                         resolved_profile_id, output_morph_names, cancelled=None, capture_binding=None):
    from src.core.final_output_projection import (build_closure_issuer_context, SEMANTIC_VOWEL_ORDER,
        LEGACY_NUMERIC_POLICY_ID, LEGACY_CURVE_POLICY_ID, CROSSFADE_POLICY_ID)
    from src.core.final_morph_transition_plan import TransitionPlanIssuerContext, transition_pair_identity
    policy=input_snapshot.policy
    if policy.policy_id!=TRANSITION_POLICY_V2:
        raise ValueError("bounded issuer requires v2 policy")
    # This identity describes the original source, never a repaired surrogate.
    source=FinalMorphIdentityContext(source_run_id=origin.source_run_id,
        analysis_generation=origin.analysis_generation,base_plan_digest=origin.base_plan_digest,
        effective_plan_digest="0"*64,manual_revision=input_snapshot.manual_revision,
        resolved_profile_id=resolved_profile_id,output_mapping=tuple(zip(SEMANTIC_VOWEL_ORDER,output_morph_names)),
        numeric_policy_id=LEGACY_NUMERIC_POLICY_ID,curve_policy_id=LEGACY_CURVE_POLICY_ID,
        silence_policy_id="acoustic-core-precedence/v1",crossfade_policy_id=CROSSFADE_POLICY_ID)
    p=prepare_transition_source(base_input,adjustment_snapshot,policy,source_identity=source,
                                acoustic_snapshot=input_snapshot.acoustic)
    source=replace(source,effective_plan_digest=effective_plan_snapshot_digest(p.unresolved_plan),
                   silence_policy_id=p.unresolved_plan.silence_policy)
    p=replace(p,source_identity=source)
    pairs=_bounded_pairs(p.unresolved_plan)
    initial=resolve_cross_vowel_transition(policy=build_adopted_transition_policy(),
        acoustic_snapshot=p.acoustic_snapshot,pairs=pairs,shapes=p.unresolved_plan.shapes)
    scheduled=schedule_vowels(p,initial.resolved_shapes,cancelled=cancelled)
    admission=ScheduleClosureAdmission(p,initial,scheduled)
    resolved=verify_schedule_admission(admission)
    closure=build_closure_issuer_context(origin=origin,base_input=base_input,
        adjustment_snapshot=p.adjustment_snapshot,effective_plan=resolved,
        manual_revision=input_snapshot.manual_revision,resolved_profile_id=resolved_profile_id,
        output_morph_names=output_morph_names)
    closure=replace(closure,schedule_admission=admission,
        baseline_points=bounded_baseline_points(resolved,source.output_mapping,scheduled.closure_guards))
    lineage=TransitionSourceLineage(source_kind="live_analysis",origin_kind="accepted_analysis",
        origin_identity=f"{input_snapshot.run_id}/{input_snapshot.analysis_generation}",
        run_id=input_snapshot.run_id,analysis_generation=input_snapshot.analysis_generation,
        input_mode=input_snapshot.input_mode,analysis_wav_sha256=input_snapshot.analysis_wav_sha256,
        policy_digest=policy.policy_digest,parameter_digest=policy.policy_digest,
        acoustic_evidence_digest=input_snapshot.acoustic.content_digest,
        base_plan_digest=input_snapshot.base_plan_digest,manual_revision=input_snapshot.manual_revision,
        manual_snapshot_digest=snapshot_digest(p.adjustment_snapshot),
        effective_plan_digest=source.effective_plan_digest,resolved_profile_id=resolved_profile_id or "default",
        output_mapping=source.output_mapping,pair_identity=transition_pair_identity(pairs))
    if capture_binding is not None:
        common={f.name:getattr(lineage,f.name) for f in fields(TransitionSourceLineage)}
        common.update(source_kind='replayed_capture',origin_kind='captured_snapshot',
            capture_manifest_sha256=capture_binding['capture_manifest_sha256'],
            original_source_sha256=capture_binding['snapshot_sha256'],
            current_runtime_sha256=bounded_runtime_digest(),preparation_digest=p.source_digest,
            legacy_baseline_status=capture_binding['legacy_baseline_status'])
        lineage=BoundedCaptureLineage(**common)
    decisions=_final_pair_decisions(p,initial,scheduled.shapes,pairs)
    resolution=TransitionResolution(policy.policy_digest,input_snapshot.acoustic.content_digest,
        initial.baseline_shapes_digest,decisions,scheduled.shapes,scheduled)
    issuer=TransitionPlanIssuerContext(input_snapshot,lineage,pairs,p.unresolved_plan.shapes,
                                       closure,preparation=p)
    return issuer,resolution


def bounded_source_issues(issuer):
    p=issuer.preparation; s=issuer.source_lineage; x=issuer.input_snapshot
    if not isinstance(p,TransitionSourcePreparation):
        return ("bounded_source_missing",)
    source=p.source_identity
    if (x.policy.policy_id!=TRANSITION_POLICY_V2 or x.policy!=p.policy
            or x.acoustic!=p.acoustic_snapshot or x.run_id!=source.source_run_id
            or x.analysis_generation!=str(source.analysis_generation)
            or x.base_plan_digest!=source.base_plan_digest or x.manual_revision!=source.manual_revision
            or s.policy_digest!=x.policy.policy_digest or s.parameter_digest!=x.policy.policy_digest
            or s.acoustic_evidence_digest!=x.acoustic.content_digest
            or s.analysis_wav_sha256!=x.analysis_wav_sha256 or s.base_plan_digest!=x.base_plan_digest
            or s.run_id!=x.run_id or s.analysis_generation!=x.analysis_generation
            or s.manual_revision!=x.manual_revision or s.input_mode!=x.input_mode
            or s.manual_snapshot_digest!=snapshot_digest(p.adjustment_snapshot)
            or s.effective_plan_digest!=source.effective_plan_digest
            or s.effective_plan_digest!=effective_plan_snapshot_digest(p.unresolved_plan)
            or s.output_mapping!=source.output_mapping or s.resolved_profile_id!=(source.resolved_profile_id or "default")
            or s.origin_identity!=f"{x.run_id}/{x.analysis_generation}"):
        return ("bounded_source_binding_mismatch",)
    from src.core.final_morph_transition_plan import transition_pair_identity
    if s.pair_identity!=transition_pair_identity(issuer.pairs):
        return ("bounded_pair_binding_mismatch",)
    if isinstance(s,BoundedCaptureLineage):
        if s.preparation_digest!=p.source_digest or s.current_runtime_sha256!=bounded_runtime_digest():
            return ("bounded_capture_runtime_mismatch",)
    elif s.source_kind!='live_analysis' or issuer.compatibility_proof is not None:
        return ("bounded_source_kind_mismatch",)
    return ()


def verify_bounded_issuer(issuer,resolution):
    if bounded_source_issues(issuer):
        raise ValueError("bounded issuer source mismatch")
    p=issuer.preparation
    admission=issuer.closure_issuer_context.schedule_admission
    resolved=verify_schedule_admission(admission)
    legacy=issuer.closure_issuer_context.legacy_context
    if legacy.identity_context != replace(p.source_identity,effective_plan_digest=effective_plan_snapshot_digest(resolved)):
        raise ValueError("bounded closure identity differs from original source")
    pairs=_bounded_pairs(p.unresolved_plan)
    initial=admission.initial_resolution
    if (admission.preparation!=p or issuer.pairs!=pairs
            or issuer.baseline_shapes!=p.unresolved_plan.shapes
            or resolution.schedule!=admission.schedule
            or resolution.policy_digest!=p.policy.policy_digest
            or resolution.acoustic_digest!=p.acoustic_snapshot.content_digest
            or resolution.baseline_shapes_digest!=initial.baseline_shapes_digest
            or resolution.decisions!=_final_pair_decisions(p,initial,resolved.shapes,pairs)
            or resolution.resolved_shapes!=resolved.shapes):
        raise ValueError("bounded issuer differs from its admitted schedule")
    return resolved


def validate_bounded_plan(plan,issuer,resolution):
    from src.core.final_morph_transition_plan import FINAL_MORPH_TRANSITION_SCHEMA_V2
    from src.core.final_morph_closure_plan import closure_plan_from_json
    from src.core.morph_closure import validate_closure_plan
    try:
        resolved=verify_bounded_issuer(issuer,resolution)
        if plan is None or plan.schema_id!=FINAL_MORPH_TRANSITION_SCHEMA_V2 or plan.state!="valid":
            raise ValueError("bounded outer schema/state mismatch")
        identity=plan.identity_context; x=issuer.input_snapshot
        snapshot=transition_effective_snapshot_json(resolution,baseline_effective_digest=issuer.source_lineage.effective_plan_digest)
        if (identity.source_lineage!=issuer.source_lineage or identity.transition_input_digest!=x.input_digest
                or identity.policy_digest!=x.policy.policy_digest or identity.acoustic_digest!=x.acoustic.content_digest
                or identity.resolution_digest!=resolution.resolution_digest
                or identity.baseline_effective_digest!=issuer.source_lineage.effective_plan_digest
                or identity.resolved_effective_digest!=effective_plan_snapshot_digest(resolved)
                or identity.resolved_effective_snapshot_sha256!=hashlib.sha256(snapshot.encode()).hexdigest()
                or plan.resolved_effective_snapshot_json!=snapshot or plan.transition_records!=resolution.decisions):
            raise ValueError("bounded outer identity mismatch")
        closure=closure_plan_from_json(plan.closure_plan_json)
        if (closure.semantic_digest!=identity.closure_semantic_digest or closure.wire_digest!=identity.closure_wire_digest
                or validate_closure_plan(closure,issuer.closure_issuer_context).state!="valid"):
            raise ValueError("bounded closure subproof invalid")
        return TransitionValidationResult("valid",(),resolution.resolution_digest)
    except (ValueError,TypeError,AttributeError,OverflowError) as error:
        return TransitionValidationResult("invalid",(f"bounded_plan_invalid:{error}",),None)


def build_bounded_shared_output(*, origin, base_input, adjustment_snapshot, input_snapshot,
        evaluation_request=None, default_selection=None, resolved_profile_id, output_morph_names, normalized_text_path,
        closure_contract, ticket=0, lifecycle_epoch=0, lifecycle_signature=None, cancelled=None):
    from src.core.final_output_projection import (
        FinalOutputSyncResult, FinalOutputIdentity, SharedFinalOutputContext,
        TransitionSharedOutputBinding, build_final_output_input_identity,
        capture_source_event_metadata, _restriction_event_targets,
    )
    from src.core.final_morph_transition_plan import build_transition_candidate, validate_transition_plan
    from src.core.final_morph_closure_plan import closure_plan_from_json, ClosureIssue
    from src.core.morph_closure import ClosureBuildResult
    from src.vmd_writer.final_morph_transition_adapter import project_validated_transition_plan
    try:
        if (evaluation_request is None) == (default_selection is None):
            raise ValueError("bounded output requires exactly one evaluation or default binding")
        if evaluation_request is not None:
            expected_policy = evaluation_request.policy
        else:
            from src.core.transition_default_policy import DefaultTransitionSelection
            if not isinstance(default_selection, DefaultTransitionSelection):
                raise ValueError("default transition selection is invalid")
            if default_selection.selection_kind != "transition":
                raise ValueError("bounded output cannot use an excluded default selection")
            expected_policy = default_selection.binding.policy
        if (expected_policy!=input_snapshot.policy
                or origin.input_mode!=input_snapshot.input_mode):
            raise ValueError("bounded request and accepted origin differ")
        issuer,resolution=build_bounded_issuer(origin=origin,base_input=base_input,
            adjustment_snapshot=adjustment_snapshot,input_snapshot=input_snapshot,
            resolved_profile_id=resolved_profile_id,output_morph_names=output_morph_names,cancelled=cancelled)
        candidate=build_transition_candidate(issuer,resolution)
        if candidate.state!="valid" or candidate.plan is None:
            raise ValueError(";".join(candidate.issues))
        validation=validate_transition_plan(candidate.plan,issuer_context=issuer,resolution=resolution)
        projection=project_validated_transition_plan(candidate.plan,issuer_context=issuer,resolution=resolution)
        closure=closure_plan_from_json(candidate.plan.closure_plan_json)
        input_identity=build_final_output_input_identity(origin=origin,
            manual_revision=input_snapshot.manual_revision,input_mode=input_snapshot.input_mode,
            normalized_text_path=normalized_text_path,issuer_context=issuer.closure_issuer_context,
            closure_contract=closure_contract,transition_input_digest=input_snapshot.input_digest,
            application_binding_digest=(
                None if default_selection is None else default_selection.selection_digest
            ),
            crossfade_policy_id=input_snapshot.policy.policy_id)
        identity=FinalOutputIdentity(input_identity,candidate.plan.schema_id,input_snapshot.policy.curve_family,
                                    candidate.plan.semantic_digest,projection.wire_digest)
        binding=TransitionSharedOutputBinding(evaluation_request,input_snapshot,issuer,resolution,
                                               candidate.plan,validation,projection,default_selection)
        metadata=capture_source_event_metadata(issuer.closure_issuer_context.legacy_context.effective_plan_snapshot)
        context=SharedFinalOutputContext(input_identity,identity,issuer.closure_issuer_context,
            ClosureBuildResult("valid",closure,()),projection.closure_projection,metadata,
            _restriction_event_targets(closure.restrictions,metadata),ticket,lifecycle_epoch,
            lifecycle_signature,binding,default_selection)
        return FinalOutputSyncResult("valid",context=context,
            expected_transition_input_digest=input_snapshot.input_digest,
            expected_application_binding_digest=(
                None if default_selection is None else default_selection.selection_digest
            ))
    except InterruptedError:
        return FinalOutputSyncResult("unavailable",expected_transition_input_digest=input_snapshot.input_digest)
    except (ValueError,TypeError,AttributeError,RuntimeError,OverflowError) as error:
        return FinalOutputSyncResult("invalid",issues=(ClosureIssue("input_invalid","bounded_transition",str(error)),),
                                    expected_transition_input_digest=input_snapshot.input_digest)
