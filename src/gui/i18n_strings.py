from __future__ import annotations


class LeftInfoPanelStrings:
    SECTION_TITLE_FILES = "入力ファイル"
    SECTION_TITLE_TEXT = "テキスト確認"
    SECTION_TITLE_CONVERSION = "変換結果"
    SECTION_TITLE_AUDIO = "音声情報"

    LABEL_TEXT_PATH = "TEXT: 未選択"
    LABEL_WAV_PATH = "WAV: 未選択"
    LABEL_TEXT_PREVIEW = "TEXT全文確認"
    LABEL_HIRAGANA_PREVIEW = "ひらがな変換確認"
    LABEL_VOWEL_PREVIEW = "母音変換確認"
    LABEL_WAV_INFO = "WAV情報: 未読込"

    PLACEHOLDER_TEXT_PREVIEW = "ここにTEXTファイルの全文が表示されます"
    PLACEHOLDER_HIRAGANA_PREVIEW = "ここにひらがな変換後のTEXTが表示されます"
    PLACEHOLDER_VOWEL_PREVIEW = "ここに母音変換結果が表示されます"


class RightDisplayStrings:
    SECTION_TITLE_WAVEFORM = "波形表示"
    SECTION_TITLE_PREVIEW = "Preview"


class MorphUpperLimitStrings:
    LABEL = "モーフ上限値"


class OperationPanelStrings:
    BUTTON_TEXTS = {
        "text": "TXT\n読込",
        "wav": "WAV\n読込",
        "run": "処理\n実行",
        "save": "VMD\n保存",
        "play": "再生",
        "stop": "停止",
        "zoom_in": "拡大",
        "zoom_out": "縮小",
    }

    BUTTON_TOOLTIPS = {
        "text": "UTF-8 のテキストファイルを読み込みます。",
        "wav": "PCM WAV ファイルを読み込みます。",
        "run": "現在の TEXT と WAV を使って解析を実行します。",
        "save": "解析結果から VMD ファイルを保存します。",
        "play": "解析済みの WAV プレビューを再生します。",
        "stop": "再生中の WAV プレビューを停止します。",
        "zoom_in": "現在の表示範囲を拡大します。",
        "zoom_out": "現在の表示範囲を縮小します。",
    }


class StatusPanelStrings:
    STATUS_PREFIX = "出力状態: "
    FALLBACK_STATE_LABEL = "状態"


class MainWindowStrings:
    WINDOW_TITLE = "MMD AutoLip Tool"
    MENU_FILE = "ファイル"
    MENU_RUN = "処理"
    MENU_VIEW = "ビュー"
    MENU_HELP = "ヘルプ"
    MENU_VIEW_THEME = "テーマ"
    ACTION_THEME_DARK = "ダーク"
    ACTION_THEME_LIGHT = "ライト"
    PROCESSING_DIALOG_LABEL = "処理中です..."
    PROCESSING_DIALOG_TITLE = "処理中"
    VERSION_INFO_TITLE = "バージョン情報"
    VERSION_INFO_APP_VERSION = "MMD AutoLip Tool Ver 0.3.5.6"
    OUTPUT_COMPLETE_TITLE = "出力完了"
    OUTPUT_COMPLETE_MESSAGE = "VMDを出力しました:\n{output_path}"
    UNEXPECTED_ERROR_TITLE = "予期しないエラー"
    UNEXPECTED_ERROR_MESSAGE = "処理中に予期しないエラーが発生しました: {error}"
    WAV_INFO_NOT_LOADED = "WAV情報: 未読込"
    WAV_INFO_TEMPLATE = (
        "WAV情報: "
        "ファイル名={file_name} / "
        "再生時間={duration_sec:.3f}s / "
        "サンプリング周波数={sample_rate_hz}Hz / "
        "発話={speech_start_sec:.3f}s-{speech_end_sec:.3f}s"
    )
    TIMING_LABEL_OUTPUT_WHISPER = "Whisper時間アンカー"
    TIMING_LABEL_READY_WHISPER = "Whisper区間配分"
    TIMING_LABEL_FALLBACK = "均等配分(フォールバック)"


class ThemeStrings:
    DARK = "dark"
    LIGHT = "light"
    SUPPORTED = (DARK, LIGHT)


class StatusTexts:
    PLAYBACK = "出力状態: 再生中"
    PROCESSING = "出力状態: 解析中"
    FAILURE = "出力状態: 失敗"
    CANCELED = "出力状態: キャンセル"
    TEXT_LOAD_FAILURE = "出力状態: TEXT読込失敗"
    WAV_LOAD_FAILURE = "出力状態: WAV読込失敗"
    READY_ANALYSIS_PENDING = "出力状態: 解析未実行 (TEXT/WAV読込済み)"
    READY_TEXT_ONLY = "出力状態: 入力準備中 (TEXT読込済み / WAV未読込)"
    READY_WAV_ONLY = "出力状態: 入力準備中 (WAV読込済み / TEXT未読込)"
    READY_NOT_LOADED = "出力状態: 入力準備中 (TEXT/WAV未読込)"
    READY_ANALYSIS_DONE_PREFIX = "出力状態: 解析実行済み ("
    SUCCESS_TEMPLATE = "出力状態: 成功 ({output_name} / {timing_label})"

    READY_PREFIXES = (
        READY_ANALYSIS_PENDING,
        READY_TEXT_ONLY,
        READY_WAV_ONLY,
        READY_NOT_LOADED,
        READY_ANALYSIS_DONE_PREFIX,
    )
