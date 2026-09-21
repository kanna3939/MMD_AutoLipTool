from __future__ import annotations

import hashlib
import threading
import tempfile
import unittest
from pathlib import Path

from src.core.whisper_model_downloader import (
    DOWNLOAD_PHASE_DOWNLOADING,
    DOWNLOAD_PHASE_VERIFYING,
    DOWNLOAD_STATUS_CANCELLED,
    DOWNLOAD_STATUS_FAILED,
    DOWNLOAD_STATUS_SUCCEEDED,
    download_model,
)
from src.core.whisper_model_store import WhisperModelStore
from src.core.whisper_models import WhisperModelCatalog, WhisperModelSpec


class _Response:
    def __init__(self, body: bytes, *, status: int = 200, headers=None) -> None:
        self._body = body
        self._offset = 0
        self.status = status
        self.headers = headers if headers is not None else {"Content-Length": str(len(body))}
        self.closed = False

    def read(self, amount: int) -> bytes:
        chunk = self._body[self._offset : self._offset + amount]
        self._offset += len(chunk)
        return chunk

    def close(self) -> None:
        self.closed = True


class _StoreFixture:
    content = b"verified fake Whisper model bytes"

    @classmethod
    def catalog(cls, *, official_url: str | None = None) -> WhisperModelCatalog:
        digest = hashlib.sha256(cls.content).hexdigest()
        spec = WhisperModelSpec(
            model_key="small",
            display_name="Whisper small",
            multilingual=True,
            japanese_supported=True,
            official_url=official_url or (
                "https://openaipublic.azureedge.net/main/whisper/models/"
                f"{digest}/small.pt"
            ),
            filename="small.pt",
            sha256=digest,
            size_bytes=len(cls.content),
            vram_hint="test",
            speed_hint="test",
            recommended_use="test",
        )
        return WhisperModelCatalog(
            schema_version=1,
            openai_whisper_version="20250625",
            default_model_key="small",
            models=(spec,),
        )


class WhisperModelDownloaderTests(unittest.TestCase):
    def _download(self, response: _Response, *, catalog=None, cancel_event=None):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            catalog = catalog or _StoreFixture.catalog()
            store = WhisperModelStore(root, catalog=catalog)
            preflight = store.preflight_download("small")
            progress = []
            result = download_model(
                "small",
                catalog=catalog,
                store=store,
                preflight=preflight,
                cancel_event=cancel_event,
                progress_callback=progress.append,
                transport=lambda url, timeout: response,
            )
            return (
                result,
                (store.storage_root / "small.pt").is_file(),
                (store.storage_root / "small.pt.part").exists(),
                progress,
            )

    def test_exact_content_length_promotes_only_after_b2_verification(self) -> None:
        result, final_exists, part_exists, progress = self._download(
            _Response(_StoreFixture.content)
        )

        self.assertEqual(result.status, DOWNLOAD_STATUS_SUCCEEDED)
        self.assertIsNotNone(result.checkpoint)
        self.assertTrue(final_exists)
        self.assertFalse(part_exists)
        self.assertEqual(progress[0].phase, DOWNLOAD_PHASE_DOWNLOADING)
        self.assertEqual(progress[-1].phase, DOWNLOAD_PHASE_VERIFYING)
        self.assertEqual(progress[-1].received_bytes, len(_StoreFixture.content))

    def test_missing_or_mismatched_content_length_fails_and_cleans_staging(self) -> None:
        for headers, expected_code in (
            ({}, "download_content_length_invalid"),
            ({"Content-Length": "1"}, "download_content_length_mismatch"),
        ):
            with self.subTest(expected_code=expected_code):
                result, final_exists, part_exists, _ = self._download(
                    _Response(_StoreFixture.content, headers=headers)
                )
                self.assertEqual(result.status, DOWNLOAD_STATUS_FAILED)
                self.assertEqual(result.failure_code, expected_code)
                self.assertFalse(part_exists)
                self.assertFalse(final_exists)

    def test_short_read_and_overrun_fail_closed(self) -> None:
        short_response = _Response(
            _StoreFixture.content[:-1],
            headers={"Content-Length": str(len(_StoreFixture.content))},
        )
        short_result, short_final_exists, short_part_exists, _ = self._download(short_response)
        self.assertEqual(short_result.failure_code, "download_short_read")
        self.assertFalse(short_final_exists)
        self.assertFalse(short_part_exists)

        overrun_response = _Response(
            _StoreFixture.content + b"x",
            headers={"Content-Length": str(len(_StoreFixture.content))},
        )
        overrun_result, overrun_final_exists, overrun_part_exists, _ = self._download(overrun_response)
        self.assertEqual(overrun_result.failure_code, "download_overrun")
        self.assertFalse(overrun_final_exists)
        self.assertFalse(overrun_part_exists)

    def test_cancel_before_request_cleans_canonical_staging(self) -> None:
        cancel_event = threading.Event()
        cancel_event.set()
        result, final_exists, part_exists, _ = self._download(
            _Response(_StoreFixture.content),
            cancel_event=cancel_event,
        )

        self.assertEqual(result.status, DOWNLOAD_STATUS_CANCELLED)
        self.assertFalse(final_exists)
        self.assertFalse(part_exists)

    def test_redirect_and_non_official_manifest_fail_closed(self) -> None:
        redirect_result, redirect_final_exists, redirect_part_exists, _ = self._download(
            _Response(
                b"",
                status=302,
                headers={"Location": "https://example.invalid/other"},
            )
        )
        self.assertEqual(redirect_result.failure_code, "download_redirect_rejected")
        self.assertFalse(redirect_final_exists)
        self.assertFalse(redirect_part_exists)

        invalid_catalog = _StoreFixture.catalog(
            official_url="https://example.invalid/models/small.pt"
        )
        invalid_result, invalid_final_exists, invalid_part_exists, _ = self._download(
            _Response(_StoreFixture.content),
            catalog=invalid_catalog,
        )
        self.assertEqual(invalid_result.failure_code, "manifest_invalid")
        self.assertFalse(invalid_final_exists)
        self.assertFalse(invalid_part_exists)


if __name__ == "__main__":
    unittest.main()
