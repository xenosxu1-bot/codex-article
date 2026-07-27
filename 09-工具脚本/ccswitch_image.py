from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "http://127.0.0.1:15721/v1"
DEFAULT_RESPONSE_MODEL = "gpt-5.6-terra"
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def load_env() -> None:
    for env_file in (REPO / ".env", REPO.parent.parent / ".env"):
        if not env_file.exists():
            continue
        for raw in env_file.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().lstrip("\ufeff")
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def cc_switch_image_config() -> tuple[str, str]:
    """Return an explicitly local CC Switch route for the Responses image tool."""
    load_env()
    base_url = os.environ.get("CC_SWITCH_IMAGE_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in LOCAL_HOSTS:
        raise RuntimeError(
            "Refusing a non-local image route. Set CC_SWITCH_IMAGE_BASE_URL to the local CC Switch proxy, for example http://127.0.0.1:15721/v1."
        )
    api_key = os.environ.get("CC_SWITCH_IMAGE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key or "put-your-key" in api_key.lower():
        raise RuntimeError("CC Switch image proxy authentication is missing. Set CC_SWITCH_IMAGE_API_KEY or OPENAI_API_KEY in the local .env file.")
    return base_url, api_key


def redact(text: str) -> str:
    return text.replace("Bearer ", "Bearer ***")[:800]


def extract_image_result(body: dict[str, object]) -> str:
    for item in body.get("output", []):
        if isinstance(item, dict) and item.get("type") == "image_generation_call" and item.get("result"):
            return str(item["result"])
    raise RuntimeError("CC Switch Responses API returned no image_generation_call result.")


def generate_image(prompt: str, output: Path, *, size: str = "1536x1024", quality: str = "high") -> dict[str, str]:
    base_url, api_key = cc_switch_image_config()
    # The local CC Switch proxy exposes the Responses API, not /images/generations.
    # In the Responses API, image_generation is a built-in tool: the mainline
    # response model calls it, while the tool/provider manages GPT Image model
    # selection.  Do not claim an exact image backend unless CC Switch exposes
    # that sub-request in its audit log.
    response_model = os.environ.get("CC_SWITCH_RESPONSE_MODEL", DEFAULT_RESPONSE_MODEL)
    endpoint = f"{base_url}/responses"
    payload: dict[str, object] = {
        "model": response_model,
        "input": prompt,
        "tools": [{"type": "image_generation", "size": size, "quality": quality, "output_format": "png"}],
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"CC Switch Responses image request failed with HTTP {exc.code}: {redact(detail)}") from exc

    encoded = extract_image_result(body)
    if encoded.startswith("data:image/") and "," in encoded:
        encoded = encoded.split(",", 1)[1]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(base64.b64decode(encoded))
    return {
        "route": f"CC Switch local proxy {base_url}",
        "endpoint": endpoint,
        "response_model": response_model,
        "image_tool": "image_generation",
        "image_model_selection": "managed by CC Switch Responses tool; exact backend not exposed by current proxy log",
        "quality": quality,
    }
