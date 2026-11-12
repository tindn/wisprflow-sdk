"""Auto-applies the macOS adapter for wisprflow-sdk.

Python imports this module automatically when the repo root is on sys.path,
e.g.:

    uv run python try_transcribe.py audio.wav
    PYTHONPATH=. uv run wisprflow audio.wav
"""

import macos_shim  # noqa: F401
