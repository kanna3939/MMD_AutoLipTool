import shutil
import tempfile
import unittest
from pathlib import Path
from src.core.ffmpeg_locator import (
    FfmpegToolPath,
    FfmpegToolSource,
    format_locator_status,
    format_tool_status,
    locate_ffmpeg_tools,
)

class TestFfmpegLocator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root_path = Path(self.temp_dir)
        
        # Setup mock project root
        self.project_root = self.root_path / "project"
        self.project_bin_dir = self.project_root / "FFmpeg" / "bin"
        self.project_bin_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup mock meipass root
        self.meipass_root = self.root_path / "meipass"
        self.meipass_bin_dir = self.meipass_root / "FFmpeg"
        self.meipass_bin_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup mock path dir
        self.path_dir = self.root_path / "path_bin"
        self.path_dir.mkdir(parents=True, exist_ok=True)
        self.path_env = str(self.path_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def _create_file(self, path: Path):
        path.touch()

    def test_repo_local_priority(self):
        # Create in all three locations
        self._create_file(self.project_bin_dir / "ffmpeg.exe")
        self._create_file(self.project_bin_dir / "ffprobe.exe")
        
        self._create_file(self.meipass_bin_dir / "ffmpeg.exe")
        self._create_file(self.meipass_bin_dir / "ffprobe.exe")
        
        self._create_file(self.path_dir / "ffmpeg.exe")
        self._create_file(self.path_dir / "ffprobe.exe")
        
        result = locate_ffmpeg_tools(
            project_root=self.project_root,
            meipass_root=self.meipass_root,
            path_env=self.path_env
        )
        
        self.assertTrue(result.is_complete)
        self.assertEqual(result.ffmpeg.source, FfmpegToolSource.REPO_LOCAL)
        self.assertEqual(result.ffprobe.source, FfmpegToolSource.REPO_LOCAL)
        self.assertEqual(result.ffmpeg.path, (self.project_bin_dir / "ffmpeg.exe").resolve())

    def test_bundled_priority_over_path(self):
        # Create in bundled and path, but not in repo
        self._create_file(self.meipass_bin_dir / "ffmpeg.exe")
        self._create_file(self.meipass_bin_dir / "ffprobe.exe")
        
        self._create_file(self.path_dir / "ffmpeg.exe")
        self._create_file(self.path_dir / "ffprobe.exe")
        
        result = locate_ffmpeg_tools(
            project_root=self.project_root,
            meipass_root=self.meipass_root,
            path_env=self.path_env
        )
        
        self.assertTrue(result.is_complete)
        self.assertEqual(result.ffmpeg.source, FfmpegToolSource.BUNDLED)
        self.assertEqual(result.ffprobe.source, FfmpegToolSource.BUNDLED)

    def test_path_fallback(self):
        # Create only in path
        self._create_file(self.path_dir / "ffmpeg.exe")
        self._create_file(self.path_dir / "ffprobe.exe")
        
        result = locate_ffmpeg_tools(
            project_root=self.project_root,
            meipass_root=self.meipass_root,
            path_env=self.path_env
        )
        
        self.assertTrue(result.is_complete)
        self.assertEqual(result.ffmpeg.source, FfmpegToolSource.PATH)
        self.assertEqual(result.ffprobe.source, FfmpegToolSource.PATH)

    def test_not_found(self):
        # Create nowhere
        result = locate_ffmpeg_tools(
            project_root=self.project_root,
            meipass_root=self.meipass_root,
            path_env=self.path_env
        )
        
        self.assertFalse(result.is_complete)
        self.assertEqual(result.ffmpeg.source, FfmpegToolSource.NOT_FOUND)
        self.assertIsNone(result.ffmpeg.path)
        self.assertEqual(result.ffprobe.source, FfmpegToolSource.NOT_FOUND)
        self.assertIsNone(result.ffprobe.path)

    def test_partial_found(self):
        # Create ffmpeg in repo, ffprobe in path
        self._create_file(self.project_bin_dir / "ffmpeg.exe")
        self._create_file(self.path_dir / "ffprobe.exe")
        
        result = locate_ffmpeg_tools(
            project_root=self.project_root,
            meipass_root=self.meipass_root,
            path_env=self.path_env
        )
        
        self.assertTrue(result.is_complete)
        self.assertEqual(result.ffmpeg.source, FfmpegToolSource.REPO_LOCAL)
        self.assertEqual(result.ffprobe.source, FfmpegToolSource.PATH)

    def test_partial_missing(self):
        # Create only ffmpeg
        self._create_file(self.project_bin_dir / "ffmpeg.exe")
        
        result = locate_ffmpeg_tools(
            project_root=self.project_root,
            meipass_root=self.meipass_root,
            path_env=self.path_env
        )
        
        self.assertFalse(result.is_complete)
        self.assertEqual(result.ffmpeg.source, FfmpegToolSource.REPO_LOCAL)
        self.assertEqual(result.ffprobe.source, FfmpegToolSource.NOT_FOUND)

    def test_format_tool_status_does_not_expose_path(self):
        tool_path = FfmpegToolPath(
            path=self.project_bin_dir / "ffmpeg.exe",
            source=FfmpegToolSource.REPO_LOCAL,
        )

        message = format_tool_status("ffmpeg.exe", tool_path)

        self.assertIn("ffmpeg.exe", message)
        self.assertIn("アプリ内 FFmpeg フォルダから検出", message)
        self.assertNotIn(str(self.project_bin_dir), message)

    def test_format_locator_status_reports_sources_without_paths(self):
        self._create_file(self.project_bin_dir / "ffmpeg.exe")
        self._create_file(self.path_dir / "ffprobe.exe")

        result = locate_ffmpeg_tools(
            project_root=self.project_root,
            meipass_root=self.meipass_root,
            path_env=self.path_env
        )

        message = format_locator_status(result)

        self.assertIn("ffmpeg.exe: アプリ内 FFmpeg フォルダから検出", message)
        self.assertIn("ffprobe.exe: PATH から検出", message)
        self.assertIn("確認対象: アプリ内 FFmpeg フォルダ、同梱 FFmpeg、PATH", message)
        self.assertNotIn(str(self.project_bin_dir), message)
        self.assertNotIn(str(self.path_dir), message)

if __name__ == '__main__':
    unittest.main()
