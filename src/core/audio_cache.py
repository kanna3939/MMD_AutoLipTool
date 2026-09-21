import hashlib
import re
from pathlib import Path

def _get_safe_stem(stem: str) -> str:
    """
    Replace unsafe or problematic characters in filename stem.
    """
    # Replace anything that is not alphanumeric, dash, or underscore with underscore
    safe = re.sub(r'[^a-zA-Z0-9_\-]', '_', stem)
    # Truncate to avoid overly long filenames
    if len(safe) > 50:
        safe = safe[:50]
    return safe

def _generate_hash8(source_path: Path, file_size: int) -> str:
    """
    Generate an 8-character hash based on the source absolute path and file size.
    """
    data_to_hash = f"{source_path.resolve()}_{file_size}".encode('utf-8')
    h = hashlib.sha256(data_to_hash).hexdigest()
    return h[:8]

def get_analysis_wav_dir(project_root: Path | None = None) -> Path:
    """
    Resolve the cache/analysis_wav/ directory.
    If project_root is provided, it uses that as the base.
    Otherwise, it assumes the current working directory.
    """
    base = project_root if project_root else Path.cwd()
    cache_dir = base / "cache" / "analysis_wav"
    return cache_dir

def generate_analysis_wav_path(source_path: Path, file_size_bytes: int, cache_dir: Path) -> Path:
    """
    Generate the destination path for the analysis WAV file.
    Format: <safe_stem>_<hash8>_analysis.wav
    """
    safe_stem = _get_safe_stem(source_path.stem)
    hash8 = _generate_hash8(source_path, file_size_bytes)
    filename = f"{safe_stem}_{hash8}_analysis.wav"
    return cache_dir / filename

def ensure_cache_dir_exists(cache_dir: Path) -> None:
    """
    Create the cache directory if it doesn't exist.
    Raises OSError (which should be caught and mapped to ANALYSIS_WAV_CACHE_DIR_FAILED).
    """
    cache_dir.mkdir(parents=True, exist_ok=True)

def cleanup_partial_file(filepath: Path) -> None:
    """
    Safely remove an incomplete file if it exists.
    Ignores errors if the file doesn't exist or cannot be removed.
    """
    try:
        if filepath.exists() and filepath.is_file():
            filepath.unlink()
    except Exception:
        pass
