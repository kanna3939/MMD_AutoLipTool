import unittest
from pathlib import Path
import tempfile
import os

from src.core.audio_cache import (
    _get_safe_stem,
    _generate_hash8,
    get_analysis_wav_dir,
    generate_analysis_wav_path,
    ensure_cache_dir_exists,
    cleanup_partial_file
)

class TestAudioCache(unittest.TestCase):
    def test_safe_stem(self):
        self.assertEqual(_get_safe_stem("normal_name"), "normal_name")
        self.assertEqual(_get_safe_stem("name with spaces"), "name_with_spaces")
        self.assertEqual(_get_safe_stem("test_file.mp3"), "test_file_mp3")
        self.assertEqual(_get_safe_stem("very" * 20), ("very" * 20)[:50])

    def test_generate_hash8(self):
        path1 = Path("C:/path/to/file1.mp3")
        path2 = Path("C:/path/to/file1.mp3")
        path3 = Path("C:/path/to/file2.mp3")
        
        h1 = _generate_hash8(path1, 1000)
        h2 = _generate_hash8(path2, 1000)
        h3 = _generate_hash8(path2, 1001)
        h4 = _generate_hash8(path3, 1000)
        
        self.assertEqual(len(h1), 8)
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h3)
        self.assertNotEqual(h1, h4)

    def test_generate_analysis_wav_path(self):
        source = Path("C:/my_audio.mp3")
        cache_dir = Path("cache_dir")
        
        result = generate_analysis_wav_path(source, 1024, cache_dir)
        self.assertEqual(result.parent, cache_dir)
        self.assertTrue(result.name.startswith("my_audio_"))
        self.assertTrue(result.name.endswith("_analysis.wav"))
        
    def test_ensure_cache_dir_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "test_cache"
            self.assertFalse(cache_dir.exists())
            
            ensure_cache_dir_exists(cache_dir)
            self.assertTrue(cache_dir.exists())
            self.assertTrue(cache_dir.is_dir())

    def test_cleanup_partial_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "partial.wav"
            file_path.touch()
            self.assertTrue(file_path.exists())
            
            cleanup_partial_file(file_path)
            self.assertFalse(file_path.exists())
            
            # Calling on non-existent file should not raise an error
            cleanup_partial_file(file_path)

if __name__ == '__main__':
    unittest.main()
