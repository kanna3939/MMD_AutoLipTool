from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional
import shutil
import sys

class FfmpegToolSource(str, Enum):
    REPO_LOCAL = "repo_local"
    BUNDLED = "bundled"
    PATH = "path"
    NOT_FOUND = "not_found"

@dataclass(frozen=True)
class FfmpegToolPath:
    path: Optional[Path]
    source: FfmpegToolSource

@dataclass(frozen=True)
class FfmpegLocatorResult:
    ffmpeg: FfmpegToolPath
    ffprobe: FfmpegToolPath

    @property
    def is_complete(self) -> bool:
        return self.ffmpeg.path is not None and self.ffprobe.path is not None

_SOURCE_DESCRIPTIONS = {
    FfmpegToolSource.REPO_LOCAL: "アプリ内 FFmpeg フォルダから検出",
    FfmpegToolSource.BUNDLED: "同梱 FFmpeg から検出",
    FfmpegToolSource.PATH: "PATH から検出",
    FfmpegToolSource.NOT_FOUND: "未検出",
}

SEARCH_LOCATIONS_DESCRIPTION = "確認対象: アプリ内 FFmpeg フォルダ、同梱 FFmpeg、PATH"


def format_tool_status(tool_name: str, tool_path: FfmpegToolPath) -> str:
    """Format a tool lookup result without exposing local filesystem paths."""
    return f"{tool_name}: {_SOURCE_DESCRIPTIONS[tool_path.source]}"


def format_locator_status(result: FfmpegLocatorResult) -> str:
    """Format ffmpeg/ffprobe lookup results for user-facing diagnostics."""
    return "\n".join(
        [
            format_tool_status("ffmpeg.exe", result.ffmpeg),
            format_tool_status("ffprobe.exe", result.ffprobe),
            SEARCH_LOCATIONS_DESCRIPTION,
        ]
    )


def _find_tool(tool_name: str, project_root: Path | None, meipass_root: Path | None, path_env: str | None) -> FfmpegToolPath:
    exe_name = f"{tool_name}.exe"
    
    # 1. Repo Local
    if project_root is not None:
        repo_path = project_root / "FFmpeg" / "bin" / exe_name
        if repo_path.is_file():
            return FfmpegToolPath(path=repo_path.resolve(), source=FfmpegToolSource.REPO_LOCAL)
            
    # 2. Bundled (PyInstaller onefile)
    if meipass_root is not None:
        bundled_path = meipass_root / "FFmpeg" / exe_name
        if bundled_path.is_file():
            return FfmpegToolPath(path=bundled_path.resolve(), source=FfmpegToolSource.BUNDLED)
            
    # 3. PATH fallback
    path_kwargs = {}
    if path_env is not None:
        path_kwargs["path"] = path_env
        
    found_in_path = shutil.which(exe_name, **path_kwargs)
    if found_in_path:
        return FfmpegToolPath(path=Path(found_in_path).resolve(), source=FfmpegToolSource.PATH)
        
    return FfmpegToolPath(path=None, source=FfmpegToolSource.NOT_FOUND)

def locate_ffmpeg_tools(
    project_root: Path | None = None,
    meipass_root: Path | None = None,
    path_env: str | None = None,
) -> FfmpegLocatorResult:
    """
    Find ffmpeg and ffprobe executables.
    Exploration order:
    1. repo_local: project_root / FFmpeg / bin / tool.exe
    2. bundled: meipass_root / FFmpeg / tool.exe
    3. path: PATH environment variable
    """
    # Default resolving if not provided
    if project_root is None:
        # Assuming src/core/ffmpeg_locator.py, root is 2 levels up
        project_root = Path(__file__).resolve().parent.parent.parent
        
    if meipass_root is None and hasattr(sys, "_MEIPASS"):
        meipass_root = Path(sys._MEIPASS) # type: ignore
        
    ffmpeg_path = _find_tool("ffmpeg", project_root, meipass_root, path_env)
    ffprobe_path = _find_tool("ffprobe", project_root, meipass_root, path_env)
    
    return FfmpegLocatorResult(ffmpeg=ffmpeg_path, ffprobe=ffprobe_path)
