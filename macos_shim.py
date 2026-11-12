"""
macos_shim.py — local, non-invasive adapter for wisprflow-sdk on macOS.

The published SDK (0.1.3) is Windows-only:
  * it reads session.json from %APPDATA%\\Wispr Flow\\
  * it reads wispr_runtime.json from %LOCALAPPDATA%\\WisprFlow\\
  * it always sends Baseten headers (Api-Key + model-id)

The current macOS Wispr Flow app (1.6.x):
  * stores session.json in ~/Library/Application Support/Wispr Flow/
  * authenticates with WorkOS (session.json -> workosSession.accessToken),
    not the old Supabase key
  * streams to a Modal-hosted gRPC endpoint and sends only
    "authorization: Bearer <token>" (no Baseten key/model-id)

Usage:
    import macos_shim  # noqa: F401  (must be imported before using WisprClient)
    from wisprflow_sdk import WisprClient
"""

import json
import os
from pathlib import Path

from wisprflow_sdk import _core

SUPABASE_KEY = "sb-dodjkfqhwrzqjwkfnthl-auth-token"

SESSION_PATH = Path.home() / "Library/Application Support/Wispr Flow/session.json"
CONFIG_PATH = Path.home() / "Library/Application Support/Wispr Flow/config.json"
RUNTIME_PATH = Path.home() / "Library/Application Support/WisprFlow/wispr_runtime.json"

# Endpoint the installed desktop client uses for dictation (non-candidate path).
DEFAULT_HOST = "wispr-ai-prod--prod-grpc-server-flowgrpcserver.us-east.modal.direct"


def _get_token() -> str:
    with open(SESSION_PATH) as f:
        session = json.load(f)

    legacy = session.get(SUPABASE_KEY)
    if legacy:  # older app builds
        return json.loads(legacy)["access_token"]

    workos = session.get("workosSession") or {}
    token = workos.get("accessToken")
    if not token:
        raise RuntimeError(f"No access token found in {SESSION_PATH}")
    return token


def _token_user_id(token: str) -> str:
    """WorkOS tokens carry a non-UUID `sub`, but the backend validates user_id
    as a UUID, so use the account UUID the desktop app stores with the session."""
    with open(SESSION_PATH) as f:
        session = json.load(f)
    user_id = (session.get("workosSession") or {}).get("userId")
    if user_id:
        return user_id
    with open(CONFIG_PATH) as f:
        return json.load(f)["prefs"]["user"]["uuid"]


def _runtime_config() -> dict:
    cfg = {}
    if RUNTIME_PATH.exists():
        with open(RUNTIME_PATH) as f:
            cfg = json.load(f)

    api_key = cfg.get("basteKey") or cfg.get("apiKey", "")
    model_id = cfg.get("modelId") or _core.DEFAULT_MODEL_ID
    host = os.environ.get("WISPRFLOW_GRPC_HOST") or cfg.get("url") or DEFAULT_HOST
    return {
        "host": host,
        "model": f"model-{model_id}",
        "env": cfg.get("environment") or "production",
        # Empty string => Baseten headers are omitted (current backend doesn't use them)
        "api_key": f"Api-Key {api_key}" if api_key else "",
    }


def _grpc_meta(token: str, rcfg: dict) -> list:
    meta = [("authorization", f"Bearer {token}")]
    if rcfg.get("api_key"):
        meta += [
            ("baseten-authorization", rcfg["api_key"]),
            ("baseten-model-id", rcfg["model"]),
            ("x-baseten-environment", rcfg["env"]),
        ]
    meta += [
        ("flow-debug", "false"),
        ("disable-formatting", "false"),
        ("content-type", "application/grpc"),
        ("user-agent", "grpc-python/1.59.0"),
        ("te", "trailers"),
    ]
    return meta


_core._get_token = _get_token
_core._token_user_id = _token_user_id
_core._runtime_config = _runtime_config
_core._grpc_meta = _grpc_meta
