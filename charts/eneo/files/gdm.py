#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import requests
import os
import urllib3

urllib3.disable_warnings()

url = os.getenv("ENEO_URL", "http://localhost:8000")
username = os.getenv("DEFAULT_USER_EMAIL", "")
password = os.getenv("DEFAULT_USER_PASSWORD", "")

gdm_config = {}
with open("/app/gdm.json", "r") as f:
    gdm_config = json.loads(f.read())

provider_config = {
    "name": "GDM",
    "provider_type": "openai",
    "config": {
        "endpoint": "https://aidev.gdm.se/api/v1" if os.getenv("TESTCLUSTER", "").lower() == "true" else "https://ai.gdm.se/api/v1"
    },
    "credentials": {
        "api_key": gdm_config.get("apiKey", "")
    },
    "is_active": gdm_config.get("enabled", False)
}

completion_models = [
    {
        "name": "gemma3-27b-it",
        "display_name": "gemma3-27b-it",
        "token_limit": 128000,
        "vision": True,
        "reasoning": False,
        "hosting": "swe",
        "is_active": True,
    },
    {
        "name": "gpt-oss-120b",
        "display_name": "gpt-oss-120b",
        "token_limit": 128000,
        "vision": False,
        "reasoning": True,
        "hosting": "swe",
        "is_active": True,
    },
]

embedding_models = [
    {
        "name": "multilingual-e5-large-instruct",
        "display_name": "multilingual-e5-large-instruct",
        "family": "e5",
        "max_input": 512,
        "hosting": "swe",
        "is_active": True,
    },
]

transcription_models = [
    {
        "name": "kb-whisper-large",
        "display_name": "kb-whisper-large",
        "hosting": "swe",
        "is_active": True,
    },
]

def wait_for_health():
    """Wait for the API healthz endpoint to return 200"""
    health_url = f"{url.rstrip('/')}/api/healthz"
    print(f"Waiting for {health_url} to be ready...")

    while True:
        try:
            response = requests.get(health_url, timeout=5, verify=False)
            if response.status_code == 200:
                print("Health check passed! Service is ready.")
                return
        except requests.exceptions.RequestException as e:
            print(f"Health check failed: {e}")

        print("Retrying in 5 seconds...")
        time.sleep(5)

def get_token():
    login_url = f"{url}/api/v1/users/login/token/"
    payload = {
        "username": username,
        "password": password
    }
    response = requests.post(login_url, data=payload, verify=False)
    response.raise_for_status()
    return response.json()

def get_model_providers(access_token):
    api_url = f"{url}/api/v1/admin/model-providers/"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(api_url, headers=headers, verify=False)
    response.raise_for_status()
    return response.json()

def create_model_provider(access_token, provider_data):
    api_url = f"{url}/api/v1/admin/model-providers/"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(api_url, headers=headers, json=provider_data, verify=False)
    response.raise_for_status()
    return response.json()

def update_model_provider(access_token, provider_id, provider_data):
    api_url = f"{url}/api/v1/admin/model-providers/{provider_id}/"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.put(api_url, headers=headers, json=provider_data, verify=False)
    response.raise_for_status()
    return response.json()

def ensure_model_provider(access_token, provider_data):
    """Create or update the model provider based on whether one named 'GDM' already exists."""
    model_providers = get_model_providers(access_token)
    existing = next(
        (p for p in model_providers if p.get("name") == "GDM"),
        None
    )

    if existing:
        provider_id = existing["id"]
        print(f"Model provider 'GDM' already exists (id={provider_id}), updating...")
        result = update_model_provider(access_token, provider_id, provider_data)
        print("Updated:", json.dumps(result, indent=2))
    else:
        print("Model provider 'GDM' not found, creating...")
        result = create_model_provider(access_token, provider_data)
        print("Created:", json.dumps(result, indent=2))

    return result

def get_ai_models(access_token):
    api_url = f"{url}/api/v1/ai-models/"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(api_url, headers=headers, verify=False)
    response.raise_for_status()
    return response.json()

def create_completion_model(access_token, model_data):
    api_url = f"{url}/api/v1/admin/tenant-models/completion/"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(api_url, headers=headers, json=model_data, verify=False)
    response.raise_for_status()
    return response.json()

def update_completion_model(access_token, model_id, model_data):
    api_url = f"{url}/api/v1/admin/tenant-models/completion/{model_id}/"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.put(api_url, headers=headers, json=model_data, verify=False)
    response.raise_for_status()
    return response.json()

def ensure_completion_models(access_token, provider_id, models):
    """Create or update completion models for the given provider."""
    ai_models = get_ai_models(access_token)
    existing_completion = ai_models.get("completion_models", [])
    existing_by_name = {m["name"]: m for m in existing_completion if m.get("name")}

    for model in models:
        model_data = {**model, "provider_id": provider_id}
        name = model["name"]

        if name in existing_by_name:
            model_id = existing_by_name[name]["id"]
            print(f"Completion model '{name}' already exists (id={model_id}), updating...")
            result = update_completion_model(access_token, model_id, model_data)
            print("Updated:", json.dumps(result, indent=2))
        else:
            print(f"Completion model '{name}' not found, creating...")
            result = create_completion_model(access_token, model_data)
            print("Created:", json.dumps(result, indent=2))

def create_embedding_model(access_token, model_data):
    api_url = f"{url}/api/v1/admin/tenant-models/embedding/"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(api_url, headers=headers, json=model_data, verify=False)
    response.raise_for_status()
    return response.json()

def update_embedding_model(access_token, model_id, model_data):
    api_url = f"{url}/api/v1/admin/tenant-models/embedding/{model_id}/"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.put(api_url, headers=headers, json=model_data, verify=False)
    response.raise_for_status()
    return response.json()

def ensure_embedding_models(access_token, provider_id, models):
    """Create or update embedding models for the given provider."""
    ai_models = get_ai_models(access_token)
    existing_embedding = ai_models.get("embedding_models", [])
    existing_by_name = {m["name"]: m for m in existing_embedding if m.get("name")}

    for model in models:
        model_data = {**model, "provider_id": provider_id}
        name = model["name"]

        if name in existing_by_name:
            model_id = existing_by_name[name]["id"]
            print(f"Embedding model '{name}' already exists (id={model_id}), updating...")
            result = update_embedding_model(access_token, model_id, model_data)
            print("Updated:", json.dumps(result, indent=2))
        else:
            print(f"Embedding model '{name}' not found, creating...")
            result = create_embedding_model(access_token, model_data)
            print("Created:", json.dumps(result, indent=2))

def create_transcription_model(access_token, model_data):
    api_url = f"{url}/api/v1/admin/tenant-models/transcription/"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(api_url, headers=headers, json=model_data, verify=False)
    response.raise_for_status()
    return response.json()

def update_transcription_model(access_token, model_id, model_data):
    api_url = f"{url}/api/v1/admin/tenant-models/transcription/{model_id}/"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.put(api_url, headers=headers, json=model_data, verify=False)
    response.raise_for_status()
    return response.json()

def ensure_transcription_models(access_token, provider_id, models):
    """Create or update transcription models for the given provider."""
    ai_models = get_ai_models(access_token)
    existing_transcription = ai_models.get("transcription_models", [])
    existing_by_name = {m["name"]: m for m in existing_transcription if m.get("name")}

    for model in models:
        model_data = {**model, "provider_id": provider_id}
        name = model["name"]

        if name in existing_by_name:
            model_id = existing_by_name[name]["id"]
            print(f"Transcription model '{name}' already exists (id={model_id}), updating...")
            result = update_transcription_model(access_token, model_id, model_data)
            print("Updated:", json.dumps(result, indent=2))
        else:
            print(f"Transcription model '{name}' not found, creating...")
            result = create_transcription_model(access_token, model_data)
            print("Created:", json.dumps(result, indent=2))

if __name__ == "__main__":
    wait_for_health()
    token_data = get_token()
    access_token = token_data["access_token"]

    provider = ensure_model_provider(access_token, provider_config)
    ensure_completion_models(access_token, provider["id"], completion_models)
    ensure_embedding_models(access_token, provider["id"], embedding_models)
    ensure_transcription_models(access_token, provider["id"], transcription_models)
    while True:
        time.sleep(86400)  # Sleep for 24 hours at a time