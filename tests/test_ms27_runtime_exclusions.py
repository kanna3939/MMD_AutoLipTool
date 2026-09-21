"""Exercise runtime imports with the onefile exclusion policy applied."""
import ast
import json
from pathlib import Path
import subprocess
import sys


def test_onefile_exclusions_preserve_runtime_imports(tmp_path):
    spec_path = Path(__file__).resolve().parents[1] / "MMD_AutoLipTool.spec"
    tree = ast.parse(spec_path.read_text(encoding="utf-8"))
    assignments = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "excluded_modules" for target in node.targets)
    ]
    assert len(assignments) == 1
    excluded = ast.literal_eval(assignments[0])
    probe = """
import importlib
import importlib.abc
import json
import sys

excluded = json.loads(sys.argv[1])
class ExclusionFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if any(fullname == name or fullname.startswith(name + '.') for name in excluded):
            raise ModuleNotFoundError('Excluded runtime dependency: ' + fullname)
        return None

sys.meta_path.insert(0, ExclusionFinder())
for name in ('numpy', 'whisper', 'jinja2', 'sympy', 'torch._dynamo'):
    importlib.import_module(name)
    print('Imported ' + name, flush=True)
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", probe, json.dumps(excluded)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
