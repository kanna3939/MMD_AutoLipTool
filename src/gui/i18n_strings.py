from __future__ import annotations

from collections.abc import Mapping

SUPPORTED_LANGUAGES = ("ja", "en")
DEFAULT_LANGUAGE = "ja"
INTERNAL_VOWEL_ORDER = ("\u3042", "\u3044", "\u3046", "\u3048", "\u304a")


def normalize_language(language: str | None) -> str:
    resolved = str(language or "").strip().lower()
    if resolved in SUPPORTED_LANGUAGES:
        return resolved
    return DEFAULT_LANGUAGE


def localized_vowel_labels(language: str) -> dict[str, str]:
    resolved_language = normalize_language(language)
    if resolved_language == "en":
        return {
            "\u3042": "A",
            "\u3044": "I",
            "\u3046": "U",
            "\u3048": "E",
            "\u304a": "O",
        }
    return {vowel: vowel for vowel in INTERNAL_VOWEL_ORDER}


def localized_vowel_label(vowel: str, language: str) -> str:
    normalized_vowel = str(vowel)
    return localized_vowel_labels(language).get(normalized_vowel, normalized_vowel)


class _LocalizedStrings:
    _TRANSLATIONS: Mapping[str, Mapping[str, str]] = {}

    @classmethod
    def for_language(cls, language: str) -> dict[str, str]:
        return dict(cls._TRANSLATIONS[normalize_language(language)])


class CommonStrings(_LocalizedStrings):
    APP_NAME = "MMD AutoLip Tool"
    OK = "OK"
    CANCEL = "キャンセル"
    YES = "はい"
    NO = "いいえ"
    ERROR = "エラー"
    WARNING = "警告"
    NOT_SELECTED = "未選択"
    NOT_LOADED = "未読込"
    NOT_INSTALLED = "not installed"

    _TRANSLATIONS = {
        "ja": {
            "APP_NAME": APP_NAME,
            "OK": OK,
            "CANCEL": CANCEL,
            "YES": YES,
            "NO": NO,
            "ERROR": ERROR,
            "WARNING": WARNING,
            "NOT_SELECTED": NOT_SELECTED,
            "NOT_LOADED": NOT_LOADED,
            "NOT_INSTALLED": NOT_INSTALLED,
        },
        "en": {
            "APP_NAME": APP_NAME,
            "OK": "OK",
            "CANCEL": "Cancel",
            "YES": "Yes",
            "NO": "No",
            "ERROR": "Error",
            "WARNING": "Warning",
            "NOT_SELECTED": "Not selected",
            "NOT_LOADED": "Not loaded",
            "NOT_INSTALLED": "not installed",
        },
    }


class LeftInfoPanelStrings(_LocalizedStrings):
    SECTION_TITLE_FILES = "入力ファイル"
    SECTION_TITLE_TEXT = "テキスト表示"
    SECTION_TITLE_CONVERSION = "変換結果"
    SECTION_TITLE_AUDIO = "音声情報"

    LABEL_TEXT_PATH = f"TEXT: {CommonStrings.NOT_SELECTED}"
    LABEL_WAV_PATH = f"WAV: {CommonStrings.NOT_SELECTED}"
    LABEL_TEXT_PREVIEW = "TEXT全文表示"
    LABEL_HIRAGANA_PREVIEW = "ひらがな変換結果"
    LABEL_VOWEL_PREVIEW = "母音変換結果"
    LABEL_WAV_INFO = f"WAV情報: {CommonStrings.NOT_LOADED}"

    PLACEHOLDER_TEXT_PREVIEW = "ここにTEXTファイルの全文が表示されます。"
    PLACEHOLDER_HIRAGANA_PREVIEW = "ここにひらがな変換後のTEXTが表示されます。"
    PLACEHOLDER_VOWEL_PREVIEW = "ここに母音変換結果が表示されます。"

    _TRANSLATIONS = {
        "ja": {
            "SECTION_TITLE_FILES": SECTION_TITLE_FILES,
            "SECTION_TITLE_TEXT": SECTION_TITLE_TEXT,
            "SECTION_TITLE_CONVERSION": SECTION_TITLE_CONVERSION,
            "SECTION_TITLE_AUDIO": SECTION_TITLE_AUDIO,
            "LABEL_TEXT_PATH": LABEL_TEXT_PATH,
            "LABEL_WAV_PATH": LABEL_WAV_PATH,
            "LABEL_TEXT_PREVIEW": LABEL_TEXT_PREVIEW,
            "LABEL_HIRAGANA_PREVIEW": LABEL_HIRAGANA_PREVIEW,
            "LABEL_VOWEL_PREVIEW": LABEL_VOWEL_PREVIEW,
            "LABEL_WAV_INFO": LABEL_WAV_INFO,
            "PLACEHOLDER_TEXT_PREVIEW": PLACEHOLDER_TEXT_PREVIEW,
            "PLACEHOLDER_HIRAGANA_PREVIEW": PLACEHOLDER_HIRAGANA_PREVIEW,
            "PLACEHOLDER_VOWEL_PREVIEW": PLACEHOLDER_VOWEL_PREVIEW,
        },
        "en": {
            "SECTION_TITLE_FILES": "Input Files",
            "SECTION_TITLE_TEXT": "Text Preview",
            "SECTION_TITLE_CONVERSION": "Conversion",
            "SECTION_TITLE_AUDIO": "Audio Info",
            "LABEL_TEXT_PATH": "TEXT: Not selected",
            "LABEL_WAV_PATH": "WAV: Not selected",
            "LABEL_TEXT_PREVIEW": "Original TEXT",
            "LABEL_HIRAGANA_PREVIEW": "Hiragana",
            "LABEL_VOWEL_PREVIEW": "Vowels",
            "LABEL_WAV_INFO": "WAV Info: Not loaded",
            "PLACEHOLDER_TEXT_PREVIEW": "The loaded TEXT file will be shown here.",
            "PLACEHOLDER_HIRAGANA_PREVIEW": "Converted hiragana text will be shown here.",
            "PLACEHOLDER_VOWEL_PREVIEW": "Converted vowel text will be shown here.",
        },
    }


class RightDisplayStrings(_LocalizedStrings):
    SECTION_TITLE_WAVEFORM = "波形表示"
    SECTION_TITLE_PREVIEW = "Preview"

    _TRANSLATIONS = {
        "ja": {
            "SECTION_TITLE_WAVEFORM": SECTION_TITLE_WAVEFORM,
            "SECTION_TITLE_PREVIEW": SECTION_TITLE_PREVIEW,
        },
        "en": {
            "SECTION_TITLE_WAVEFORM": "Waveform",
            "SECTION_TITLE_PREVIEW": "Preview",
        },
    }


class MorphUpperLimitStrings(_LocalizedStrings):
    LABEL = "モーフ最大値"
    INPUT_TOOLTIP = "モーフ最大値を調整します。"
    DECREMENT_TOOLTIP = "モーフ最大値を下げます。"
    INCREMENT_TOOLTIP = "モーフ最大値を上げます。"

    _TRANSLATIONS = {
        "ja": {
            "LABEL": LABEL,
            "INPUT_TOOLTIP": INPUT_TOOLTIP,
            "DECREMENT_TOOLTIP": DECREMENT_TOOLTIP,
            "INCREMENT_TOOLTIP": INCREMENT_TOOLTIP,
        },
        "en": {
            "LABEL": "Morph Max",
            "INPUT_TOOLTIP": "Adjust the morph upper limit.",
            "DECREMENT_TOOLTIP": "Decrease the morph upper limit.",
            "INCREMENT_TOOLTIP": "Increase the morph upper limit.",
        },
    }


class ClosingSoftnessStrings(_LocalizedStrings):
    LABEL = "閉口スムース"
    UNIT = "フレーム"
    INPUT_TOOLTIP = "閉口スムースをフレーム数で調整します。"
    DECREMENT_TOOLTIP = "閉口スムースを下げます。"
    INCREMENT_TOOLTIP = "閉口スムースを上げます。"

    _TRANSLATIONS = {
        "ja": {
            "LABEL": LABEL,
            "UNIT": UNIT,
            "INPUT_TOOLTIP": INPUT_TOOLTIP,
            "DECREMENT_TOOLTIP": DECREMENT_TOOLTIP,
            "INCREMENT_TOOLTIP": INCREMENT_TOOLTIP,
        },
        "en": {
            "LABEL": "Closing Smooth",
            "UNIT": "Frame",
            "INPUT_TOOLTIP": "Adjust closing smooth in frames.",
            "DECREMENT_TOOLTIP": "Decrease closing smooth.",
            "INCREMENT_TOOLTIP": "Increase closing smooth.",
        },
    }


class LipHoldStrings(_LocalizedStrings):
    LABEL = "開口保持"
    UNIT = "フレーム"
    INPUT_TOOLTIP = "開口保持をフレーム数で調整します。"
    DECREMENT_TOOLTIP = "開口保持を下げます。"
    INCREMENT_TOOLTIP = "開口保持を上げます。"

    _TRANSLATIONS = {
        "ja": {
            "LABEL": LABEL,
            "UNIT": UNIT,
            "INPUT_TOOLTIP": INPUT_TOOLTIP,
            "DECREMENT_TOOLTIP": DECREMENT_TOOLTIP,
            "INCREMENT_TOOLTIP": INCREMENT_TOOLTIP,
        },
        "en": {
            "LABEL": "Lip Hold",
            "UNIT": "Frame",
            "INPUT_TOOLTIP": "Adjust lip hold in frames.",
            "DECREMENT_TOOLTIP": "Decrease lip hold.",
            "INCREMENT_TOOLTIP": "Increase lip hold.",
        },
    }


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
        "text": "UTF-8 のTEXTファイルを読み込みます。",
        "wav": "PCM WAV ファイルを読み込みます。",
        "run": "現在の TEXT と WAV を使って解析を実行します。",
        "save": "解析結果から VMD ファイルを保存します。",
        "play": "解析対象の WAV プレビューを再生します。",
        "stop": "再生中の WAV プレビューを停止します。",
        "zoom_in": "現在の表示範囲を拡大します。",
        "zoom_out": "現在の表示範囲を縮小します。",
    }

    _BUTTON_TEXTS_BY_LANGUAGE = {
        "ja": BUTTON_TEXTS,
        "en": {
            "text": "TXT",
            "wav": "WAV",
            "run": "Run",
            "save": "Save",
            "play": "Play",
            "stop": "Stop",
            "zoom_in": "Zoom In",
            "zoom_out": "Zoom Out",
        },
    }

    _BUTTON_TOOLTIPS_BY_LANGUAGE = {
        "ja": BUTTON_TOOLTIPS,
        "en": {
            "text": "Open a UTF-8 text file.",
            "wav": "Open a PCM WAV file.",
            "run": "Analyze the current TEXT and WAV.",
            "save": "Save a VMD file from the current analysis result.",
            "play": "Play the analyzed WAV preview.",
            "stop": "Stop the current WAV preview playback.",
            "zoom_in": "Zoom in on the current visible range.",
            "zoom_out": "Zoom out on the current visible range.",
        },
    }

    @classmethod
    def button_texts(cls, language: str) -> dict[str, str]:
        return dict(cls._BUTTON_TEXTS_BY_LANGUAGE[normalize_language(language)])

    @classmethod
    def button_tooltips(cls, language: str) -> dict[str, str]:
        return dict(cls._BUTTON_TOOLTIPS_BY_LANGUAGE[normalize_language(language)])


class StatusPanelStrings(_LocalizedStrings):
    STATUS_PREFIX = "出力状態: "
    FALLBACK_STATE_LABEL = "状態"

    _TRANSLATIONS = {
        "ja": {
            "STATUS_PREFIX": STATUS_PREFIX,
            "FALLBACK_STATE_LABEL": FALLBACK_STATE_LABEL,
        },
        "en": {
            "STATUS_PREFIX": "Status: ",
            "FALLBACK_STATE_LABEL": "State",
        },
    }


class WaveformViewStrings(_LocalizedStrings):
    PLACEHOLDER_NOT_LOADED = "波形プレビュー（未読込）"
    PLACEHOLDER_NO_DATA = "波形データがありません"
    AXIS_FRAME = "フレーム (30fps)"
    AXIS_SAMPLE = "サンプル"

    _TRANSLATIONS = {
        "ja": {
            "PLACEHOLDER_NOT_LOADED": PLACEHOLDER_NOT_LOADED,
            "PLACEHOLDER_NO_DATA": PLACEHOLDER_NO_DATA,
            "AXIS_FRAME": AXIS_FRAME,
            "AXIS_SAMPLE": AXIS_SAMPLE,
        },
        "en": {
            "PLACEHOLDER_NOT_LOADED": "Waveform preview (not loaded)",
            "PLACEHOLDER_NO_DATA": "No waveform data",
            "AXIS_FRAME": "Frame (30fps)",
            "AXIS_SAMPLE": "Sample",
        },
    }


class MainWindowStrings(_LocalizedStrings):
    APP_DISPLAY_NAME = CommonStrings.APP_NAME
    WINDOW_TITLE = APP_DISPLAY_NAME
    MENU_FILE = "ファイル"
    MENU_RUN = "処理"
    MENU_VIEW = "ビュー"
    MENU_VIEW_LANGUAGE = "言語"
    MENU_HELP = "ヘルプ"
    MENU_VIEW_THEME = "テーマ"

    ACTION_THEME_DARK = "ダーク"
    ACTION_THEME_LIGHT = "ライト"
    ACTION_OPEN_TEXT = "TEXTを開く"
    ACTION_OPEN_WAV = "WAVを開く"
    ACTION_SAVE_VMD = "VMDを保存"
    ACTION_EXIT = "終了"
    ACTION_RUN_PROCESSING = "処理実行"
    ACTION_REANALYZE = "再解析"
    ACTION_SHOW_30FPS_LINES = "30fps縦線を表示"
    ACTION_SHOW_VOWEL_LABELS = "母音ラベルを表示"
    ACTION_SHOW_EVENT_RANGES = "イベント区間を表示"
    ACTION_ZOOM_IN = "Zoom In"
    ACTION_ZOOM_OUT = "Zoom Out"
    ACTION_RESET_WAVEFORM_VIEW = "波形表示を初期化"
    ACTION_SHOW_VERSION = "バージョン情報"

    RECENT_TEXT_MENU = "最近使ったTEXT"
    RECENT_WAV_MENU = "最近使ったWAV"
    EMPTY_RECENT_FILES = "(履歴なし)"
    FILE_NOT_SELECTED_SUFFIX = CommonStrings.NOT_SELECTED
    INITIAL_STATUS = "出力状態: 未実行"

    PROCESSING_DIALOG_LABEL = "処理中です..."
    PROCESSING_DIALOG_TITLE = "処理中"

    VERSION_INFO_TITLE = "バージョン情報"
    VERSION_INFO_APP_VERSION_TEMPLATE = "{app_name} Ver {version}"
    VERSION_INFO_DEPENDENCY_TEMPLATE = "{name}: {version}"

    OUTPUT_COMPLETE_TITLE = "出力完了"
    OUTPUT_COMPLETE_MESSAGE = "VMDを出力しました:\n{output_path}"
    UNEXPECTED_ERROR_TITLE = "予期しないエラー"
    UNEXPECTED_ERROR_MESSAGE = "処理中に予期しないエラーが発生しました: {error}"

    SETTINGS_SAVE_WARNING_TITLE = "設定保存エラー"
    SETTINGS_SAVE_WARNING_MESSAGE = (
        "設定ファイルを保存できなかったため、このセッションでは設定保存を停止します。\n"
        "画面上の変更は反映されますが、次回起動時には保持されません。"
    )

    WAV_INFO_NOT_LOADED = f"WAV情報: {CommonStrings.NOT_LOADED}"
    WAV_INFO_TEMPLATE = (
        "WAV情報: "
        "ファイル名={file_name} / "
        "再生時間={duration_sec:.3f}s / "
        "サンプリング周波数={sample_rate_hz}Hz / "
        "音声区間={speech_start_sec:.3f}s-{speech_end_sec:.3f}s"
    )

    TIMING_LABEL_OUTPUT_WHISPER = "Whisper時間アンカー"
    TIMING_LABEL_READY_WHISPER = "Whisper音声解析"
    TIMING_LABEL_FALLBACK = "フォールバック"

    _TRANSLATIONS = {
        "ja": {
            "APP_DISPLAY_NAME": APP_DISPLAY_NAME,
            "WINDOW_TITLE": WINDOW_TITLE,
            "MENU_FILE": MENU_FILE,
            "MENU_RUN": MENU_RUN,
            "MENU_VIEW": MENU_VIEW,
            "MENU_VIEW_LANGUAGE": MENU_VIEW_LANGUAGE,
            "MENU_HELP": MENU_HELP,
            "MENU_VIEW_THEME": MENU_VIEW_THEME,
            "ACTION_THEME_DARK": ACTION_THEME_DARK,
            "ACTION_THEME_LIGHT": ACTION_THEME_LIGHT,
            "ACTION_OPEN_TEXT": ACTION_OPEN_TEXT,
            "ACTION_OPEN_WAV": ACTION_OPEN_WAV,
            "ACTION_SAVE_VMD": ACTION_SAVE_VMD,
            "ACTION_EXIT": ACTION_EXIT,
            "ACTION_RUN_PROCESSING": ACTION_RUN_PROCESSING,
            "ACTION_REANALYZE": ACTION_REANALYZE,
            "ACTION_SHOW_30FPS_LINES": ACTION_SHOW_30FPS_LINES,
            "ACTION_SHOW_VOWEL_LABELS": ACTION_SHOW_VOWEL_LABELS,
            "ACTION_SHOW_EVENT_RANGES": ACTION_SHOW_EVENT_RANGES,
            "ACTION_ZOOM_IN": ACTION_ZOOM_IN,
            "ACTION_ZOOM_OUT": ACTION_ZOOM_OUT,
            "ACTION_RESET_WAVEFORM_VIEW": ACTION_RESET_WAVEFORM_VIEW,
            "ACTION_SHOW_VERSION": ACTION_SHOW_VERSION,
            "RECENT_TEXT_MENU": RECENT_TEXT_MENU,
            "RECENT_WAV_MENU": RECENT_WAV_MENU,
            "EMPTY_RECENT_FILES": EMPTY_RECENT_FILES,
            "FILE_NOT_SELECTED_SUFFIX": FILE_NOT_SELECTED_SUFFIX,
            "INITIAL_STATUS": INITIAL_STATUS,
            "PROCESSING_DIALOG_LABEL": PROCESSING_DIALOG_LABEL,
            "PROCESSING_DIALOG_TITLE": PROCESSING_DIALOG_TITLE,
            "VERSION_INFO_TITLE": VERSION_INFO_TITLE,
            "VERSION_INFO_APP_VERSION_TEMPLATE": VERSION_INFO_APP_VERSION_TEMPLATE,
            "VERSION_INFO_DEPENDENCY_TEMPLATE": VERSION_INFO_DEPENDENCY_TEMPLATE,
            "VERSION_INFO_NOT_INSTALLED": CommonStrings.NOT_INSTALLED,
            "OUTPUT_COMPLETE_TITLE": OUTPUT_COMPLETE_TITLE,
            "OUTPUT_COMPLETE_MESSAGE": OUTPUT_COMPLETE_MESSAGE,
            "UNEXPECTED_ERROR_TITLE": UNEXPECTED_ERROR_TITLE,
            "UNEXPECTED_ERROR_MESSAGE": UNEXPECTED_ERROR_MESSAGE,
            "SETTINGS_SAVE_WARNING_TITLE": SETTINGS_SAVE_WARNING_TITLE,
            "SETTINGS_SAVE_WARNING_MESSAGE": SETTINGS_SAVE_WARNING_MESSAGE,
            "WAV_INFO_NOT_LOADED": WAV_INFO_NOT_LOADED,
            "WAV_INFO_TEMPLATE": WAV_INFO_TEMPLATE,
            "TIMING_LABEL_OUTPUT_WHISPER": TIMING_LABEL_OUTPUT_WHISPER,
            "TIMING_LABEL_READY_WHISPER": TIMING_LABEL_READY_WHISPER,
            "TIMING_LABEL_FALLBACK": TIMING_LABEL_FALLBACK,
            "TEXT_PREVIEW_HIRAGANA_FAILED": "(\u3072\u3089\u304c\u306a\u5909\u63db\u306b\u5931\u6557\u3057\u307e\u3057\u305f)",
            "TEXT_PREVIEW_HIRAGANA_PENDING": "(\u3072\u3089\u304c\u306a\u5909\u63db\u306f\u672a\u5b9f\u884c\u3067\u3059)",
            "TEXT_PREVIEW_VOWEL_PENDING": "(\u6bcd\u97f3\u5909\u63db\u306f\u672a\u5b9f\u884c\u3067\u3059)",
            "TEXT_PREVIEW_NO_VOWELS": "(\u6bcd\u97f3\u306e\u62bd\u51fa\u7d50\u679c\u306f\u3042\u308a\u307e\u305b\u3093)",
            "TEXT_LOAD_EMPTY_PATH": "TEXT\u30d5\u30a1\u30a4\u30eb\u306e\u30d1\u30b9\u304c\u7a7a\u3067\u3059\u3002",
            "TEXT_LOAD_NOT_FOUND": "TEXT\u30d5\u30a1\u30a4\u30eb\u304c\u5b58\u5728\u3057\u307e\u305b\u3093\u3002",
            "TEXT_LOAD_DIRECTORY_SELECTED": "TEXT\u30d5\u30a1\u30a4\u30eb\u3067\u306f\u306a\u304f\u30d5\u30a9\u30eb\u30c0\u304c\u9078\u629e\u3055\u308c\u3066\u3044\u307e\u3059\u3002",
            "TEXT_LOAD_CHECK_ERROR": "TEXT\u30d5\u30a1\u30a4\u30eb\u306e\u78ba\u8a8d\u4e2d\u306b\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
            "TEXT_LOAD_READ_ERROR": "TEXT\u30d5\u30a1\u30a4\u30eb\u3092\u8aad\u307f\u8fbc\u3081\u307e\u305b\u3093: {error}",
            "TEXT_LOAD_UNSUPPORTED_ENCODING": "\u5bfe\u5fdc\u3059\u308b\u6587\u5b57\u30b3\u30fc\u30c9\uff08UTF-8, Shift_JIS, UTF-16\uff09\u3067TEXT\u30d5\u30a1\u30a4\u30eb\u3092\u8aad\u307f\u8fbc\u3081\u307e\u305b\u3093\u3067\u3057\u305f\u3002",
            "TEXT_LOAD_EMPTY_FILE": "TEXT\u30d5\u30a1\u30a4\u30eb\u304c\u7a7a\u3067\u3059\u3002",
            "TEXT_CONVERSION_ERROR": "TEXT\u3092\u304b\u306a/\u3072\u3089\u304c\u306a\u306b\u5909\u63db\u3067\u304d\u307e\u305b\u3093: {error}",
            "TEXT_LOAD_UNEXPECTED_ERROR": "TEXT\u8aad\u307f\u8fbc\u307f\u4e2d\u306b\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
            "TEXT_CONVERSION_NO_VOWELS": "\u6bcd\u97f3\u3092\u62bd\u51fa\u3067\u304d\u308b\u6587\u5b57\u304c\u3042\u308a\u307e\u305b\u3093\u3002",
            "WAV_LOAD_FAILED_PLACEHOLDER": "\u6ce2\u5f62\u30d7\u30ec\u30d3\u30e5\u30fc (\u8aad\u8fbc\u5931\u6557)",
            "WAV_LOAD_EMPTY_PATH": "WAV\u30d5\u30a1\u30a4\u30eb\u306e\u30d1\u30b9\u304c\u7a7a\u3067\u3059\u3002",
            "WAV_LOAD_NOT_FOUND": "WAV\u30d5\u30a1\u30a4\u30eb\u304c\u5b58\u5728\u3057\u307e\u305b\u3093\u3002",
            "WAV_LOAD_DIRECTORY_SELECTED": "WAV\u30d5\u30a1\u30a4\u30eb\u3067\u306f\u306a\u304f\u30d5\u30a9\u30eb\u30c0\u304c\u9078\u629e\u3055\u308c\u3066\u3044\u307e\u3059\u3002",
            "WAV_LOAD_CHECK_ERROR": "WAV\u30d5\u30a1\u30a4\u30eb\u306e\u78ba\u8a8d\u4e2d\u306b\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
            "WAV_ANALYZE_ERROR": "WAV\u30d5\u30a1\u30a4\u30eb\u3092\u89e3\u6790\u3067\u304d\u307e\u305b\u3093: {error}",
            "WAV_ANALYZE_UNEXPECTED_ERROR": "WAV\u89e3\u6790\u4e2d\u306b\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
            "WAV_PREVIEW_ERROR": "WAV\u6ce2\u5f62\u3092\u8aad\u307f\u8fbc\u3081\u307e\u305b\u3093: {error}",
            "WAV_PREVIEW_UNEXPECTED_ERROR": "WAV\u6ce2\u5f62\u53d6\u5f97\u4e2d\u306b\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
            "WAV_INVALID_INFO": "WAV\u60c5\u5831\u304c\u7121\u52b9\u3067\u3059: {detail}",
            "WAV_INVALID_SAMPLE_RATE": "WAV\u306e\u30b5\u30f3\u30d7\u30ea\u30f3\u30b0\u5468\u6ce2\u6570\u304c\u7121\u52b9\u3067\u3059\u3002",
            "WAV_INVALID_FRAME_COUNT": "WAV\u306e\u30d5\u30ec\u30fc\u30e0\u6570\u304c\u7121\u52b9\u3067\u3059\u3002",
            "WAV_INVALID_DURATION": "WAV\u306e\u518d\u751f\u6642\u9593\u304c\u7121\u52b9\u3067\u3059\u3002",
            "WAV_INVALID_SPEECH_START": "WAV\u306e\u767a\u8a71\u958b\u59cb\u6642\u9593\u304c\u7121\u52b9\u3067\u3059\u3002",
            "WAV_INVALID_SPEECH_RANGE": "WAV\u306e\u767a\u8a71\u533a\u9593\u304c\u7121\u52b9\u3067\u3059\u3002",
            "WAV_INVALID_SPEECH_END": "WAV\u306e\u767a\u8a71\u7d42\u4e86\u6642\u9593\u304c\u518d\u751f\u6642\u9593\u3092\u8d85\u3048\u3066\u3044\u307e\u3059\u3002",
            "WAV_INVALID_PREVIEW_DURATION": "WAV\u6ce2\u5f62\u306e\u518d\u751f\u6642\u9593\u304c\u7121\u52b9\u3067\u3059\u3002",
            "WAV_INVALID_PREVIEW_SAMPLES": "WAV\u6ce2\u5f62\u306e\u8868\u793a\u30c7\u30fc\u30bf\u304c\u53d6\u5f97\u3067\u304d\u307e\u305b\u3093\u3002",
            "RECENT_TEXT_OPEN_FAILED": "\u6700\u8fd1\u4f7f\u3063\u305fTEXT\u3092\u958b\u3051\u307e\u305b\u3093: {detail}",
            "RECENT_TEXT_UNEXPECTED_ERROR": "\u6700\u8fd1\u4f7f\u3063\u305fTEXT\u306e\u8aad\u307f\u8fbc\u307f\u4e2d\u306b\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
            "RECENT_WAV_OPEN_FAILED": "\u6700\u8fd1\u4f7f\u3063\u305fWAV\u3092\u958b\u3051\u307e\u305b\u3093: {detail}",
            "RECENT_WAV_UNEXPECTED_ERROR": "\u6700\u8fd1\u4f7f\u3063\u305fWAV\u306e\u8aad\u307f\u8fbc\u307f\u4e2d\u306b\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
            "RECENT_INVALID_EMPTY_PATH": "\u30d1\u30b9\u304c\u7a7a\u3067\u3059\u3002",
            "RECENT_INVALID_NOT_FOUND": "\u30d5\u30a1\u30a4\u30eb\u304c\u5b58\u5728\u3057\u307e\u305b\u3093\u3002",
            "RECENT_INVALID_DIRECTORY": "\u30d5\u30a9\u30eb\u30c0\u304c\u9078\u629e\u3055\u308c\u3066\u3044\u307e\u3059\u3002",
            "RECENT_INVALID_CHECK_ERROR": "\u30d5\u30a1\u30a4\u30eb\u78ba\u8a8d\u4e2d\u306b\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
            "RECENT_INVALID_SUFFIX": "{expected_suffix} \u30d5\u30a1\u30a4\u30eb\u3067\u306f\u3042\u308a\u307e\u305b\u3093\u3002",
            "VMD_OUTPUT_EMPTY_PATH": "VMD\u306e\u4fdd\u5b58\u30d1\u30b9\u304c\u7a7a\u3067\u3059\u3002",
            "VMD_OUTPUT_INVALID_PATH": "VMD\u306e\u4fdd\u5b58\u30d1\u30b9\u304c\u4e0d\u6b63\u3067\u3059\u3002",
            "VMD_OUTPUT_DIRECTORY_SELECTED": "\u4fdd\u5b58\u5148\u306b\u30d5\u30a9\u30eb\u30c0\u304c\u9078\u629e\u3055\u308c\u3066\u3044\u307e\u3059\u3002\u30d5\u30a1\u30a4\u30eb\u540d\u3092\u6307\u5b9a\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
            "VMD_OUTPUT_PARENT_INVALID": "\u4fdd\u5b58\u5148\u30d5\u30a9\u30eb\u30c0\u304c\u4e0d\u6b63\u3067\u3059\u3002",
            "VMD_OUTPUT_CHECK_ERROR": "\u4fdd\u5b58\u5148\u306e\u78ba\u8a8d\u4e2d\u306b\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
            "EXPORT_INVALID_TEXT_CONVERSION": "TEXT\u304b\u3089\u6709\u52b9\u306a\u3072\u3089\u304c\u306a/\u6bcd\u97f3\u5217\u3092\u751f\u6210\u3067\u304d\u3066\u3044\u307e\u305b\u3093\u3002TEXT\u3092\u898b\u76f4\u3057\u3066\u518d\u8aad\u307f\u8fbc\u307f\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
            "EXPORT_MISSING_INPUTS": "TEXT\u3068WAV\u306e\u4e21\u65b9\u3092\u8aad\u307f\u8fbc\u3093\u3067\u304b\u3089\u51fa\u529b\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
            "EXPORT_ANALYSIS_NOT_RUN": "\u51e6\u7406\u5b9f\u884c\u30dc\u30bf\u30f3\u3067\u89e3\u6790\u3057\u3066\u304b\u3089\u51fa\u529b\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
            "EXPORT_OVERWRITE_CONFIRM_MESSAGE": "\u30d5\u30a1\u30a4\u30eb '{file_name}' \u306f\u65e2\u306b\u5b58\u5728\u3057\u307e\u3059\u3002\n\u4e0a\u66f8\u304d\u3057\u3066\u3082\u3088\u308d\u3057\u3044\u3067\u3059\u304b\uff1f",
            "EXPORT_TIMING_ERROR": "\u6bcd\u97f3\u30bf\u30a4\u30df\u30f3\u30b0\u3092\u6c7a\u5b9a\u3067\u304d\u307e\u305b\u3093: {error}",
            "EXPORT_PIPELINE_ERROR": "VMD\u306e\u51fa\u529b\u306b\u5931\u6557\u3057\u307e\u3057\u305f: {error}",
            "EXPORT_FILE_ERROR": "VMD\u4fdd\u5b58\u6642\u306b\u30d5\u30a1\u30a4\u30eb\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
            "PROCESSING_MISSING_TEXT": "TEXT\u3092\u8aad\u307f\u8fbc\u3093\u3067\u304b\u3089\u51e6\u7406\u5b9f\u884c\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
            "PROCESSING_MISSING_WAV": "WAV\u3092\u8aad\u307f\u8fbc\u3093\u3067\u304b\u3089\u51e6\u7406\u5b9f\u884c\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
            "PROCESSING_MISSING_VOWELS": "TEXT\u304b\u3089\u6709\u52b9\u306a\u3072\u3089\u304c\u306a/\u6bcd\u97f3\u5217\u3092\u751f\u6210\u3067\u304d\u3066\u3044\u307e\u305b\u3093\u3002",
            "PROCESSING_FAILED": "\u97f3\u58f0\u51e6\u7406\u306b\u5931\u6557\u3057\u307e\u3057\u305f\u3002",
            "TIMING_PLAN_TEXT_NOT_READY": "TEXT \u304c\u307e\u3060\u6e96\u5099\u3067\u304d\u3066\u3044\u307e\u305b\u3093\u3002",
            "TIMING_PLAN_WAV_NOT_READY": "WAV \u304c\u307e\u3060\u6e96\u5099\u3067\u304d\u3066\u3044\u307e\u305b\u3093\u3002",
            "TIMING_PLAN_NOT_ANALYZED": "\u89e3\u6790\u304c\u307e\u3060\u5b9f\u884c\u3055\u308c\u3066\u3044\u307e\u305b\u3093\u3002\u300c\u51e6\u7406\u5b9f\u884c\u300d\u3092\u62bc\u3057\u3066\u304b\u3089\u51fa\u529b\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
        },
        "en": {
            "APP_DISPLAY_NAME": APP_DISPLAY_NAME,
            "WINDOW_TITLE": WINDOW_TITLE,
            "MENU_FILE": "File",
            "MENU_RUN": "Run",
            "MENU_VIEW": "View",
            "MENU_VIEW_LANGUAGE": "Language",
            "MENU_HELP": "Help",
            "MENU_VIEW_THEME": "Theme",
            "ACTION_THEME_DARK": "Dark",
            "ACTION_THEME_LIGHT": "Light",
            "ACTION_OPEN_TEXT": "Open TEXT",
            "ACTION_OPEN_WAV": "Open WAV",
            "ACTION_SAVE_VMD": "Save VMD",
            "ACTION_EXIT": "Exit",
            "ACTION_RUN_PROCESSING": "Run",
            "ACTION_REANALYZE": "Reanalyze",
            "ACTION_SHOW_30FPS_LINES": "Show 30fps Grid",
            "ACTION_SHOW_VOWEL_LABELS": "Show Vowel Labels",
            "ACTION_SHOW_EVENT_RANGES": "Show Event Ranges",
            "ACTION_ZOOM_IN": "Zoom In",
            "ACTION_ZOOM_OUT": "Zoom Out",
            "ACTION_RESET_WAVEFORM_VIEW": "Reset Waveform View",
            "ACTION_SHOW_VERSION": "Version",
            "RECENT_TEXT_MENU": "Recent TEXT",
            "RECENT_WAV_MENU": "Recent WAV",
            "EMPTY_RECENT_FILES": "(No recent files)",
            "FILE_NOT_SELECTED_SUFFIX": "Not selected",
            "INITIAL_STATUS": "Status: Not started",
            "PROCESSING_DIALOG_LABEL": "Processing...",
            "PROCESSING_DIALOG_TITLE": "Processing",
            "VERSION_INFO_TITLE": "Version Information",
            "VERSION_INFO_APP_VERSION_TEMPLATE": "{app_name} Ver {version}",
            "VERSION_INFO_DEPENDENCY_TEMPLATE": "{name}: {version}",
            "VERSION_INFO_NOT_INSTALLED": "not installed",
            "OUTPUT_COMPLETE_TITLE": "Export Complete",
            "OUTPUT_COMPLETE_MESSAGE": "VMD export completed:\n{output_path}",
            "UNEXPECTED_ERROR_TITLE": "Unexpected Error",
            "UNEXPECTED_ERROR_MESSAGE": "An unexpected error occurred while processing: {error}",
            "SETTINGS_SAVE_WARNING_TITLE": "Settings Save Error",
            "SETTINGS_SAVE_WARNING_MESSAGE": (
                "The settings file could not be saved, so settings persistence is disabled "
                "for this session.\n"
                "Your on-screen changes still apply now, but they will not be kept next time."
            ),
            "WAV_INFO_NOT_LOADED": "WAV Info: Not loaded",
            "WAV_INFO_TEMPLATE": (
                "WAV Info: "
                "File={file_name} / "
                "Duration={duration_sec:.3f}s / "
                "Sample Rate={sample_rate_hz}Hz / "
                "Speech={speech_start_sec:.3f}s-{speech_end_sec:.3f}s"
            ),
            "TIMING_LABEL_OUTPUT_WHISPER": "Whisper timing anchors",
            "TIMING_LABEL_READY_WHISPER": "Whisper audio analysis",
            "TIMING_LABEL_FALLBACK": "Fallback",
            "TEXT_PREVIEW_HIRAGANA_FAILED": "(Hiragana conversion failed)",
            "TEXT_PREVIEW_HIRAGANA_PENDING": "(Hiragana conversion has not been run)",
            "TEXT_PREVIEW_VOWEL_PENDING": "(Vowel conversion has not been run)",
            "TEXT_PREVIEW_NO_VOWELS": "(No vowels were extracted)",
            "TEXT_LOAD_EMPTY_PATH": "The TEXT file path is empty.",
            "TEXT_LOAD_NOT_FOUND": "The TEXT file does not exist.",
            "TEXT_LOAD_DIRECTORY_SELECTED": "A folder was selected instead of a TEXT file.",
            "TEXT_LOAD_CHECK_ERROR": "An error occurred while checking the TEXT file: {error}",
            "TEXT_LOAD_READ_ERROR": "Could not read the TEXT file: {error}",
            "TEXT_LOAD_UNSUPPORTED_ENCODING": "The TEXT file could not be read with a supported encoding (UTF-8, Shift_JIS, UTF-16).",
            "TEXT_LOAD_EMPTY_FILE": "The TEXT file is empty.",
            "TEXT_CONVERSION_ERROR": "Could not convert the TEXT into kana/hiragana: {error}",
            "TEXT_LOAD_UNEXPECTED_ERROR": "An unexpected error occurred while loading the TEXT: {error}",
            "TEXT_CONVERSION_NO_VOWELS": "No characters were available for vowel extraction.",
            "WAV_LOAD_FAILED_PLACEHOLDER": "Waveform preview (load failed)",
            "WAV_LOAD_EMPTY_PATH": "The WAV file path is empty.",
            "WAV_LOAD_NOT_FOUND": "The WAV file does not exist.",
            "WAV_LOAD_DIRECTORY_SELECTED": "A folder was selected instead of a WAV file.",
            "WAV_LOAD_CHECK_ERROR": "An error occurred while checking the WAV file: {error}",
            "WAV_ANALYZE_ERROR": "Could not analyze the WAV file: {error}",
            "WAV_ANALYZE_UNEXPECTED_ERROR": "An unexpected error occurred while analyzing the WAV: {error}",
            "WAV_PREVIEW_ERROR": "Could not load the WAV waveform preview: {error}",
            "WAV_PREVIEW_UNEXPECTED_ERROR": "An unexpected error occurred while loading the waveform preview: {error}",
            "WAV_INVALID_INFO": "The WAV information is invalid: {detail}",
            "WAV_INVALID_SAMPLE_RATE": "The WAV sample rate is invalid.",
            "WAV_INVALID_FRAME_COUNT": "The WAV frame count is invalid.",
            "WAV_INVALID_DURATION": "The WAV duration is invalid.",
            "WAV_INVALID_SPEECH_START": "The WAV speech start time is invalid.",
            "WAV_INVALID_SPEECH_RANGE": "The WAV speech range is invalid.",
            "WAV_INVALID_SPEECH_END": "The WAV speech end time exceeds the playback duration.",
            "WAV_INVALID_PREVIEW_DURATION": "The waveform preview duration is invalid.",
            "WAV_INVALID_PREVIEW_SAMPLES": "The waveform preview display data could not be obtained.",
            "RECENT_TEXT_OPEN_FAILED": "Could not open the recent TEXT file: {detail}",
            "RECENT_TEXT_UNEXPECTED_ERROR": "An unexpected error occurred while loading a recent TEXT file: {error}",
            "RECENT_WAV_OPEN_FAILED": "Could not open the recent WAV file: {detail}",
            "RECENT_WAV_UNEXPECTED_ERROR": "An unexpected error occurred while loading a recent WAV file: {error}",
            "RECENT_INVALID_EMPTY_PATH": "The path is empty.",
            "RECENT_INVALID_NOT_FOUND": "The file does not exist.",
            "RECENT_INVALID_DIRECTORY": "A folder was selected.",
            "RECENT_INVALID_CHECK_ERROR": "An error occurred while checking the file: {error}",
            "RECENT_INVALID_SUFFIX": "This is not a {expected_suffix} file.",
            "VMD_OUTPUT_EMPTY_PATH": "The VMD output path is empty.",
            "VMD_OUTPUT_INVALID_PATH": "The VMD output path is invalid.",
            "VMD_OUTPUT_DIRECTORY_SELECTED": "A folder was selected as the save destination. Please specify a file name.",
            "VMD_OUTPUT_PARENT_INVALID": "The save destination folder is invalid.",
            "VMD_OUTPUT_CHECK_ERROR": "An error occurred while checking the save destination: {error}",
            "EXPORT_INVALID_TEXT_CONVERSION": "Valid hiragana/vowel text could not be generated from the TEXT. Please review and reload the TEXT.",
            "EXPORT_MISSING_INPUTS": "Load both the TEXT and WAV files before exporting.",
            "EXPORT_ANALYSIS_NOT_RUN": "Run the analysis before exporting.",
            "EXPORT_OVERWRITE_CONFIRM_MESSAGE": "The file '{file_name}' already exists.\nDo you want to overwrite it?",
            "EXPORT_TIMING_ERROR": "Could not determine vowel timing: {error}",
            "EXPORT_PIPELINE_ERROR": "VMD export failed: {error}",
            "EXPORT_FILE_ERROR": "A file error occurred while saving the VMD: {error}",
            "PROCESSING_MISSING_TEXT": "Load the TEXT file before running processing.",
            "PROCESSING_MISSING_WAV": "Load the WAV file before running processing.",
            "PROCESSING_MISSING_VOWELS": "Valid hiragana/vowel text could not be generated from the TEXT.",
            "PROCESSING_FAILED": "Audio processing failed.",
            "TIMING_PLAN_TEXT_NOT_READY": "The TEXT is not ready yet.",
            "TIMING_PLAN_WAV_NOT_READY": "The WAV is not ready yet.",
            "TIMING_PLAN_NOT_ANALYZED": "The analysis has not been run yet. Press \"Run\" before exporting.",
        },
    }


class FileDialogStrings(_LocalizedStrings):
    _TRANSLATIONS = {
        "ja": {
            "OPEN_TEXT_TITLE": "TEXTファイルを選択",
            "OPEN_WAV_TITLE": "WAVファイルを選択",
            "SAVE_VMD_TITLE": "VMDファイルの保存先を選択",
            "TEXT_FILTER": "Text Files (*.txt);;All Files (*)",
            "WAV_FILTER": "WAV Files (*.wav);;All Files (*)",
            "VMD_FILTER": "VMD Files (*.vmd);;All Files (*)",
        },
        "en": {
            "OPEN_TEXT_TITLE": "Select a TEXT file",
            "OPEN_WAV_TITLE": "Select a WAV file",
            "SAVE_VMD_TITLE": "Choose where to save the VMD file",
            "TEXT_FILTER": "Text Files (*.txt);;All Files (*)",
            "WAV_FILTER": "WAV Files (*.wav);;All Files (*)",
            "VMD_FILTER": "VMD Files (*.vmd);;All Files (*)",
        },
    }


class WarningDialogStrings(_LocalizedStrings):
    _TRANSLATIONS = {
        "ja": {
            "READ_ERROR_TITLE": "読み込みエラー",
            "TEXT_CONVERSION_ERROR_TITLE": "TEXT変換エラー",
            "INPUT_MISSING_TITLE": "入力不足",
            "ANALYSIS_NOT_RUN_TITLE": "未解析",
            "PROCESSING_ERROR_TITLE": "処理エラー",
            "OUTPUT_ERROR_TITLE": "出力エラー",
            "OVERWRITE_CONFIRM_TITLE": "上書き確認",
            "UNEXPECTED_ERROR_TITLE": MainWindowStrings.UNEXPECTED_ERROR_TITLE,
        },
        "en": {
            "READ_ERROR_TITLE": "Read Error",
            "TEXT_CONVERSION_ERROR_TITLE": "TEXT Conversion Error",
            "INPUT_MISSING_TITLE": "Missing Input",
            "ANALYSIS_NOT_RUN_TITLE": "Analysis Required",
            "PROCESSING_ERROR_TITLE": "Processing Error",
            "OUTPUT_ERROR_TITLE": "Export Error",
            "OVERWRITE_CONFIRM_TITLE": "Overwrite Confirmation",
            "UNEXPECTED_ERROR_TITLE": MainWindowStrings.UNEXPECTED_ERROR_TITLE,
        },
    }


class ThemeStrings:
    DARK = "dark"
    LIGHT = "light"
    SUPPORTED = (DARK, LIGHT)


class StatusTexts:
    STATUS_PREFIX = "出力状態: "
    PLAYBACK = "出力状態: 再生中"
    PROCESSING = "出力状態: 処理中"
    FAILURE = "出力状態: 失敗"
    CANCELED = "出力状態: キャンセル"
    TEXT_LOAD_FAILURE = "出力状態: TEXT読込失敗"
    WAV_LOAD_FAILURE = "出力状態: WAV読込失敗"
    TEXT_CONVERSION_FAILURE = "出力状態: TEXT変換失敗"
    INPUT_MISSING = "出力状態: 入力不足"
    ANALYSIS_NOT_RUN = "出力状態: 解析未実行"
    READY_ANALYSIS_PENDING = "出力状態: 解析待機中 (TEXT/WAV読込済み)"
    READY_TEXT_ONLY = "出力状態: 入力待機中 (TEXT読込済み / WAV未読込)"
    READY_WAV_ONLY = "出力状態: 入力待機中 (WAV読込済み / TEXT未読込)"
    READY_NOT_LOADED = "出力状態: 入力待機中 (TEXT/WAV未読込)"
    READY_ANALYSIS_DONE_PREFIX = "出力状態: 解析実行済み ("
    READY_ANALYSIS_DONE_TEMPLATE = "出力状態: 解析実行済み ({timing_label} / 区間={anchor_count} / 母音={vowel_count})"
    SUCCESS_PREFIX = "出力状態: 成功 ("
    SUCCESS_TEMPLATE = "出力状態: 成功 ({output_name} / {timing_label})"

    READY_PREFIXES = (
        READY_ANALYSIS_PENDING,
        READY_TEXT_ONLY,
        READY_WAV_ONLY,
        READY_NOT_LOADED,
        READY_ANALYSIS_DONE_PREFIX,
    )

    _TRANSLATIONS = {
        "ja": {
            "STATUS_PREFIX": STATUS_PREFIX,
            "PLAYBACK": PLAYBACK,
            "PROCESSING": PROCESSING,
            "FAILURE": FAILURE,
            "CANCELED": CANCELED,
            "TEXT_LOAD_FAILURE": TEXT_LOAD_FAILURE,
            "WAV_LOAD_FAILURE": WAV_LOAD_FAILURE,
            "TEXT_CONVERSION_FAILURE": TEXT_CONVERSION_FAILURE,
            "INPUT_MISSING": INPUT_MISSING,
            "ANALYSIS_NOT_RUN": ANALYSIS_NOT_RUN,
            "READY_ANALYSIS_PENDING": READY_ANALYSIS_PENDING,
            "READY_TEXT_ONLY": READY_TEXT_ONLY,
            "READY_WAV_ONLY": READY_WAV_ONLY,
            "READY_NOT_LOADED": READY_NOT_LOADED,
            "READY_ANALYSIS_DONE_PREFIX": READY_ANALYSIS_DONE_PREFIX,
            "READY_ANALYSIS_DONE_TEMPLATE": READY_ANALYSIS_DONE_TEMPLATE,
            "SUCCESS_PREFIX": SUCCESS_PREFIX,
            "SUCCESS_TEMPLATE": SUCCESS_TEMPLATE,
        },
        "en": {
            "STATUS_PREFIX": "Status: ",
            "PLAYBACK": "Status: Playing",
            "PROCESSING": "Status: Processing",
            "FAILURE": "Status: Failed",
            "CANCELED": "Status: Canceled",
            "TEXT_LOAD_FAILURE": "Status: TEXT load failed",
            "WAV_LOAD_FAILURE": "Status: WAV load failed",
            "TEXT_CONVERSION_FAILURE": "Status: TEXT conversion failed",
            "INPUT_MISSING": "Status: Missing input",
            "ANALYSIS_NOT_RUN": "Status: Analysis not run",
            "READY_ANALYSIS_PENDING": "Status: Ready (TEXT/WAV loaded, analysis pending)",
            "READY_TEXT_ONLY": "Status: Waiting for input (TEXT loaded / WAV not loaded)",
            "READY_WAV_ONLY": "Status: Waiting for input (WAV loaded / TEXT not loaded)",
            "READY_NOT_LOADED": "Status: Waiting for input (TEXT/WAV not loaded)",
            "READY_ANALYSIS_DONE_PREFIX": "Status: Analysis complete (",
            "READY_ANALYSIS_DONE_TEMPLATE": "Status: Analysis complete ({timing_label} / anchors={anchor_count} / vowels={vowel_count})",
            "SUCCESS_PREFIX": "Status: Success (",
            "SUCCESS_TEMPLATE": "Status: Success ({output_name} / {timing_label})",
        },
    }

    @classmethod
    def for_language(cls, language: str) -> dict[str, str]:
        return dict(cls._TRANSLATIONS[normalize_language(language)])

    @classmethod
    def ready_prefixes_for_language(cls, language: str) -> tuple[str, ...]:
        strings = cls.for_language(language)
        return (
            strings["READY_ANALYSIS_PENDING"],
            strings["READY_TEXT_ONLY"],
            strings["READY_WAV_ONLY"],
            strings["READY_NOT_LOADED"],
            strings["READY_ANALYSIS_DONE_PREFIX"],
        )
