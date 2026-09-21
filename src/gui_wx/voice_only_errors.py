from dataclasses import dataclass

from src.core.pipeline import PipelineError
from src.core.text_processing import TextProcessingError
from src.core.whisper_timing import WhisperTimingError
from src.core.whisper_model_runtime import WhisperModelRuntimeError


@dataclass(frozen=True)
class VoiceOnlyAnalysisErrorPresentation:
    category: str
    summary: str
    action: str

    def format_message(self, error: Exception) -> str:
        if isinstance(error, (WhisperTimingError, WhisperModelRuntimeError)):
            return f"{self.summary}\n{self.action}"
        return f"{self.summary}\n{self.action}\n\n詳細: {error}"


def classify_voice_only_analysis_error(error: Exception) -> VoiceOnlyAnalysisErrorPresentation:
    detail = str(error).lower()

    if isinstance(error, WhisperModelRuntimeError):
        if error.failure_class == "model_unavailable":
            return VoiceOnlyAnalysisErrorPresentation(
                category="voice_only_model_unavailable",
                summary="確認済みのWhisperモデルを利用できません。",
                action="モデルの保存状態を確認してから再解析してください。",
            )
        if error.failure_class == "integrity_mismatch":
            return VoiceOnlyAnalysisErrorPresentation(
                category="voice_only_model_integrity_failed",
                summary="Whisperモデルの検証に失敗しました。",
                action="モデルを確認してから再解析してください。",
            )
        if error.failure_class == "memory_failure":
            return VoiceOnlyAnalysisErrorPresentation(
                category="voice_only_model_memory_failed",
                summary="Whisperモデルを読み込むメモリが不足しました。",
                action="小さいモデルを選択して再解析してください。",
            )
        return VoiceOnlyAnalysisErrorPresentation(
            category="voice_only_whisper_runtime_failed",
            summary="Whisperモデルの処理に失敗しました。",
            action="モデルと音声の状態を確認して再解析してください。",
        )

    if isinstance(error, WhisperTimingError):
        if "no usable transcription text" in detail:
            return VoiceOnlyAnalysisErrorPresentation(
                category="voice_only_transcription_empty",
                summary="音声から有効な書き起こし結果を取得できませんでした。",
                action="発話が明瞭な音声か確認し、音声ファイルを読み込み直して再解析してください。",
            )
        if "timing anchor" in detail:
            return VoiceOnlyAnalysisErrorPresentation(
                category="voice_only_timing_anchor_failed",
                summary="書き起こしのタイミング情報を取得できませんでした。",
                action="発話区間を確認し、音声ファイルを読み込み直して再解析してください。",
            )
        return VoiceOnlyAnalysisErrorPresentation(
            category="voice_only_whisper_failed",
            summary="音声の書き起こしに失敗しました。",
            action="音声ファイル、Whisper、FFmpegの状態を確認して再解析してください。",
        )

    if isinstance(error, TextProcessingError):
        return VoiceOnlyAnalysisErrorPresentation(
            category="voice_only_text_conversion_failed",
            summary="書き起こし結果の日本語読み変換に失敗しました。",
            action="書き起こし内容を確認し、修正してから再解析してください。",
        )

    if "編集済み書き起こしテキストが空" in str(error):
        return VoiceOnlyAnalysisErrorPresentation(
            category="voice_only_edited_text_empty",
            summary="編集済みの書き起こしテキストが空です。",
            action="書き起こしテキストを入力して適用してから再解析してください。",
        )

    if "no vowels" in detail:
        return VoiceOnlyAnalysisErrorPresentation(
            category="voice_only_vowel_empty",
            summary="書き起こし結果から母音列を作成できませんでした。",
            action="書き起こし内容を確認し、日本語の発話テキストへ修正してから再解析してください。",
        )

    if isinstance(error, PipelineError) or "timing result" in detail or "timing plan" in detail:
        return VoiceOnlyAnalysisErrorPresentation(
            category="voice_only_timing_plan_invalid",
            summary="解析結果を再構築するための情報が不足しています。",
            action="音声のみ解析を最初からやり直してください。",
        )

    return VoiceOnlyAnalysisErrorPresentation(
        category="voice_only_analysis_failed",
        summary="音声のみ解析を完了できませんでした。",
        action="入力音声と書き起こし内容を確認して再解析してください。",
    )


def format_voice_only_analysis_error(error: Exception) -> str:
    presentation = classify_voice_only_analysis_error(error)
    return presentation.format_message(error)
