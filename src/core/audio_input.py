from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class AudioInputKind(str, Enum):
    WAV = "wav"
    MP3 = "mp3"
    M4A = "m4a"

@dataclass(frozen=True)
class AudioInputInfo:
    source_path: Path
    kind: AudioInputKind
    suffix: str

def detect_audio_input_kind(path: str | Path) -> AudioInputKind:
    """
    Detect the AudioInputKind from the file extension.
    Accepts .wav, .mp3, .m4a (case-insensitive).
    Raises ValueError for unsupported extensions or empty paths.
    """
    path_obj = Path(path)
    if not str(path_obj).strip():
        raise ValueError("Audio file path cannot be empty.")
        
    suffix = path_obj.suffix.lower()
    
    if suffix == ".wav":
        return AudioInputKind.WAV
    elif suffix == ".mp3":
        return AudioInputKind.MP3
    elif suffix == ".m4a":
        return AudioInputKind.M4A
    else:
        raise ValueError(f"Unsupported audio file extension: '{suffix}'. Supported extensions are .wav, .mp3, .m4a.")

def build_audio_input_info(path: str | Path) -> AudioInputInfo:
    """
    Build AudioInputInfo from the given path.
    Raises ValueError if the extension is unsupported.
    """
    path_obj = Path(path)
    kind = detect_audio_input_kind(path_obj)
    
    return AudioInputInfo(
        source_path=path_obj,
        kind=kind,
        suffix=path_obj.suffix.lower()
    )
