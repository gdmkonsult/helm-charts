#!/usr/bin/env python3
"""
n8n inference bootstrap script.

When enabled, this script logs into n8n as the owner user and ensures a shared
OpenAI-compatible credential exists for the GDM inference endpoint.
"""

import json
import os
import time
import urllib.error
import urllib.request
from http.cookiejar import CookieJar

N8N_URL = os.getenv("N8N_URL", "http://localhost:5678")
ADMIN_EMAIL = os.getenv("N8N_DEFAULT_USER_EMAIL", "")
ADMIN_PASSWORD = os.getenv("N8N_DEFAULT_USER_PASSWORD", "")

INFERENS_ENABLED = os.getenv("INFERENS_ENABLED", "false").lower() == "true"
INFERENS_API_KEY = os.getenv("INFERENS_API_KEY", "")
INFERENS_ENDPOINT = os.getenv("INFERENS_ENDPOINT", "https://ai.gdm.se/api/v1")
INFERENS_CREDENTIAL_NAME = os.getenv("INFERENS_CREDENTIAL_NAME", "GDM Inference")
INFERENS_DEFAULT_MODEL = os.getenv("INFERENS_DEFAULT_MODEL", "")


def wait_for_health():
    """Wait for n8n healthz endpoint to return 200."""
    url = f"{N8N_URL}/healthz"
    print(f"INFERENS: Waiting for n8n to be ready at {url}...")

    for attempt in range(1, 121):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    print("INFERENS: n8n is ready!")
                    return True
        except Exception:
            pass
        print(f"INFERENS: Attempt {attempt}/120 - waiting...")
        time.sleep(3)

    print("INFERENS: ERROR - n8n did not become ready in time")
    return False


def _build_opener():
    cj = CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def _request_json(opener, method, path, payload=None, extra_headers=None):
    body = None
    headers = {
        "Accept": "application/json",
    }
    if payload is not None:
        body = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(
        f"{N8N_URL}{path}",
        data=body,
        headers=headers,
        method=method,
    )

    with opener.open(req, timeout=20) as resp:
        raw = resp.read().decode()
        if not raw.strip():
            return {}
        return json.loads(raw)


def login(opener):
    """Authenticate against n8n REST API and keep session cookies."""
    payload = {
        "emailOrLdapLoginId": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
    }
    try:
        _request_json(opener, "POST", "/rest/login", payload)
        print("INFERENS: Logged in successfully")
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        print(f"INFERENS: Login failed ({e.code}): {body}")
        return False
    except Exception as e:
        print(f"INFERENS: Login error: {e}")
        return False


def list_credentials(opener):
    for path in ["/rest/credentials", "/api/v1/credentials"]:
        try:
            response = _request_json(opener, "GET", path)
            if isinstance(response, dict) and "data" in response:
                return response.get("data", [])
            if isinstance(response, list):
                return response
        except Exception:
            continue
    return []


def create_credential(opener, payload):
    last_error = None
    for path in ["/rest/credentials", "/api/v1/credentials"]:
        try:
            return _request_json(opener, "POST", path, payload)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="ignore")
            last_error = f"status={e.code} body={body}"
        except Exception as e:
            last_error = str(e)
    raise RuntimeError(last_error or "unable to create credential")


def update_credential(opener, credential_id, payload):
    last_error = None
    for path in [f"/rest/credentials/{credential_id}", f"/api/v1/credentials/{credential_id}"]:
        try:
            return _request_json(opener, "PATCH", path, payload)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="ignore")
            last_error = f"status={e.code} body={body}"
        except Exception as e:
            last_error = str(e)
    raise RuntimeError(last_error or "unable to update credential")


def ensure_inference_credential(opener):
    credentials = list_credentials(opener)
    existing = next((c for c in credentials if c.get("name") == INFERENS_CREDENTIAL_NAME), None)

    base_payload = {
        "name": INFERENS_CREDENTIAL_NAME,
        "type": "openAiApi",
        "data": {
            "apiKey": INFERENS_API_KEY,
            "url": INFERENS_ENDPOINT,
            "baseUrl": INFERENS_ENDPOINT,
        },
    }

    if INFERENS_DEFAULT_MODEL:
        base_payload["data"]["model"] = INFERENS_DEFAULT_MODEL

    if existing:
        credential_id = existing.get("id")
        print(f"INFERENS: Updating credential '{INFERENS_CREDENTIAL_NAME}' (id={credential_id})")
        result = update_credential(opener, credential_id, base_payload)
        print(f"INFERENS: Updated credential: {json.dumps(result)}")
        return

    print(f"INFERENS: Creating credential '{INFERENS_CREDENTIAL_NAME}'")
    result = create_credential(opener, base_payload)
    print(f"INFERENS: Created credential: {json.dumps(result)}")


def run():
    if not INFERENS_ENABLED:
        print("INFERENS: Disabled, skipping.")
        return

    missing = []
    if not ADMIN_EMAIL:
        missing.append("N8N_DEFAULT_USER_EMAIL")
    if not ADMIN_PASSWORD:
        missing.append("N8N_DEFAULT_USER_PASSWORD")
    if not INFERENS_API_KEY:
        missing.append("INFERENS_API_KEY")

    if missing:
        print(f"INFERENS: Missing required env vars: {', '.join(missing)}")
        return

    if not wait_for_health():
        return

    opener = _build_opener()
    if not login(opener):
        return

    try:
        ensure_inference_credential(opener)
    except Exception as e:
        print(f"INFERENS: Failed to ensure credential: {e}")


if __name__ == "__main__":
    run()
    print("INFERENS: Done. Sleeping.")
    while True:
        time.sleep(86400)