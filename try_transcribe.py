"""Minimal end-to-end transcription attempt with the macOS shim."""

import sys
import traceback

import macos_shim  # noqa: F401  (must be imported first)
from wisprflow_sdk import WisprClient

AUDIO = sys.argv[1] if len(sys.argv) > 1 else "/tmp/wispr_test.wav"

client = WisprClient()
print("auth:", client.auth_status())

try:
    result = client.transcribe(AUDIO, languages=["en"])
    print("\n--- raw ---")
    print(result.raw)
    print("--- formatted ---")
    print(result.formatted)
    print("--- final ---")
    print(result.final)
    print("\nstatus:", result.result_status, "warmup:", result.warmup)
except Exception:
    print("\nTRANSCRIBE FAILED")
    traceback.print_exc()
