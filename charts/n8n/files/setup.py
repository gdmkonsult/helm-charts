#!/usr/bin/env python3
"""
n8n first-run setup script.
Waits for n8n to become ready, then checks if initial owner setup is needed.
If showSetupOnFirstLoad is true, creates the first admin user.
"""

import json
import os
import time
import urllib.request
import urllib.error

N8N_URL = os.getenv("N8N_URL", "http://localhost:5678")
ADMIN_EMAIL = os.getenv("N8N_DEFAULT_USER_EMAIL", "")
ADMIN_PASSWORD = os.getenv("N8N_DEFAULT_USER_PASSWORD", "")


def wait_for_health():
    """Wait for n8n healthz endpoint to return 200."""
    url = f"{N8N_URL}/healthz"
    print(f"SETUP: Waiting for n8n to be ready at {url}...")

    for attempt in range(1, 121):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    print("SETUP: n8n is ready!")
                    return True
        except Exception as e:
            pass
        print(f"SETUP: Attempt {attempt}/120 - waiting...")
        time.sleep(3)

    print("SETUP: ERROR - n8n did not become ready in time")
    return False


def check_setup_needed():
    """Check /rest/settings to see if first-run setup is required."""
    url = f"{N8N_URL}/rest/settings"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            show_setup = (
                data.get("data", {})
                .get("userManagement", {})
                .get("showSetupOnFirstLoad", False)
            )
            return show_setup
    except Exception as e:
        print(f"SETUP: Could not fetch settings: {e}")
        return False


def create_owner():
    """Create the first owner account via /rest/owner/setup."""
    url = f"{N8N_URL}/rest/owner/setup"
    payload = json.dumps({
        "email": ADMIN_EMAIL,
        "firstName": "Admin",
        "lastName": "User",
        "password": ADMIN_PASSWORD,
    }).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            print(f"SETUP: Owner account created successfully! (id={result.get('data', {}).get('id', 'unknown')})")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"SETUP: Owner setup failed ({e.code}): {body}")
    except Exception as e:
        print(f"SETUP: Owner setup error: {e}")


if __name__ == "__main__":
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        print("SETUP: No admin email/password configured, skipping setup.")
    elif not wait_for_health():
        print("SETUP: Aborting - n8n not ready.")
    elif not check_setup_needed():
        print("SETUP: Initial setup already completed. Nothing to do.")
    else:
        create_owner()

    print("SETUP: Done. Sleeping.")
    while True:
        time.sleep(86400)
