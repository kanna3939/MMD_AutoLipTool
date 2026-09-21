from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from src.core.whisper_model_loader import (
    LoadedWhisperModel,
    VerifiedWhisperCheckpoint,
    WhisperModelLoaderError,
    _load_model_from_bytes,
    load_verified_local_checkpoint,
)
from src.core.whisper_models import (
    WhisperModelCatalog,
    WhisperModelSpec,
    build_manifest_identity,
)


class _FakeWhisper:
    __version__ = "20250625"
    _ALIGNMENT_HEADS = {"small": b"alignment-heads"}
    ModelDimensions = object
    Whisper = object

    @staticmethod
    def load_model(*args, **kwargs):
        raise AssertionError("official whisper.load_model() must not be called")


class _FakeCuda:
    @staticmethod
    def is_available() -> bool:
        return False


class _FakeTorch:
    cuda = _FakeCuda()


class _LoaderFixture:
    content = b"verified fake Whisper checkpoint"

    @classmethod
    def create(cls, temporary_directory: Path) -> tuple[WhisperModelCatalog, Path, VerifiedWhisperCheckpoint]:
        sha256 = hashlib.sha256(cls.content).hexdigest()
        model_path = temporary_directory / "small.pt"
        model_path.write_bytes(cls.content)
        spec = WhisperModelSpec(
            model_key="small",
            display_name="Whisper small",
            multilingual=True,
            japanese_supported=True,
            official_url=(
                "https://openaipublic.azureedge.net/main/whisper/models/"
                f"{sha256}/small.pt"
            ),
            filename="small.pt",
            sha256=sha256,
            size_bytes=len(cls.content),
            vram_hint="test",
            speed_hint="test",
            recommended_use="test",
        )
        catalog = WhisperModelCatalog(
            schema_version=1,
            openai_whisper_version="20250625",
            default_model_key="small",
            models=(spec,),
        )
        checkpoint = VerifiedWhisperCheckpoint(
            model_key="small",
            checkpoint_path=model_path,
            manifest_identity=build_manifest_identity("20250625", "small", sha256),
            sha256=sha256,
            size_bytes=len(cls.content),
        )
        return catalog, model_path, checkpoint


class WhisperModelLoaderTests(unittest.TestCase):
    def test_success_loads_only_verified_bytes_and_preserves_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            catalog, _, checkpoint = _LoaderFixture.create(Path(temporary_directory))
            loaded_model = object()
            with (
                patch("src.core.whisper_model_loader._import_whisper", return_value=_FakeWhisper),
                patch("src.core.whisper_model_loader._import_torch", return_value=_FakeTorch),
                patch(
                    "src.core.whisper_model_loader._load_model_from_bytes",
                    return_value=loaded_model,
                ) as bytes_loader,
            ):
                result = load_verified_local_checkpoint(checkpoint, catalog=catalog)

        self.assertIsInstance(result, LoadedWhisperModel)
        self.assertIs(result.model, loaded_model)
        self.assertEqual(result.model_key, "small")
        self.assertEqual(result.manifest_identity, checkpoint.manifest_identity)
        bytes_loader.assert_called_once()
        self.assertEqual(bytes_loader.call_args.kwargs["checkpoint_bytes"], _LoaderFixture.content)
        self.assertEqual(bytes_loader.call_args.kwargs["alignment_heads"], b"alignment-heads")

    def test_loader_does_not_call_official_model_key_loader(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            catalog, _, checkpoint = _LoaderFixture.create(Path(temporary_directory))
            with (
                patch("src.core.whisper_model_loader._import_whisper", return_value=_FakeWhisper),
                patch("src.core.whisper_model_loader._import_torch", return_value=_FakeTorch),
                patch(
                    "src.core.whisper_model_loader._load_model_from_bytes",
                    return_value=object(),
                ),
            ):
                load_verified_local_checkpoint(checkpoint, catalog=catalog)

    def test_checkpoint_metadata_mismatch_fails_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            catalog, _, checkpoint = _LoaderFixture.create(Path(temporary_directory))
            invalid_checkpoint = VerifiedWhisperCheckpoint(
                model_key=checkpoint.model_key,
                checkpoint_path=checkpoint.checkpoint_path,
                manifest_identity=checkpoint.manifest_identity,
                sha256="0" * 64,
                size_bytes=checkpoint.size_bytes,
            )
            with (
                patch("src.core.whisper_model_loader._import_whisper") as import_whisper,
                patch("src.core.whisper_model_loader._load_model_from_bytes") as bytes_loader,
                self.assertRaises(WhisperModelLoaderError) as raised,
            ):
                load_verified_local_checkpoint(invalid_checkpoint, catalog=catalog)

        self.assertEqual(raised.exception.code, "checkpoint_not_verified")
        import_whisper.assert_not_called()
        bytes_loader.assert_not_called()

    def test_missing_directory_and_partial_paths_fail_closed_without_bytes_loader(self) -> None:
        cases = ("missing", "directory", "partial")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary_directory:
                catalog, model_path, checkpoint = _LoaderFixture.create(Path(temporary_directory))
                if case == "missing":
                    model_path.unlink()
                elif case == "directory":
                    model_path.unlink()
                    model_path.mkdir()
                else:
                    partial_path = model_path.with_name("small.pt.part")
                    model_path.rename(partial_path)
                    checkpoint = VerifiedWhisperCheckpoint(
                        model_key=checkpoint.model_key,
                        checkpoint_path=partial_path,
                        manifest_identity=checkpoint.manifest_identity,
                        sha256=checkpoint.sha256,
                        size_bytes=checkpoint.size_bytes,
                    )
                with (
                    patch("src.core.whisper_model_loader._import_whisper", return_value=_FakeWhisper),
                    patch("src.core.whisper_model_loader._import_torch", return_value=_FakeTorch),
                    patch("src.core.whisper_model_loader._load_model_from_bytes") as bytes_loader,
                    self.assertRaises(WhisperModelLoaderError) as raised,
                ):
                    load_verified_local_checkpoint(checkpoint, catalog=catalog)
                self.assertEqual(raised.exception.code, "checkpoint_path_invalid")
                bytes_loader.assert_not_called()

    def test_same_size_replacement_fails_integrity_without_loading_replaced_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            catalog, model_path, checkpoint = _LoaderFixture.create(Path(temporary_directory))
            model_path.write_bytes(b"replaced checkpoint bytes, same length"[: len(_LoaderFixture.content)])
            with (
                patch("src.core.whisper_model_loader._import_whisper", return_value=_FakeWhisper),
                patch("src.core.whisper_model_loader._import_torch", return_value=_FakeTorch),
                patch("src.core.whisper_model_loader._load_model_from_bytes") as bytes_loader,
                self.assertRaises(WhisperModelLoaderError) as raised,
            ):
                load_verified_local_checkpoint(checkpoint, catalog=catalog)

        self.assertEqual(raised.exception.code, "checkpoint_integrity_mismatch")
        bytes_loader.assert_not_called()

    def test_streaming_read_failure_is_stable_and_does_not_load_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            catalog, _, checkpoint = _LoaderFixture.create(Path(temporary_directory))
            with (
                patch("src.core.whisper_model_loader._import_whisper", return_value=_FakeWhisper),
                patch("src.core.whisper_model_loader._import_torch", return_value=_FakeTorch),
                patch.object(Path, "open", side_effect=PermissionError("denied")),
                patch("src.core.whisper_model_loader._load_model_from_bytes") as bytes_loader,
                self.assertRaises(WhisperModelLoaderError) as raised,
            ):
                load_verified_local_checkpoint(checkpoint, catalog=catalog)

        self.assertEqual(raised.exception.code, "checkpoint_read_failed")
        bytes_loader.assert_not_called()

    def test_version_and_alignment_api_gates_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            catalog, _, checkpoint = _LoaderFixture.create(Path(temporary_directory))
            wrong_version = type("WrongVersionWhisper", (), dict(_FakeWhisper.__dict__))
            wrong_version.__version__ = "20240930"
            with (
                patch("src.core.whisper_model_loader._import_whisper", return_value=wrong_version),
                self.assertRaises(WhisperModelLoaderError) as raised,
            ):
                load_verified_local_checkpoint(checkpoint, catalog=catalog)
            self.assertEqual(raised.exception.code, "whisper_version_mismatch")

            missing_key = type("MissingAlignmentHeadWhisper", (), dict(_FakeWhisper.__dict__))
            missing_key._ALIGNMENT_HEADS = {}
            with (
                patch("src.core.whisper_model_loader._import_whisper", return_value=missing_key),
                self.assertRaises(WhisperModelLoaderError) as raised,
            ):
                load_verified_local_checkpoint(checkpoint, catalog=catalog)
            self.assertEqual(raised.exception.code, "alignment_heads_key_missing")

    def test_bytes_loader_applies_alignment_heads_and_uses_weights_only(self) -> None:
        captured: dict[str, object] = {}

        class FakeDimensions:
            def __init__(self, **values: object) -> None:
                captured["dimensions"] = values

        class FakeModel:
            def __init__(self, dimensions: object) -> None:
                captured["dimensions_object"] = dimensions

            def load_state_dict(self, state_dict: object) -> None:
                captured["state_dict"] = state_dict

            def set_alignment_heads(self, alignment_heads: bytes) -> None:
                captured["alignment_heads"] = alignment_heads

            def to(self, device: object) -> FakeModel:
                captured["device"] = device
                return self

        class FakeWhisperModule:
            ModelDimensions = FakeDimensions
            Whisper = FakeModel

        class FakeTorchModule:
            @staticmethod
            def load(file_object: object, *, map_location: object, weights_only: bool) -> dict[str, object]:
                captured["bytes"] = file_object.read()
                captured["map_location"] = map_location
                captured["weights_only"] = weights_only
                return {"dims": {"n_mels": 80}, "model_state_dict": {"weight": 1}}

        result = _load_model_from_bytes(
            whisper_module=FakeWhisperModule,
            torch_module=FakeTorchModule,
            checkpoint_bytes=b"verified-bytes",
            alignment_heads=b"alignment-heads",
            device="cpu",
        )

        self.assertIsInstance(result, FakeModel)
        self.assertEqual(captured["bytes"], b"verified-bytes")
        self.assertEqual(captured["weights_only"], True)
        self.assertEqual(captured["map_location"], "cpu")
        self.assertEqual(captured["alignment_heads"], b"alignment-heads")

    def test_alignment_head_application_failure_is_stable(self) -> None:
        class FakeDimensions:
            def __init__(self, **values: object) -> None:
                pass

        class FakeModel:
            def __init__(self, dimensions: object) -> None:
                pass

            def load_state_dict(self, state_dict: object) -> None:
                pass

            def set_alignment_heads(self, alignment_heads: bytes) -> None:
                raise ValueError("alignment head rejected")

        class FakeWhisperModule:
            ModelDimensions = FakeDimensions
            Whisper = FakeModel

        class FakeTorchModule:
            @staticmethod
            def load(file_object: object, *, map_location: object, weights_only: bool) -> dict[str, object]:
                return {"dims": {}, "model_state_dict": {}}

        with self.assertRaises(WhisperModelLoaderError) as raised:
            _load_model_from_bytes(
                whisper_module=FakeWhisperModule,
                torch_module=FakeTorchModule,
                checkpoint_bytes=b"verified-bytes",
                alignment_heads=b"alignment-heads",
                device="cpu",
            )

        self.assertEqual(raised.exception.code, "alignment_heads_apply_failed")


if __name__ == "__main__":
    unittest.main()
