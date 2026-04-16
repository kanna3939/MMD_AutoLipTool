import threading
import wx
from core.pipeline import build_vowel_timing_plan

class AnalysisWorker(threading.Thread):
    def __init__(self, job_id, callback, error_callback, phase_callback, text_content, wav_path, wav_analysis, whisper_model_name="small", upper_limit=0.5):
        super().__init__()
        self.daemon = True
        self.job_id = job_id
        self.callback = callback
        self.error_callback = error_callback
        self.phase_callback = phase_callback
        self.text_content = text_content
        self.wav_path = wav_path
        self.wav_analysis = wav_analysis
        self.whisper_model_name = whisper_model_name
        self.upper_limit = upper_limit

    def run(self):
        def _phase_cb(phase_name):
            if self.phase_callback:
                wx.CallAfter(self.phase_callback, self.job_id, phase_name)

        try:
            plan = build_vowel_timing_plan(
                text_content=self.text_content,
                wav_path=self.wav_path,
                wav_analysis=self.wav_analysis,
                whisper_model_name=self.whisper_model_name,
                upper_limit=self.upper_limit,
                phase_callback=_phase_cb
            )
            wx.CallAfter(self.callback, self.job_id, plan)
        except Exception as e:
            wx.CallAfter(self.error_callback, self.job_id, e)
