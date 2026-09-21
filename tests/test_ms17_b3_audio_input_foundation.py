import unittest
from pathlib import Path
from src.core.audio_input import (
    AudioInputKind,
    detect_audio_input_kind,
    build_audio_input_info,
)

class TestAudioInputFoundation(unittest.TestCase):
    
    def test_detect_wav(self):
        self.assertEqual(detect_audio_input_kind("test.wav"), AudioInputKind.WAV)
        self.assertEqual(detect_audio_input_kind("TEST.WAV"), AudioInputKind.WAV)
        self.assertEqual(detect_audio_input_kind(Path("dir/test.wAv")), AudioInputKind.WAV)

    def test_detect_mp3(self):
        self.assertEqual(detect_audio_input_kind("test.mp3"), AudioInputKind.MP3)
        self.assertEqual(detect_audio_input_kind("TEST.MP3"), AudioInputKind.MP3)
        self.assertEqual(detect_audio_input_kind(Path("dir/test.mP3")), AudioInputKind.MP3)

    def test_detect_m4a(self):
        self.assertEqual(detect_audio_input_kind("test.m4a"), AudioInputKind.M4A)
        self.assertEqual(detect_audio_input_kind("TEST.M4A"), AudioInputKind.M4A)
        self.assertEqual(detect_audio_input_kind(Path("dir/test.M4a")), AudioInputKind.M4A)

    def test_detect_unsupported(self):
        with self.assertRaises(ValueError):
            detect_audio_input_kind("test.ogg")
            
        with self.assertRaises(ValueError):
            detect_audio_input_kind("test.flac")
            
        with self.assertRaises(ValueError):
            detect_audio_input_kind("test") # No extension

    def test_empty_path(self):
        with self.assertRaises(ValueError):
            detect_audio_input_kind("")
            
        with self.assertRaises(ValueError):
            detect_audio_input_kind("   ")

    def test_build_audio_input_info(self):
        path_str = "some/dir/MyAudio.Mp3"
        info = build_audio_input_info(path_str)
        
        self.assertEqual(info.source_path, Path(path_str))
        self.assertEqual(info.kind, AudioInputKind.MP3)
        self.assertEqual(info.suffix, ".mp3")
        
        # Verify it doesn't contain fields for analysis/MMD WAVs
        self.assertFalse(hasattr(info, "analysis_wav_path"))
        self.assertFalse(hasattr(info, "mmd_wav_path"))

if __name__ == '__main__':
    unittest.main()
