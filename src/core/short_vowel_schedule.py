"""B4B source preparation and deterministic, bounded vowel scheduling.

Preparation is deliberately not an accepted output plan. Only the final issuer
may expose the independently checked schedule to consumers.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import dataclass, replace
from typing import Callable

from src.core.canonical_morph_value import canonicalize_morph_value
from src.core.cross_vowel_transition import (
    TRANSITION_POLICY_V2, TransitionPolicySnapshot, _canonical_value,
    effective_shapes_digest,
)
from src.core.effective_shape_plan import (
    BaseTimingPlanInput, EffectiveShape, EffectiveShapePlan, ShapeControlPoint,
    _manual_crossfade_context_for_shape,
    _build_effective_shape_plan, _normalization_contract, _validate_required_zero_conflicts,
    build_base_plan_identity,
)
from src.core.event_adjustment import AdjustmentLayerSnapshot
from src.core.final_morph_plan import effective_plan_snapshot_digest, FinalMorphIdentityContext
from src.core.transition_acoustic import TransitionAcousticSnapshot


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(_canonical_value(value), sort_keys=True,
                                    separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True)
class TransitionSourcePreparation:
    base_input: BaseTimingPlanInput
    adjustment_snapshot: AdjustmentLayerSnapshot
    source_identity: object
    acoustic_snapshot: object
    policy: TransitionPolicySnapshot
    unresolved_plan: EffectiveShapePlan
    zero_conflicts: tuple[tuple[str, int], ...]

    @property
    def source_digest(self) -> str:
        return digest((self.base_input, self.adjustment_snapshot, self.source_identity,
                       self.acoustic_snapshot, self.policy.policy_digest,
                       effective_plan_snapshot_digest(self.unresolved_plan), self.zero_conflicts))


def _conflicts(plan: EffectiveShapePlan) -> tuple[tuple[str, int], ...]:
    zeros, positive = {}, {}
    for i, shape in enumerate(plan.shapes):
        for p in shape.control_points:
            target = zeros if p.value == 0 and p.point_kind in {"start_zero", "end_zero"} else positive
            if p.value > 0 or target is zeros:
                target.setdefault((shape.vowel, p.frame_no), set()).add(i)
    return tuple(sorted(key for key, owners in zeros.items()
                        if any(a != b for a in owners for b in positive.get(key, ()))))


def prepare_transition_source(base_input, adjustment_snapshot, policy, *, source_identity, acoustic_snapshot):
    if not isinstance(policy, TransitionPolicySnapshot) or policy.policy_id != TRANSITION_POLICY_V2:
        raise ValueError("source preparation requires the explicit B4B policy")
    if not isinstance(base_input, BaseTimingPlanInput):
        raise ValueError("complete base input is required")
    identity = build_base_plan_identity(base_input)
    if not isinstance(source_identity, FinalMorphIdentityContext) or source_identity.base_plan_digest != identity.digest:
        raise ValueError("source identity differs from base input")
    if getattr(source_identity, "numeric_policy_id", None) is None:
        raise ValueError("complete profile/mapping source identity is required")
    if not isinstance(acoustic_snapshot, TransitionAcousticSnapshot) or acoustic_snapshot.state not in {"observed", "unobserved"}:
        raise ValueError("acoustic snapshot is invalid")
    plan = _build_effective_shape_plan(base_input, adjustment_snapshot, _defer_zero_conflicts=True)
    return TransitionSourcePreparation(base_input, plan.canonical_adjustment_snapshot,
        source_identity, acoustic_snapshot, policy, plan, _conflicts(plan))


def verify_preparation(preparation: TransitionSourcePreparation) -> None:
    if not isinstance(preparation, TransitionSourcePreparation):
        raise ValueError("typed source preparation is required")
    expected = prepare_transition_source(preparation.base_input, preparation.adjustment_snapshot,
        preparation.policy, source_identity=preparation.source_identity,
        acoustic_snapshot=preparation.acoustic_snapshot)
    if expected != preparation:
        raise ValueError("source preparation does not match the original input")


def curve_value(points, frame):
    if not points or frame < points[0].frame_no or frame > points[-1].frame_no:
        return 0.0
    for p in points:
        if frame == p.frame_no:
            return p.value
    for a, b in zip(points, points[1:]):
        if a.frame_no < frame < b.frame_no:
            return a.value + (b.value-a.value)*(frame-a.frame_no)/(b.frame_no-a.frame_no)
    return 0.0


def _probes(shapes):
    frames = sorted({p.frame_no for s in shapes for p in s.control_points})
    return frames + [(a+b)/2 for a,b in zip(frames, frames[1:])]


def _manual_overlap_override_allows_active_set(plan, shapes, frame, active):
    adjustments = {
        item.base_event_index: item
        for item in plan.canonical_adjustment_snapshot.adjustments
    }
    for candidate_shape in shapes:
        tail = candidate_shape.resolved_tail
        if tail is None or candidate_shape.shape_kind.startswith("long_vowel_"):
            continue
        owner = tail.tail_base_event_index
        adjustment = adjustments.get(owner)
        if (
            adjustment is None
            or not adjustment.manual_overlap_limit_override
            or candidate_shape.vowel not in active
            or curve_value(candidate_shape.control_points, frame) <= 0
        ):
            continue
        source_matches = tuple(
            (index, shape)
            for index, shape in enumerate(plan.shapes)
            if owner in shape.real_base_event_indices
            and shape.resolved_tail is not None
            and shape.resolved_tail.tail_base_event_index == owner
            and not shape.shape_kind.startswith("long_vowel_")
        )
        if len(source_matches) != 1:
            continue
        source_index, _source_shape = source_matches[0]
        context = _manual_crossfade_context_for_shape(
            plan.shapes,
            source_index,
            plan.effective_events,
        )
        if context is not None and frame > context.crossfade_limit_frame:
            return True
    return False


def independent_zeros(plan):
    structural = {(s.vowel,p.frame_no) for s in plan.shapes for p in s.control_points
                  if p.value == 0 and p.point_kind in {"start_zero","end_zero"}}
    result = set(plan.normalization_contract.required_zero_frames)-structural
    for a in plan.event_silence_admissions:
        for start,end in a.required_zero_frame_ranges:
            result.update((a.vowel,f) for f in range(start,end))
        if a.boundary_only and a.boundary_frame is not None:
            result.add((a.vowel,a.boundary_frame))
    return frozenset(result)


def mutable_shape_indices(plan):
    manual = {a.base_event_index for a in plan.canonical_adjustment_snapshot.adjustments if not a.is_empty}
    handoffs = {i for h in plan.observation_handoffs if h.enabled
                for i in (h.previous_non_zero_event_index,h.next_non_zero_event_index)}
    handoffs.update(i for h in plan.manual_crossfades for i in (h.source_base_event_index,h.target_base_event_index))
    admissions = {a.event_index:a for a in plan.event_silence_admissions}
    result = set()
    for i,s in enumerate(plan.shapes):
        if len(s.real_base_event_indices) != 1:
            continue
        owner = s.real_base_event_indices[0]
        e = plan.effective_events[owner]
        a = admissions.get(owner)
        if (owner not in manual|handoffs and not e.long_vowel_role
                and s.shape_kind == "asymmetric_trapezoid"
                and (a is None or a.enabled and not a.boundary_only)):
            result.add(i)
    return frozenset(result)


@dataclass(frozen=True)
class ScheduleChange:
    shape_index: int
    owner: int
    action: str
    before: tuple[ShapeControlPoint,...]
    after: tuple[ShapeControlPoint,...]
    reason: str | None = None


@dataclass(frozen=True)
class ScheduleResolution:
    source_digest: str
    baseline_digest: str
    shapes: tuple[EffectiveShape,...]
    changes: tuple[ScheduleChange,...]
    unresolved: tuple[tuple[int,str],...]
    closure_guards: tuple[tuple[str,int],...] = ()

    @property
    def resolution_digest(self):
        return digest(self)


@dataclass(frozen=True)
class _Option:
    shape: EffectiveShape
    cost: tuple[float,float,int]
    frames: tuple[int,...]
    short: bool


def _replace_shape(shape, points, *, resolved_tail=None):
    points = tuple(points)
    return replace(shape, control_points=points, event_ranges=((points[0].frame_no,points[-1].frame_no),),
                   resolved_tail=shape.resolved_tail if resolved_tail is None else resolved_tail)


def _scheduled_tail(shape, event, end_frame, *, short=False):
    tail = shape.resolved_tail
    if tail is None:
        return None
    if short or end_frame < event.end_frame:
        return replace(
            tail,
            effective_hold_frames=0,
            effective_softness_frames=0,
            has_slope_midpoint=False,
        )
    available = max(0, end_frame - event.end_frame)
    if tail.available_extension_frames is not None:
        available = min(available, tail.available_extension_frames)
    effective_hold = min(tail.requested_hold_frames, available)
    effective_softness = min(
        tail.requested_softness_frames,
        max(0, available - effective_hold),
    )
    return replace(
        tail,
        effective_hold_frames=effective_hold,
        effective_softness_frames=effective_softness,
        has_slope_midpoint=False,
    )


def _scheduled_control_points(shape, event, end_frame, *, short=False, peak_value=None):
    if short:
        peak_value = event.peak_value if peak_value is None else peak_value
        return (
            ShapeControlPoint(end_frame - 1, 0., "start_zero"),
            ShapeControlPoint(end_frame, peak_value, "top"),
            ShapeControlPoint(end_frame + 1, 0., "end_zero"),
        ), _scheduled_tail(shape, event, end_frame - 1, short=True)

    core_end = min(event.end_frame, end_frame)
    points = [
        point
        for point in shape.control_points
        if point.frame_no <= core_end
        and point.point_kind not in {"hold", "slope_mid", "end_zero"}
    ]
    tail = _scheduled_tail(shape, event, end_frame)
    if tail is None:
        closing_point = ShapeControlPoint(end_frame, 0., "end_zero")
        if points[-1].frame_no == end_frame:
            points[-1] = closing_point
        else:
            points.append(closing_point)
        return tuple(points), None

    effective_hold = tail.effective_hold_frames
    effective_softness = tail.effective_softness_frames
    closing_frame = core_end + effective_hold + effective_softness
    hold_frame = None
    if effective_hold > 0:
        hold_frame = max(core_end, closing_frame - effective_softness - 1)
        if points[-1].frame_no < hold_frame < closing_frame:
            points.append(ShapeControlPoint(hold_frame, event.peak_value, "hold"))
    has_slope_midpoint = False
    if effective_softness > 0:
        midpoint = closing_frame - 1
        minimum_midpoint = core_end if hold_frame is None else hold_frame + 1
        midpoint = max(midpoint, minimum_midpoint)
        if points[-1].frame_no < midpoint < closing_frame:
            points.append(
                ShapeControlPoint(
                    midpoint,
                    event.peak_value * tail.slope_ratio,
                    "slope_mid",
                )
            )
            has_slope_midpoint = True
    closing_point = ShapeControlPoint(closing_frame, 0., "end_zero")
    if points[-1].frame_no == closing_frame:
        points[-1] = closing_point
    else:
        points.append(closing_point)
    tail = replace(tail, has_slope_midpoint=has_slope_midpoint)
    return tuple(points), tail


def _schedule_change_reason(before, after, action):
    before_tail = before.resolved_tail
    after_tail = after.resolved_tail
    if before_tail is None or after_tail is None:
        return None
    if action == "short_pulse" and (
        after_tail.requested_hold_frames or after_tail.requested_softness_frames
    ):
        return "tail_not_applicable_to_short_pulse"
    before_total = before_tail.effective_hold_frames + before_tail.effective_softness_frames
    after_total = after_tail.effective_hold_frames + after_tail.effective_softness_frames
    if after_total < before_total:
        return "tail_reduced_for_schedule_overlap"
    if (
        after_tail.requested_softness_frames > 0
        and after_tail.effective_softness_frames == 0
        and not after_tail.has_slope_midpoint
    ):
        return "tail_slope_midpoint_unavailable"
    return None


def _tail_reduction_cost(before, after):
    before_tail = before.resolved_tail
    after_tail = after.resolved_tail
    if before_tail is None or after_tail is None:
        return 0
    before_total = before_tail.effective_hold_frames + before_tail.effective_softness_frames
    after_total = after_tail.effective_hold_frames + after_tail.effective_softness_frames
    return max(0, before_total - after_total)


def _options(prep, shape):
    owner = shape.real_base_event_indices[0]
    base = prep.unresolved_plan.base_events[owner]
    event = prep.unresolved_plan.effective_events[owner]
    width = (base.end_sec-base.start_sec)*30
    amplitude = event.peak_value
    short = amplitude > 0 and width > 0 and (width < 1 or not any(
        curve_value(shape.control_points,f)>0 for f in range(shape.start_frame,shape.end_frame+1)))
    if short:
        peak = canonicalize_morph_value(min(amplitude, amplitude*width/2)).scalar
        if peak <= 0:
            return (), True
        result=[]
        for k in sorted({round(base.time_sec*30)+d for d in (-1,0,1)},key=lambda k:(abs(k-base.time_sec*30),k)):
            if k-1 < 0 or k+1 > prep.base_input.source_duration_frames:
                continue
            points, tail = _scheduled_control_points(
                shape,
                event,
                k,
                short=True,
                peak_value=peak,
            )
            candidate = _replace_shape(shape, points, resolved_tail=tail)
            result.append(_Option(
                candidate,
                (_tail_reduction_cost(shape,candidate),abs(k-base.time_sec*30),0),
                (k,k-1,k+1,k+1),
                True,
            ))
        return tuple(result),True
    result=[]
    # Treat the selected zero frame as a joint event-end/tail candidate. The
    # cost first minimizes lost effective tail frames so a feasible closing
    # hold/softness is retained; overlap constraints can still force reduction.
    for end in range(shape.end_frame,max(event.peak_frame,shape.start_frame),-1):
        if end == shape.end_frame:
            candidate=shape
        else:
            points, tail = _scheduled_control_points(shape, event, end)
            candidate=_replace_shape(shape,points,resolved_tail=tail)
        if candidate.control_points[0].value > 0 and candidate.start_frame > 0:
            # A positive start after a distant same-morph terminal otherwise
            # interpolates across the entire gap in MMD.
            candidate=_replace_shape(candidate,(
                ShapeControlPoint(candidate.start_frame-1,0.,"start_zero"),
                *candidate.control_points))
        result.append(_Option(
            candidate,
            (
                _tail_reduction_cost(shape,candidate),
                abs(end-base.end_sec*30) if end!=shape.end_frame else 0.,
                shape.end_frame-candidate.end_frame,
            ),
            (event.peak_frame,candidate.start_frame,end,candidate.end_frame),
            False,
        ))
    if not result:
        result=[_Option(shape,(0.,0.,0),(event.peak_frame,shape.start_frame,shape.end_frame,shape.end_frame),False)]
    return tuple(result),False


def _wire_shapes(shapes):
    result=[]
    for s in shapes:
        if (s.control_points[0].value>0 and s.start_frame>0
                and not any(other is not s and other.vowel==s.vowel
                    and curve_value(other.control_points,s.start_frame-1)>0 for other in shapes)):
            s=replace(s,control_points=(ShapeControlPoint(s.start_frame-1,0.,"start_zero"),*s.control_points))
        result.append(s)
    return tuple(result)


def _closure_guards(shapes):
    return tuple(sorted({(s.vowel,s.start_frame) for old,s in zip(shapes,_wire_shapes(shapes))
                         if old.control_points!=s.control_points}))


def _hard_valid(shapes, plan):
    shapes=_wire_shapes(shapes)
    try:
        _validate_required_zero_conflicts(tuple(shapes))
    except ValueError:
        return False
    for vowel,frame in independent_zeros(plan):
        if any(s.vowel==vowel and curve_value(s.control_points,frame)>0 for s in shapes):
            return False
    for start,end in plan.silence_core_frame_ranges:
        for s in shapes:
            probes=[start,end]+[p.frame_no for p in s.control_points if start<=p.frame_no<=end]
            if any(curve_value(s.control_points,x)>0 for x in probes):
                return False
    # Disjoint same-morph shapes must not create a zero/positive collision or
    # overlap. The source grouping semantics remain intact.
    for a,b in itertools.combinations(shapes,2):
        if a.vowel==b.vowel and max(a.start_frame,b.start_frame)<min(a.end_frame,b.end_frame):
            return False
    return True


def _limits_valid(shapes, fixed_indices, plan):
    shapes=_wire_shapes(shapes)
    for x in _probes(shapes):
        active={s.vowel for s in shapes if curve_value(s.control_points,x)>0}
        fixed={s.vowel for i,s in enumerate(shapes) if i in fixed_indices and curve_value(s.control_points,x)>0}
        if len(active)>2 and not (len(fixed)>2 and active==fixed):
            if not _manual_overlap_override_allows_active_set(
                plan, shapes, x, active
            ):
                return False
    ordered=sorted(enumerate(shapes),key=lambda z:min(z[1].real_base_event_indices or (10**12,)))
    for position,(i,shape) in enumerate(ordered[:-1]):
        if i in fixed_indices or not any(p.value>0 for p in shape.control_points):
            continue
        _j,next_shape=ordered[position+1]
        if shape.vowel==next_shape.vowel or next_shape.start_frame>=shape.end_frame:
            continue
        if any(shape.end_frame<=a<=next_shape.start_frame for a,b in plan.silence_core_frame_ranges):
            continue
        if shape.end_frame>next_shape.start_frame+3:
            return False
    return True


def _components(options, shapes):
    bounds={i:(min((o.shape.start_frame for o in opts),default=shapes[i].start_frame),
               max((o.shape.end_frame for o in opts),default=shapes[i].end_frame)) for i,opts in options.items()}
    components=[]
    for i in sorted(options,key=lambda i:(bounds[i][0],i)):
        touching=[c for c in components if any(max(bounds[i][0],bounds[j][0])<=min(bounds[i][1],bounds[j][1]) for j in c)]
        merged={i}
        for c in touching:
            merged.update(c)
            components.remove(c)
        components.append(merged)
    return bounds,components


def schedule_vowels(preparation, baseline_shapes=None, *, cancelled: Callable[[],bool] | None=None):
    verify_preparation(preparation)
    plan=preparation.unresolved_plan
    shapes=tuple(plan.shapes if baseline_shapes is None else baseline_shapes)
    if len(shapes)!=len(plan.shapes):
        raise ValueError("schedule baseline shape count differs from source")
    mutable=mutable_shape_indices(plan)
    options={}; shorts=set()
    for i,s in enumerate(shapes):
        if i in mutable:
            options[i],short=_options(preparation,s)
            if short: shorts.add(i)
        else:
            options[i]=(_Option(s,(0.,0.,0),(),False),)
    # Components include every possible support, not only the first choice.
    bounds,components=_components(options,shapes)
    selected=list(shapes); unresolved=[]
    for component in components:
        indices=sorted(component,key=lambda i:min(shapes[i].real_base_event_indices or (10**12,)))
        fixed=frozenset(k for k,i in enumerate(indices) if i not in mutable)
        original=tuple(shapes[i] for i in indices)
        best=None; best_cost=None
        # An iterative frontier avoids recursion limits on long utterances.
        stack=[(0,(),(0.,0.,0),())]
        memo={}
        while stack:
            if cancelled is not None and cancelled():
                raise InterruptedError("vowel schedule cancelled")
            pos,chosen,cost,frame_key=stack.pop()
            if best_cost is not None and cost>best_cost[:3]:
                continue
            if pos==len(indices):
                candidate=tuple(o.shape for o in chosen)
                if _hard_valid(candidate,plan) and _limits_valid(candidate,fixed,plan):
                    key=(*cost,frame_key)
                    if best_cost is None or key<best_cost: best,best_cost=candidate,key
                continue
            i=indices[pos]
            for option in reversed(options[i]):
                next_chosen=chosen+(option,)
                partial=tuple(o.shape for o in next_chosen)
                if not _hard_valid(partial,plan):
                    continue
                if not _limits_valid(partial,frozenset(k for k in fixed if k<len(partial)),plan):
                    continue
                next_cost=tuple(a+b for a,b in zip(cost,option.cost))
                next_key=frame_key+option.frames
                # Past shapes which cannot meet any remaining support are
                # summarized by the cost. Only the active frontier is retained.
                lower=min((bounds[j][0] for j in indices[pos+1:]),default=float('inf'))
                frontier=tuple((indices[k],o.shape.control_points) for k,o in enumerate(next_chosen) if o.shape.end_frame>=lower)
                state=(pos+1,frontier)
                score=(*next_cost,next_key)
                if state in memo and memo[state]<=score:
                    continue
                memo[state]=score
                stack.append((pos+1,next_chosen,next_cost,next_key))
        if best is None:
            if not _hard_valid(original,plan):
                raise ValueError("unresolved required-zero collision in schedule component")
            for i in indices:
                if i in mutable:
                    unresolved.append((i,"short_event_not_representable" if i in shorts else "overlap_limit_unresolved"))
        else:
            for i,s in zip(indices,best): selected[i]=s
    changes=[]
    for i,(a,b) in enumerate(zip(shapes,selected)):
        if a!=b:
            action="short_pulse" if i in shorts else "early_release" if b.end_frame<a.end_frame else "closure_reposition"
            changes.append(ScheduleChange(i,a.real_base_event_indices[0],action,a.control_points,b.control_points,
                                          _schedule_change_reason(a,b,action)))
    wire_shapes=_wire_shapes(selected)
    for i,s in enumerate(wire_shapes):
        if i not in mutable and any(len({t.vowel for t in wire_shapes if curve_value(t.control_points,x)>0})>2
                                    and curve_value(s.control_points,x)>0 for x in _probes(wire_shapes)):
            unresolved.append((i,"protected_overlap_exemption"))
    return ScheduleResolution(preparation.source_digest,effective_shapes_digest(shapes),tuple(selected),tuple(changes),
        tuple(sorted(set(unresolved))),_closure_guards(tuple(selected)))


def apply_schedule(preparation, resolution):
    plan=preparation.unresolved_plan
    events=list(plan.effective_events)
    for change in resolution.changes:
        shape=resolution.shapes[change.shape_index]
        e=events[change.owner]
        peak=max(shape.control_points,key=lambda p:p.value)
        scheduled_end_frame = (
            shape.end_frame
            if change.action == "short_pulse"
            else min(e.end_frame, shape.end_frame)
        )
        events[change.owner]=replace(e,start_frame=shape.start_frame,end_frame=scheduled_end_frame,
                                    peak_frame=peak.frame_no if change.action=="short_pulse" else e.peak_frame,
                                    peak_value=peak.value if change.action=="short_pulse" else e.peak_value)
    return replace(plan,shapes=resolution.shapes,effective_events=tuple(events),
        normalization_contract=_normalization_contract(resolution.shapes,
            additional_required_zero_frames=tuple(independent_zeros(plan)|set(resolution.closure_guards))))


def validate_schedule(preparation,resolution,baseline_shapes=None):
    """Check source, permitted edits and constraints independently of producer."""
    verify_preparation(preparation)
    plan=preparation.unresolved_plan
    baseline=tuple(plan.shapes if baseline_shapes is None else baseline_shapes)
    if (not isinstance(resolution,ScheduleResolution) or resolution.source_digest!=preparation.source_digest
            or resolution.baseline_digest!=effective_shapes_digest(baseline) or len(resolution.shapes)!=len(baseline)):
        raise ValueError("schedule source binding mismatch")
    mutable=mutable_shape_indices(plan)
    expected_changes=[]
    for i,(old,new) in enumerate(zip(baseline,resolution.shapes)):
        if old!=new:
            if i not in mutable:
                raise ValueError("schedule changed a protected shape")
            options,short=_options(preparation,old)
            if new not in tuple(o.shape for o in options):
                raise ValueError("schedule contains an unauthorized placement")
            action="short_pulse" if short else "early_release" if new.end_frame<old.end_frame else "closure_reposition"
            expected_changes.append(ScheduleChange(
                i,
                old.real_base_event_indices[0],
                action,
                old.control_points,
                new.control_points,
                _schedule_change_reason(old,new,action),
            ))
    if tuple(expected_changes)!=resolution.changes or not _hard_valid(resolution.shapes,plan):
        raise ValueError("schedule changes or hard closure constraints are invalid")
    if resolution.closure_guards!=_closure_guards(resolution.shapes):
        raise ValueError("schedule closure guards differ from the source-derived gaps")
    unresolved={i for i,r in resolution.unresolved if r!="protected_overlap_exemption"}
    for i,r in resolution.unresolved:
        if type(i) is not int or not 0<=i<len(baseline) or r not in {"short_event_not_representable","overlap_limit_unresolved","release_limit_unresolved","protected_overlap_exemption"}:
            raise ValueError("unknown schedule outcome")
        if r!="protected_overlap_exemption" and resolution.shapes[i]!=baseline[i]:
            raise ValueError("unresolved shape was modified")
        if r=="protected_overlap_exemption" and i in mutable:
            raise ValueError("automatic shape cannot claim a protected overlap exemption")
    checked=tuple(s for i,s in enumerate(resolution.shapes) if i not in unresolved)
    fixed=frozenset(k for k,(i,s) in enumerate((i,s) for i,s in enumerate(resolution.shapes) if i not in unresolved) if i not in mutable)
    if not _limits_valid(checked,fixed,plan):
        raise ValueError("schedule exceeds active-morph or release limits")
    _validate_selection(preparation,resolution,baseline,mutable)


def _validate_selection(preparation,resolution,baseline,mutable):
    """Search for a strictly better witness, without invoking the producer.

    This also prevents an otherwise legal source from being falsely labelled
    unrepresentable. Frontier states retain only supports which can still meet
    an unassigned event; the cheapest prefix dominates the others.
    """
    options={i:_options(preparation,s)[0] if i in mutable else
             (_Option(s,(0.,0.,0),(),False),) for i,s in enumerate(baseline)}
    bounds,components=_components(options,baseline)
    unresolved={i for i,r in resolution.unresolved if r!='protected_overlap_exemption'}
    for component in components:
        ids=sorted(component,key=lambda i:min(baseline[i].real_base_event_indices or (10**12,)))
        excluded=component&unresolved
        if excluded and (excluded!=component&mutable or any(resolution.shapes[i]!=baseline[i] for i in component)):
            raise ValueError("incomplete unresolved-component record")
        target=None
        if not excluded:
            chosen=[next((o for o in options[i] if o.shape==resolution.shapes[i]),None) for i in ids]
            if any(o is None for o in chosen):
                raise ValueError("selected schedule is outside its source domain")
            target=tuple(sum(o.cost[k] for o in chosen) for k in range(3))+(tuple(f for o in chosen for f in o.frames),)
        frontier_states=[((),(0.,0.,0),())]
        fixed=frozenset(k for k,i in enumerate(ids) if i not in mutable)
        for pos,i in enumerate(ids):
            next_states={}
            for prefix,cost,frame_key in frontier_states:
                for option in options[i]:
                    new_cost=tuple(a+b for a,b in zip(cost,option.cost))
                    if target is not None and new_cost>target[:3]:
                        continue
                    shapes=prefix+(option.shape,)
                    if not _hard_valid(shapes,preparation.unresolved_plan):
                        continue
                    if not _limits_valid(shapes,frozenset(k for k in fixed if k<len(shapes)),preparation.unresolved_plan):
                        continue
                    key=frame_key+option.frames
                    if pos==len(ids)-1:
                        if target is None or (*new_cost,key)<target:
                            raise ValueError("schedule is nonminimal or falsely unrepresentable")
                        continue
                    lower=min(bounds[j][0] for j in ids[pos+1:])
                    state=tuple((ids[k],s.control_points) for k,s in enumerate(shapes) if s.end_frame>=lower)
                    score=(*new_cost,key)
                    old=next_states.get(state)
                    if old is None or score<(*old[1],old[2]):
                        next_states[state]=(shapes,new_cost,key)
            frontier_states=list(next_states.values())
