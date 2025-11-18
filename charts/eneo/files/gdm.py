#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import requests
import os
import asyncio
from intric.ai_models.completion_models.completion_model import (
    CompletionModelCreate,
    CompletionModelUpdate,
)
from intric.ai_models.completion_models.completion_models_repo import (
    CompletionModelsRepository,
)
from intric.ai_models.embedding_models.embedding_model import (
    EmbeddingModelCreate,
    EmbeddingModelUpdate,
)
from intric.ai_models.embedding_models.embedding_models_repo import (
    AdminEmbeddingModelsService,
)
from intric.database.database import sessionmanager
from intric.main.logging import get_logger
from intric.main.config import get_settings

logger = get_logger(__name__)

url = "http://localhost:8000"
superapikey = os.getenv("INTRIC_SUPER_API_KEY")
superduperapikey = os.getenv("INTRIC_SUPER_DUPER_API_KEY")

def wait_for_health():
    """Wait for the API healthz endpoint to return 200"""
    health_url = f"{url.rstrip('/')}/api/healthz"
    print(f"Waiting for {health_url} to be ready...")
    
    while True:
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                print("Health check passed! Service is ready.")
                return
        except requests.exceptions.RequestException as e:
            print(f"Health check failed: {e}")
        
        print("Retrying in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    try:
        wait_for_health()
        print("Entering main loop...")
        r = requests.get(f"{url.rstrip('/')}/api/v1/sysadmin/tenants/", headers={"X-API-KEY": superapikey})
        tenant_id = r.json()['items'][0]['id']
        
        r = requests.get(f"{url.rstrip('/')}/api/v1/modules/", headers={"X-API-KEY": superduperapikey})
        print(r.json())
        for module in r.json()['items']:
            if module['name'] == 'SWE Models':
                module_id = module['id']
                break
        
        r = requests.post(
            f"{url.rstrip('/')}/api/v1/modules/{tenant_id}/",
            headers={"X-API-KEY": superduperapikey},
            json=[{"id": module_id}]
        )
        
        with open("/app/oidc.json", "r") as f:
            oidc_config = json.loads(f.read())
            if oidc_config.get("enabled", False):
                r = requests.put(
                    f"{url.rstrip('/')}/api/v1/sysadmin/tenants/{tenant_id}/federation",
                    headers={"X-API-KEY": superapikey},
                    json={
                        "provider": oidc_config.get("providerName", ""),
                        "client_id": oidc_config.get("clientId", ""),
                        "client_secret": oidc_config.get("clientSecret", ""),
                        "discovery_endpoint": oidc_config.get("discoveryUrl", ""),
                        "redirect_path": "/oauth/callback",
                    }
                )
                print("OIDC enabled:", r.status_code, r.text)
        
        while True:
            time.sleep(86400)  # Sleep for 24 hours at a time
    except KeyboardInterrupt:
        print("\nExiting...")

