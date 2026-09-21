import threading
from dataclasses import dataclass
from typing import Any

import wx
from src.core.pipeline import build_vowel_timing_plan
from src.core.whisper_timing import extract_transcription_text, recognize_audio_timing
from src.core.whisper_model_runtime import (
    VerifiedAnalysisModelRequest,
    WhisperModelRuntime,
    WhisperModelSession,
)
from gui_wx.ui_state import INPUT_MODE_TEXT_AUDIO, INPUT_MODE_VOICE_ONLY


@dataclass(frozen=True)
class AnalysisWorkerResult:
    timing_plan: Any
    input_mode: str
    analysis_text_content: str
    analysis_text_source: str
    transcription_text: str = ""
    transcription_source: str = ""
    transcription_timing_source: str = ""
    whisper_timing_result: Any = None
    model_identity: Any = None
    debug_trace: Any = None

class AnalysisWorker(threading.Thread):
    def __init__(
        self,
        job_id,
        callback,
        error_callback,
        phase_callback,
        text_content,
        wav_path,
        wav_analysis,
        whisper_model_request: VerifiedAnalysisModelRequest | None = None,
        whisper_runtime: WhisperModelRuntime | None = None,
        upper_limit=0.5,
        input_mode=INPUT_MODE_TEXT_AUDIO,
        transcription_text_override=None,
        retained_whisper_timing_result=None,
        reuse_retained_timing=False,
        debug_trace=None,
    ):
        super().__init__()
        self.daemon = True
        self.job_id = job_id
        self.callback = callback
        self.error_callback = error_callback
        self.phase_callback = phase_callback
        self.text_content = text_content
        self.wav_path = wav_path
        self.wav_analysis = wav_analysis
        self.whisper_model_request = whisper_model_request
        self.whisper_runtime = whisper_runtime
        self.upper_limit = upper_limit
        self.input_mode = input_mode
        self.transcription_text_override = transcription_text_override
        self.retained_whisper_timing_result = retained_whisper_timing_result
        self.reuse_retained_timing = reuse_retained_timing
        self.debug_trace = debug_trace

    def run(self):
        def _phase_cb(phase_name):
            if self.phase_callback:
                wx.CallAfter(self.phase_callback, self.job_id, phase_name)

        session: WhisperModelSession | None = None
        try:
            if self.debug_trace is not None:
                self.debug_trace.record_stage(
                    "audio_analysis",
                    payload={
                        "duration_sec": getattr(self.wav_analysis, "duration_sec", None),
                        "sample_rate_hz": getattr(self.wav_analysis, "sample_rate_hz", None),
                        "channel_count": getattr(self.wav_analysis, "channel_count", None),
                        "has_speech": getattr(self.wav_analysis, "has_speech", None),
                        "speech_start_sec": getattr(self.wav_analysis, "speech_start_sec", None),
                        "speech_end_sec": getattr(self.wav_analysis, "speech_end_sec", None),
                        "source": "reused_input_metadata",
                    },
                )
            if not isinstance(self.whisper_model_request, VerifiedAnalysisModelRequest):
                raise ValueError("解析に使用するverified Whisper model requestがありません。")
            if not isinstance(self.whisper_runtime, WhisperModelRuntime):
                raise ValueError("Whisper model runtimeがありません。")
            session = self.whisper_runtime.acquire(self.whisper_model_request)
            if self.debug_trace is not None:
                self.debug_trace.set_model_identity(session.identity)
            if self.input_mode == INPUT_MODE_VOICE_ONLY:
                if self.reuse_retained_timing:
                    _phase_cb("編集済みテキスト再解析中")
                    if self.retained_whisper_timing_result is None:
                        raise ValueError("保持済みのWhisper timing resultがありません。")
                    transcription_text = (self.transcription_text_override or "").strip()
                    if not transcription_text:
                        raise ValueError("編集済み書き起こしテキストが空です。")
                    whisper_result = self.retained_whisper_timing_result
                    transcription_source = "user_edited_transcription"
                    analysis_text_source = "user_edited_transcription"
                else:
                    _phase_cb("Whisper 解析中")
                    whisper_result = recognize_audio_timing(
                        wav_path=self.wav_path,
                        model_session=session,
                        language="ja",
                        fp16=False,
                    )
                    transcription = extract_transcription_text(whisper_result.raw_result)
                    transcription_text = transcription.text
                    transcription_source = transcription.source
                    analysis_text_source = "whisper_transcription"
                if self.debug_trace is not None:
                    self.debug_trace.set_analysis_text(
                        transcription_text,
                        source=analysis_text_source,
                    )
                if self.debug_trace is not None:
                    self.debug_trace.record_stage(
                        "whisper_timing",
                        payload={
                            "source": "reused" if self.reuse_retained_timing else "generated",
                            "timing_source": getattr(whisper_result, "source", None),
                            "anchor_count": len(getattr(whisper_result, "anchors", ()) or ()),
                            "anchors": [
                                {
                                    "anchor_index": index,
                                    "start_sec": getattr(anchor, "start_sec", None),
                                    "end_sec": getattr(anchor, "end_sec", None),
                                }
                                for index, anchor in enumerate(
                                    getattr(whisper_result, "anchors", ()) or ()
                                )
                            ],
                            "model_identity": {
                                "model_key": getattr(session.identity, "model_key", None),
                                "manifest_identity": getattr(session.identity, "manifest_identity", None),
                            },
                        },
                    )
                plan = build_vowel_timing_plan(
                    text_content=transcription_text,
                    wav_path=self.wav_path,
                    wav_analysis=self.wav_analysis,
                    whisper_model_session=session,
                    upper_limit=self.upper_limit,
                    phase_callback=_phase_cb,
                    whisper_timing_result=whisper_result,
                    debug_trace=self.debug_trace,
                )
                if self.debug_trace is not None:
                    self.debug_trace.set_timing_source(getattr(plan, "source", None))
                result = AnalysisWorkerResult(
                    timing_plan=plan,
                    input_mode=INPUT_MODE_VOICE_ONLY,
                    analysis_text_content=transcription_text,
                    analysis_text_source=analysis_text_source,
                    transcription_text=transcription_text,
                    transcription_source=transcription_source,
                    transcription_timing_source=whisper_result.source,
                    whisper_timing_result=whisper_result,
                    model_identity=session.identity,
                    debug_trace=self.debug_trace,
                )
            else:
                if self.debug_trace is not None:
                    self.debug_trace.set_analysis_text(
                        self.text_content,
                        source="text_file",
                    )
                plan = build_vowel_timing_plan(
                    text_content=self.text_content,
                    wav_path=self.wav_path,
                    wav_analysis=self.wav_analysis,
                    whisper_model_session=session,
                    upper_limit=self.upper_limit,
                    phase_callback=_phase_cb,
                    debug_trace=self.debug_trace,
                )
                if self.debug_trace is not None:
                    self.debug_trace.set_timing_source(getattr(plan, "source", None))
                result = AnalysisWorkerResult(
                    timing_plan=plan,
                    input_mode=INPUT_MODE_TEXT_AUDIO,
                    analysis_text_content=self.text_content,
                    analysis_text_source="text_file",
                    model_identity=session.identity,
                    debug_trace=self.debug_trace,
                )
            wx.CallAfter(self.callback, self.job_id, result)
        except Exception as e:
            wx.CallAfter(self.error_callback, self.job_id, e)
        finally:
            if session is not None and self.whisper_runtime is not None:
                self.whisper_runtime.release(session)
