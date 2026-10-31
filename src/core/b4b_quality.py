"""Reported B4B quality coverage and source-bound adoption checks."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

from src.core.audio_probe import probe_audio_file
from src.core.mmd_wav_export import export_mmd_wav


CHECKS=frozenset({'short_opening','necessary_closure','mixed_morph_limit','continuity',
    'audio_sync','silence_protection','full_playback','load_playback','non_regression',
    'selection_edit_save','manual_undo_redo'})
MODELS=frozenset({'tda','mobco','miku_ver2','gui'})
MODES=frozenset({'text_audio','voice_only'})


def _sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def evaluate_b4b_report(comparison,report,comparison_sha):
    if set(report)!={'schema_id','comparison_sha256','accepted_modes','adoption_answer','items'}:
        raise ValueError('B4B report has missing or unknown fields')
    if report['schema_id']!='ms32-b4b-user-report/v2' or report['comparison_sha256']!=comparison_sha:
        raise ValueError('report belongs to a different candidate pack')
    modes=report['accepted_modes']
    if not isinstance(modes,list) or not modes or len(set(modes))!=len(modes) or not set(modes)<=MODES:
        raise ValueError('accepted modes are invalid')
    if report['adoption_answer'] not in {'accepted','needs_revision','pending'} or not isinstance(report['items'],list):
        raise ValueError('adoption answer/items are invalid')
    cases={c['case_id']:c for c in comparison['cases']}
    required={(model,mode,check) for mode in modes for model,checks in (
        ('tda',{'short_opening','necessary_closure','mixed_morph_limit','continuity','audio_sync','silence_protection','full_playback'}),
        ('mobco',{'short_opening','mixed_morph_limit','audio_sync'}),
        ('miku_ver2',{'load_playback','non_regression'})) for check in checks}
    required.update(('gui',mode,check) for mode in modes for check in {'selection_edit_save','manual_undo_redo'})
    covered=set(); failed=[]; seen=set()
    for item in report['items']:
        if not isinstance(item,dict) or set(item)!={'case_id','model_id','checks','result','note'}:
            raise ValueError('quality report item fields differ from schema')
        case=cases.get(item['case_id']); model=item['model_id']; checks=item['checks']
        if case is None or model not in MODELS or not isinstance(checks,list) or not checks or len(set(checks))!=len(checks) or not set(checks)<=CHECKS:
            raise ValueError('unknown case/model/check in report')
        if item['result'] not in {'pass','fail','not_evaluable','pending'} or not isinstance(item['note'],str):
            raise ValueError('invalid reported quality result')
        for check in checks:
            key=(item['case_id'],model,check)
            if key in seen: raise ValueError('duplicate quality observation')
            seen.add(key)
            if item['result']=='pass': covered.add((model,case['input_mode'],check))
            elif item['result']=='fail': failed.append(key)
    missing=sorted(required-covered)
    technical=all(c['status']=='valid' for c in cases.values())
    for mode in modes:
        if not any(c['input_mode']==mode and c.get('changes',0)>0 for c in cases.values()):
            missing.append(('technical',mode,'changed_candidate'))
    accepted=technical and not missing and not failed and report['adoption_answer']=='accepted'
    return {'schema_id':'ms32-b4b-adoption/v2','quality_assessment':'not_performed',
        'reported_quality':'pass' if accepted else 'fail' if failed or report['adoption_answer']=='needs_revision' else 'incomplete',
        'comparison_sha256':comparison_sha,'policy_digest':comparison['policy']['policy_digest'],
        'runtime_scope':{'input_modes':modes},'adoption':'accepted' if accepted else 'needs_revision' if failed or report['adoption_answer']=='needs_revision' else 'pending',
        'g32_04':'established' if accepted else 'not_established','missing':missing,'failed':failed,
        'limitations':{c['case_id']:c.get('unresolved',[]) for c in cases.values() if c.get('unresolved')},
        'exit_code':0 if accepted else 1 if failed or not technical or report['adoption_answer']=='needs_revision' else 2}


def _read(path):
    def pairs(items):
        result={}
        for k,v in items:
            if k in result: raise ValueError('duplicate JSON key')
            result[k]=v
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'),object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def _ref(ref,root=None):
    p=Path(ref['path']).resolve()
    if root is not None and root not in p.parents:
        raise ValueError('comparison artifact escaped pack root')
    if _sha(p)!=ref['sha256'] or p.stat().st_size!=ref['bytes']:
        raise ValueError('comparison artifact hash/size mismatch')
    return p


def _capture_artifact_path(capture, capture_manifest_ref, role):
    records=[record for record in capture['artifact_records'] if record.get('role')==role]
    if len(records)!=1:
        raise ValueError(f'capture must contain exactly one {role} artifact')
    record=records[0]
    capture_root=Path(capture_manifest_ref['path']).resolve().parent
    relative=Path(record['path'])
    if relative.is_absolute():
        raise ValueError('capture artifact path must be relative')
    artifact=(capture_root/relative).resolve()
    if capture_root not in artifact.parents:
        raise ValueError('capture artifact escaped capture root')
    if (_sha(artifact)!=record['sha256'] or artifact.stat().st_size!=record['bytes']):
        raise ValueError('capture artifact hash/size mismatch')
    return artifact


def _capture_audio_identity(capture, capture_manifest_ref, candidate_wav_sha256, repo):
    trace_path=_capture_artifact_path(capture,capture_manifest_ref,'analysis_trace')
    trace=_read(trace_path).get('input_identity')
    if not isinstance(trace,dict):
        raise ValueError('capture analysis trace has no input identity')
    analysis_wav=trace.get('analysis_wav')
    source_audio=trace.get('source_audio')
    if not isinstance(analysis_wav,dict) or not isinstance(source_audio,dict):
        raise ValueError('capture analysis trace has incomplete audio identity')
    analysis_sha=analysis_wav.get('sha256')
    source_sha=source_audio.get('sha256')
    for label,digest in (('analysis WAV',analysis_sha),('source audio',source_sha)):
        if (not isinstance(digest,str) or len(digest)!=64
                or any(character not in '0123456789abcdef' for character in digest)):
            raise ValueError(f'capture {label} SHA-256 is invalid')
    if candidate_wav_sha256!=analysis_sha:
        raise ValueError('candidate analysis WAV differs from captured analysis trace')
    if capture.get('input_hashes',{}).get('audio')!=source_sha:
        raise ValueError('capture input audio hash differs from analysis trace')
    if capture.get('origin',{}).get('audio_sha256')!=source_sha:
        raise ValueError('capture origin audio hash differs from analysis trace')
    basename=source_audio.get('file_basename')
    if (not isinstance(basename,str) or not basename or Path(basename).name!=basename
            or '/' in basename or '\\' in basename):
        raise ValueError('capture source audio filename is invalid')
    source_path=(repo/'MMD Files'/'Dialogue'/basename).resolve()
    source_root=(repo/'MMD Files'/'Dialogue').resolve()
    if source_root not in source_path.parents:
        raise ValueError('capture source audio escaped Dialogue root')
    if (_sha(source_path)!=source_sha
            or source_path.stat().st_size!=source_audio.get('bytes')):
        raise ValueError('source audio differs from captured input identity')
    return analysis_wav,source_audio,source_path


def _verify_mmd_wav_export(source_audio_path,source_audio_sha256,mmd_wav_path,
                           regenerated_wav_path,repo):
    if _sha(source_audio_path)!=source_audio_sha256:
        raise ValueError('source audio changed before MMD WAV verification')
    probe=probe_audio_file(source_audio_path,repo/'FFmpeg'/'bin'/'ffprobe.exe')
    export_mmd_wav(probe,repo/'FFmpeg'/'bin'/'ffmpeg.exe',regenerated_wav_path)
    if _sha(regenerated_wav_path)!=_sha(mmd_wav_path):
        raise ValueError('MMD WAV differs from product export of captured source audio')


def verify_b4b_comparison(path,*,audio_temp_dir):
    """Reissue the v2 issuer from retained source and verify the actual VMD."""
    from src.core.bounded_transition import bounded_runtime_digest, build_bounded_issuer
    from src.core.cross_vowel_transition import read_transition_policy, TransitionInputSnapshot, TRANSITION_POLICY_V2
    from src.core.final_morph_plan import FinalMorphIdentityContext
    from src.core.event_adjustment import AdjustmentLayerSnapshot
    from src.core.final_morph_transition_plan import read_final_morph_transition_plan, validate_transition_plan
    from src.core.final_output_state import FinalOutputOrigin
    from src.core.audio_processing import load_rms_series
    from src.core.transition_acoustic import build_transition_acoustic_snapshot
    from src.vmd_writer.final_morph_transition_adapter import validate_transition_vmd_readback
    path=Path(path).resolve(); comparison=_read(path); root=path.parent
    if comparison['schema_id']!='ms32-b4b-comparison/v2' or comparison['runtime_digest']!=bounded_runtime_digest():
        raise ValueError('comparison runtime/schema is stale or unknown')
    policy=read_transition_policy(comparison['policy'])
    if policy.policy_id!=TRANSITION_POLICY_V2:
        raise ValueError('v1 quality cannot adopt the v2 policy')
    research=_read(_ref(comparison['input_manifest']))
    captures={c['case_id']:c for c in research['captures']}
    expected={f'ms31-b1-0{i}-{mode}' for i in range(4) for mode in ('ta','vo')}
    if {c['case_id'] for c in comparison['cases']}!=expected or len(comparison['cases'])!=8:
        raise ValueError('technical comparison requires the eight retained cases')
    repo=Path(__file__).resolve().parents[2]
    audio_temp_dir=Path(audio_temp_dir).resolve()
    if not audio_temp_dir.is_dir():
        raise ValueError('audio verification temporary directory is unavailable')
    spec=importlib.util.spec_from_file_location('b4b_quality_decoder',repo/'tools/ms30-shadow-check.py')
    decoder=importlib.util.module_from_spec(spec);sys.modules[spec.name]=decoder;spec.loader.exec_module(decoder)
    wavs=list((Path(research['source_root'])/'cache/analysis_wav').glob('*.wav'))
    verified_mmd_exports=set()
    for case in comparison['cases']:
        if case['status']!='valid': raise ValueError('comparison case is not technically valid')
        capture_ref=captures[case['case_id']]['capture_manifest']
        capture=_read(_ref(capture_ref))
        if capture['case_id']!=case['case_id'] or capture['input_mode']!=case['input_mode']:
            raise ValueError('case identity/mode differs from retained capture')
        snapshot_path=_ref(case['source_snapshot']); raw=_read(snapshot_path)
        record=next(r for r in capture['artifact_records'] if r['role']=='full_snapshot')
        if record['sha256']!=_sha(snapshot_path): raise ValueError('source snapshot differs from capture')
        base=decoder._decode_base_input(raw['base_input'])
        adjustment=decoder._decode_typed(AdjustmentLayerSnapshot,raw['adjustment_snapshot'],'adjustment')
        identity=decoder._decode_typed(FinalMorphIdentityContext,raw['identity_context'],'identity')
        role=case['roles']['ms32_v2_candidate']
        plan=read_final_morph_transition_plan(_read(_ref(role['plan'],root)))
        wav_hash=plan.identity_context.source_lineage.analysis_wav_sha256
        analysis_wav,source_audio,source_audio_path=_capture_audio_identity(
            capture,capture_ref,wav_hash,repo)
        wav=next((p for p in wavs if _sha(p)==wav_hash),None)
        if wav is None: raise ValueError('retained analysis WAV missing')
        if wav.stat().st_size!=analysis_wav.get('bytes'):
            raise ValueError('retained analysis WAV size differs from capture trace')
        rms=load_rms_series(str(wav),window_ms=25,hop_ms=10,smoothing_frames=3,stereo_mode='average')
        acoustic=build_transition_acoustic_snapshot(rms_series=rms,source_sha256_before=wav_hash,
            source_sha256_after=_sha(wav),duration_sec=rms.duration_sec)
        origin=FinalOutputOrigin(identity.source_run_id,1,identity.analysis_generation,case['input_mode'],
            _sha(snapshot_path),None,str(wav),None,'retained-'+case['case_id'],identity.base_plan_digest)
        x=TransitionInputSnapshot(identity.source_run_id,str(identity.analysis_generation),identity.manual_revision,
            case['input_mode'],wav_hash,identity.base_plan_digest,policy,acoustic)
        issuer,resolution=build_bounded_issuer(origin=origin,base_input=base,adjustment_snapshot=adjustment,
            input_snapshot=x,resolved_profile_id=identity.resolved_profile_id,
            output_morph_names=tuple(name for _,name in identity.output_mapping),
            capture_binding={'capture_manifest_sha256':captures[case['case_id']]['capture_manifest']['sha256'],
                'snapshot_sha256':_sha(snapshot_path),'legacy_baseline_status':case['roles']['ms31_baseline']['status']})
        if (case['changes'] != len(resolution.schedule.changes)
                or case['unresolved'] != [list(item) for item in resolution.schedule.unresolved]):
            raise ValueError('comparison schedule outcomes differ from independently validated source')
        from src.core.cross_vowel_transition import _canonical_value
        if _read(_ref(role['schedule'],root)) != _canonical_value(resolution.schedule):
            raise ValueError('stored schedule differs from independently validated source')
        for legacy_role in ('ms31_baseline','ms32_v1_reference'):
            if case['roles'][legacy_role]['status']=='generated':
                _ref(case['roles'][legacy_role],root)
        validation=validate_transition_plan(plan,issuer_context=issuer,resolution=resolution)
        if validation.state!='valid':
            raise ValueError(f"{case['case_id']}: stored candidate no longer validates against full source: {validation.issues}")
        validate_transition_vmd_readback(_ref(role,root),plan,issuer_context=issuer,resolution=resolution,model_name='AutoLipTool')
        mmd_wav_path=_ref(case['mmd_wav'],root)
        export_key=(source_audio['sha256'],case['mmd_wav']['sha256'])
        if export_key not in verified_mmd_exports:
            regenerated_wav=audio_temp_dir/f"{case['case_id']}-MMD.wav"
            _verify_mmd_wav_export(source_audio_path,source_audio['sha256'],mmd_wav_path,
                                   regenerated_wav,repo)
            verified_mmd_exports.add(export_key)
    return comparison


def check_b4b_adoption(comparison_path,report_path,output_root):
    comparison_path=Path(comparison_path).resolve(); report_path=Path(report_path).resolve()
    output_root=Path(output_root).resolve()
    if (output_root.exists() or output_root in comparison_path.parents or output_root in report_path.parents
            or comparison_path.parent==output_root):
        raise ValueError('output root exists or overlaps inputs')
    scratch_parent=output_root.parent if output_root.parent.is_dir() else Path('C:/tmp')
    with tempfile.TemporaryDirectory(prefix='ms32-b4b-audio-',dir=scratch_parent) as temp_dir:
        comparison=verify_b4b_comparison(comparison_path,audio_temp_dir=temp_dir)
    result=evaluate_b4b_report(comparison,_read(report_path),_sha(comparison_path))
    result['report_sha256']=_sha(report_path)
    output_root.mkdir(parents=True,exist_ok=False)
    out=output_root/'adoption.json'
    with out.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,sort_keys=True,indent=2)
    return out
