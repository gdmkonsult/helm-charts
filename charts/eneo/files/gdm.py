#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import requests
import os

# Check if this is the first run
firstrun_file = "/app/data/firstrun.gdm"
firstrun = not os.path.exists(firstrun_file)

url = "http://localhost:8000"
superapikey = os.getenv("INTRIC_SUPER_API_KEY")
superduperapikey = os.getenv("INTRIC_SUPER_DUPER_API_KEY")

gdm_config = {}
with open("/app/gdm.json", "r") as f:
    gdm_config = json.loads(f.read())

models = { "completion_models": {}, "embedding_models": {} }

models["completion_models"]["gemma3-27b-it"] = {
    "name": "gemma3-27b-it",
    "nickname": "gemma3-27b-it",
    "family": "openai",
    "token_limit": 128000,
    "stability": "stable",
    "is_deprecated": False,
    "hosting": "swe",
    "description": "Google's Gemma 3 27B instruction-tuned model, hosted by GDM in Sweden (ai.gdm.se).",
    "org": "GDM",
    "vision": True,
    "reasoning": False,
    "litellm_model_name": "gdm/gemma3-27b-it"
}

models["completion_models"]["gpt-oss-120b"] = {
    "name": "gpt-oss-120b",
    "nickname": "gpt-oss-120b",
    "family": "openai",
    "token_limit": 128000,
    "stability": "stable",
    "is_deprecated": False,
    "hosting": "swe",
    "description": "OpenAIs open model gpt-oss-120b, hosted by GDM in Sweden (ai.gdm.se).",
    "org": "GDM",
    "vision": False,
    "reasoning": False,
    "litellm_model_name": "gdm/gpt-oss-120b"
}

models["embedding_models"]["multilingual-e5-large-instruct"] = {
    "name": "multilingual-e5-large-instruct",
    "family": "e5",
    "open_source": True,
    "max_input": 1400,
    "max_batch_size": 32,
    "is_deprecated": False,
    "stability": "stable",
    "hosting": "swe",
    "description": "GDM's E5 multilingual embedding model with instruction tuning, hosted in Sweden (ai.gdm.se).",
    "org": "GDM",
    "litellm_model_name": "gdm/multilingual-e5-large-instruct"
}


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

def delete_completion_model(model_id: str) -> bool:
    """Delete a completion model by its ID.
    
    Args:
        model_id: The ID of the model to delete
        
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        response = requests.delete(
            f"{url.rstrip('/')}/api/v1/sysadmin/completion-models/{model_id}",
            headers={"X-API-KEY": superapikey}
        )
        if response.status_code in (200, 204):
            print(f"Successfully deleted completion model: {model_id}")
            return True
        else:
            print(f"Failed to delete completion model {model_id}: {response.status_code} {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error deleting completion model {model_id}: {e}")
        return False

def delete_embedding_model(model_id: str) -> bool:
    """Delete an embedding model by its ID.
    
    Args:
        model_id: The ID of the model to delete
        
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        response = requests.delete(
            f"{url.rstrip('/')}/api/v1/sysadmin/embedding-models/{model_id}",
            headers={"X-API-KEY": superapikey}
        )
        if response.status_code in (200, 204):
            print(f"Successfully deleted embedding model: {model_id}")
            return True
        else:
            print(f"Failed to delete embedding model {model_id}: {response.status_code} {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error deleting embedding model {model_id}: {e}")
        return False

if __name__ == "__main__":
    try:
        wait_for_health()
        print("Entering main loop...")
        print(f"First run: {firstrun}")
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


        if gdm_config.get("enabled", False):
            r = requests.put(
                f"{url.rstrip('/')}/api/v1/sysadmin/tenants/{tenant_id}/credentials/gdm",
                headers={"X-API-KEY": superapikey},
                json={
                    "api_key": gdm_config.get("apiKey", ""),
                }
            )
            print("GDM enabled:", r.status_code, r.text)

        # If first run, register models
        if firstrun:
            # First, delete models that don't have org set to GDM
            print("Cleaning up non-GDM models...")
            
            # Fetch and delete non-GDM completion models
            r = requests.get(
                f"{url.rstrip('/')}/api/v1/sysadmin/completion-models/",
                headers={"X-API-KEY": superapikey}
            )
            if r.status_code == 200:
                existing_completion_models = r.json().get('items', [])
                for model in existing_completion_models:
                    if model.get('org') != 'GDM':
                        print(f"Deleting non-GDM completion model: {model.get('name', model.get('id'))}")
                        delete_completion_model(model['id'])
            
            # Fetch and delete non-GDM embedding models
            r = requests.get(
                f"{url.rstrip('/')}/api/v1/sysadmin/embedding-models/",
                headers={"X-API-KEY": superapikey}
            )
            if r.status_code == 200:
                existing_embedding_models = r.json().get('items', [])
                for model in existing_embedding_models:
                    if model.get('org') != 'GDM':
                        print(f"Deleting non-GDM embedding model: {model.get('name', model.get('id'))}")
                        delete_embedding_model(model['id'])
            
            print("Registering GDM models...")
            for model in models["completion_models"].values():
                r = requests.post(
                    f"{url.rstrip('/')}/api/v1/sysadmin/completion-models/create",
                    headers={"X-API-KEY": superapikey},
                    json=model
                )
                print(f"Registered completion model {model['name']}: {r.status_code} {r.text}")
                
                # Enable model on tenant if creation was successful
                if r.status_code in (200, 201):
                    model_id = r.json().get("id")
                    if model_id:
                        is_default = model['name'] == 'gpt-oss-120b'
                        enable_r = requests.post(
                            f"{url.rstrip('/')}/api/v1/sysadmin/tenants/{tenant_id}/completion-models/{model_id}/",
                            headers={"X-API-KEY": superapikey},
                            json={
                                "is_org_enabled": True,
                                "is_org_default": is_default
                            }
                        )
                        print(f"Enabled completion model {model['name']} on tenant (default={is_default}): {enable_r.status_code} {enable_r.text}")
            
            for model in models["embedding_models"].values():
                r = requests.post(
                    f"{url.rstrip('/')}/api/v1/sysadmin/embedding-models/create",
                    headers={"X-API-KEY": superapikey},
                    json=model
                )
                print(f"Registered embedding model {model['name']}: {r.status_code} {r.text}")
                
                # Enable model on tenant if creation was successful
                if r.status_code in (200, 201):
                    model_id = r.json().get("id")
                    if model_id:
                        is_default = model['name'] == 'multilingual-e5-large-instruct'
                        enable_r = requests.post(
                            f"{url.rstrip('/')}/api/v1/sysadmin/tenants/{tenant_id}/embedding-models/{model_id}/",
                            headers={"X-API-KEY": superapikey},
                            json={
                                "is_org_enabled": True,
                                "is_org_default": is_default
                            }
                        )
                        print(f"Enabled embedding model {model['name']} on tenant (default={is_default}): {enable_r.status_code} {enable_r.text}")

        # Fetch existing models
        r = requests.get(
            f"{url.rstrip('/')}/api/v1/sysadmin/completion-models/",
            headers={"X-API-KEY": superapikey}
        )
        
        
        r = requests.get(
            f"{url.rstrip('/')}/api/v1/sysadmin/embedding-models/",
            headers={"X-API-KEY": superapikey}
        )

        
        # Mark first run as complete
        os.makedirs(os.path.dirname(firstrun_file), exist_ok=True)
        with open(firstrun_file, "w") as f:
            f.write("")
        
        while True:
            time.sleep(86400)  # Sleep for 24 hours at a time
    except KeyboardInterrupt:
        print("\nExiting...")

