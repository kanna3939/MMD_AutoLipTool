from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs


# Whisper uses the ordinary torch import graph. The contrib hook collects
# every torch submodule, including tests and optional integrations, which is
# not required by this wxPython application.
module_collection_mode = "pyz+py"

datas = collect_data_files(
    "torch",
    excludes=[
        "**/*.h",
        "**/*.hpp",
        "**/*.cuh",
        "**/*.lib",
        "**/*.cpp",
        "**/*.pyi",
        "**/*.cmake",
    ],
)
binaries = collect_dynamic_libs("torch")
hiddenimports = []
