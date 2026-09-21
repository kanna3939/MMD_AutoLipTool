import subprocess
import sys


def test_b2_import_orders_and_mixed_namespace_are_fresh_process_safe() -> None:
    commands = (
        "import src.core.morph_name_sets; import src.vmd_writer; import src.vmd_writer.effective_shape_adapter",
        "import src.vmd_writer; import src.core.morph_name_sets; import src.vmd_writer.effective_shape_adapter",
        "import src.vmd_writer.effective_shape_adapter; import src.vmd_writer; import src.core.morph_name_sets",
        (
            "from types import SimpleNamespace; "
            "import vmd_writer.writer as top_writer; "
            "import src.vmd_writer.writer as src_writer; "
            "import vmd_writer.effective_shape_adapter as adapter; "
            "assert top_writer.VowelTimelinePoint is not src_writer.VowelTimelinePoint; "
            "plan=SimpleNamespace(shapes=(SimpleNamespace(vowel='あ', control_points=(SimpleNamespace(frame_no=1, value=0.2),)),)); "
            "assert adapter.build_morph_frames_from_effective_shape_plan(plan, False, output_morph_names=('A','I','U','E','O')) == ((1, 'A', 0.2),)"
        ),
    )
    for command in commands:
        result = subprocess.run(
            [sys.executable, "-c", command],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
