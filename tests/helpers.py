from __future__ import annotations

from contextlib import contextmanager
import math
from pathlib import Path
import shutil
import struct
from tempfile import TemporaryDirectory
from uuid import uuid4
import wave


def write_test_wav(
    path: Path,
    sample_rate: int = 44100,
    lead_sec: float = 0.2,
    speech_sec: float = 0.6,
    trail_sec: float = 0.2,
    amplitude: int = 12000,
) -> None:
    total_sec = lead_sec + speech_sec + trail_sec
    total_frames = int(total_sec * sample_rate)
    lead_frames = int(lead_sec * sample_rate)
    speech_frames = int(speech_sec * sample_rate)
    speech_end = lead_frames + speech_frames

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        frames: list[bytes] = []
        for frame_index in range(total_frames):
            if lead_frames <= frame_index < speech_end:
                t = (frame_index - lead_frames) / sample_rate
                sample = int(amplitude * math.sin(2.0 * math.pi * 220.0 * t))
            else:
                sample = 0
            frames.append(struct.pack("<h", sample))

        wav_file.writeframes(b"".join(frames))


def get_or_create_wx_app(app_class, *args, **kwargs):
    """Return an active wx App and whether this call created it."""
    import wx

    existing = wx.App.Get()
    if existing is not None and getattr(existing, "_test_app_teardown_done", False):
        try:
            wx.App.SetInstance(None)
        except Exception:
            pass
        existing = None
    if existing is not None:
        return existing, False
    return app_class(*args, **kwargs), True


def _safe_process_pending_events(app) -> None:
    try:
        app.ProcessPendingEvents()
    except Exception:
        # Teardown must also tolerate a partially initialized or already
        # destroyed wx application.
        return


def _safe_yield(app) -> None:
    try:
        app.Yield()
    except Exception:
        return


def _safe_destroy_window(window) -> None:
    try:
        if window is not None and not window.IsBeingDeleted():
            window.Destroy()
    except Exception:
        return


def _safe_stop_and_destroy_timer(timer) -> None:
    if timer is None:
        return
    try:
        timer.Stop()
    except Exception:
        pass
    try:
        timer.Destroy()
    except Exception:
        pass


def _redirect_controller_stores(controller, temp_root: Path) -> None:
    """Keep close-time pending saves outside repository runtime user data."""
    from src.core.generation_presets import GenerationPresetStore
    from src.core.model_profiles import ModelProfileStore
    from src.core.settings_store import SettingsStore

    settings_store = SettingsStore(temp_root / "MMD_AutoLipTool.ini")
    preset_store = GenerationPresetStore(
        settings_store=settings_store,
        presets_path=temp_root / "presets.json",
    )
    profile_store = ModelProfileStore(
        settings_store=settings_store,
        profiles_path=temp_root / "profiles.json",
    )
    controller.settings_store = settings_store
    controller.preset_store = preset_store
    controller.profile_store = profile_store


def _cleanup_controller_resources(controller) -> None:
    _safe_stop_and_destroy_timer(getattr(controller, "_coalesced_save_timer", None))

    playback = getattr(controller, "playback_controller", None)
    playback_timer = getattr(playback, "_timer", None)
    playback_active = False
    if playback_timer is not None:
        try:
            playback_active = playback_timer.IsRunning()
        except Exception:
            playback_active = False
    if playback_active or getattr(playback, "_playback_path", None):
        try:
            playback.stop()
        except Exception:
            pass
    _safe_stop_and_destroy_timer(playback_timer)


def destroy_wx_app(app, frame=None, *, owns_app: bool = True) -> None:
    """Close wx test objects in a deterministic, ownership-aware order."""
    if app is None:
        return

    app_teardown_done = bool(getattr(app, "_test_app_teardown_done", False))
    target = frame if frame is not None else getattr(app, "frame", None)
    frame_teardown_ids = getattr(app, "_test_frame_teardown_ids", set())
    frame_teardown_done = target is not None and id(target) in frame_teardown_ids
    controller = getattr(app, "controller", None)
    if controller is None and target is not None:
        controller = getattr(target, "controller", None)

    # request_exit() flushes pending settings.  Redirect all controller stores
    # before draining events or closing the frame so tests never update the
    # repository-root profiles.json, presets.json, or MMD_AutoLipTool.ini.
    if controller is not None and not frame_teardown_done:
        with TemporaryDirectory(prefix="mmd_autoliptool_wx_teardown_") as temp_dir:
            _redirect_controller_stores(controller, Path(temp_dir))
            if target is not None:
                _safe_process_pending_events(app)
                cleanup = getattr(target, "_cleanup_analysis_job", None)
                if cleanup is not None:
                    try:
                        cleanup()
                    except Exception:
                        pass
            controller_view = getattr(controller, "view", None)
            if controller_view is target or (target is None and controller_view is not None):
                try:
                    controller.request_exit()
                except Exception:
                    pass
            elif target is not None:
                _safe_destroy_window(target)
            _cleanup_controller_resources(controller)
    elif not frame_teardown_done and target is not None:
        cleanup = getattr(target, "_cleanup_analysis_job", None)
        if cleanup is not None:
            try:
                cleanup()
            except Exception:
                pass
        _safe_destroy_window(target)

    if target is not None and not frame_teardown_done:
        frame_teardown_ids.add(id(target))
        setattr(app, "_test_frame_teardown_ids", frame_teardown_ids)

    _safe_yield(app)
    _safe_process_pending_events(app)
    if owns_app and not app_teardown_done:
        try:
            app.Destroy()
        except Exception:
            pass
        _safe_process_pending_events(app)
        setattr(app, "_test_app_teardown_done", True)
        try:
            import wx

            wx.App.SetInstance(None)
        except Exception:
            pass


@contextmanager
def workspace_tempdir(prefix: str = "test") -> Path:
    temp_dir = Path("sample") / f"_{prefix}_{uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
