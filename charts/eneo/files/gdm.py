#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

logger = get_logger(__name__)

url = "https://gdm-allo.ai.gdm.se/"
superapikey = os.getenv("INTRIC_SUPER_API_KEY")
superduperapikey = os.getenv("INTRIC_SUPERDUPER_API_KEY")

models = { "completion_models": [], "embedding_models": [] }

models["completion_models"].append({
    "name": "gemma3-27b-it",
    "nickname": "gemma3-27b-it",
    "family": "openai",
    "token_limit": 128000,
    "stability": "stable",
    "hosting": "swe",
    "description": "Google's Gemma 3 27B instruction-tuned model, hosted by GDM in Sweden (ai.gdm.se).",
    "org": "GDM",
    "vision": True,
    "reasoning": False,
    "litellm_model_name": "gdm/gemma3-27b-it"
})

models["embedding_models"].append({
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
})

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


async def create_models(
    models: dict,
    repository: type[CompletionModelsRepository] | type[AdminEmbeddingModelsService],
    model_create: type[CompletionModelCreate] | type[EmbeddingModelCreate],
    model_update: type[CompletionModelUpdate] | type[EmbeddingModelUpdate],
):
    async with sessionmanager.session() as session, session.begin():
        repository = repository(session=session)

        existing_models = await repository.get_ids_and_names()
        existing_models_names = {model.name: model.id for model in existing_models}
        new_models_names = [model["name"] for model in models]

        # remove models
        for model in existing_models:
            if model.name not in new_models_names:
                await repository.delete_model(model.id)

        # create new models or update existing
        for model in models:
            model = model_create(**model)
            if model.name not in existing_models_names:
                await repository.create_model(model)
            else:
                model = model_update(**model.model_dump(), id=existing_models_names[model.name])
                await repository.update_model(model)


async def init_models():
    try:

        logger.info("Completion Models initialization...")
        completion_models = models["completion_models"]
        await create_models(
            models=completion_models,
            repository=CompletionModelsRepository,
            model_create=CompletionModelCreate,
            model_update=CompletionModelUpdate,
        )
        logger.info("Completion Models initialization completed.")

        logger.info("Embedding Models initialization...")
        embedding_models = models["embedding_models"]
        await create_models(
            models=embedding_models,
            repository=AdminEmbeddingModelsService,
            model_create=EmbeddingModelCreate,
            model_update=EmbeddingModelUpdate,
        )
        logger.info("Embedding Models initialization completed.")

    except Exception as e:
        logger.exception(f"Creating models crashed with next error: {str(e)}")

if __name__ == "__main__":
    try:
        wait_for_health()
        print("Entering main loop...")
        r = requests.get(f"{url.rstrip('/')}/api/v1/sysadmin/tenants/", headers={"X-API-KEY": superapikey})
        print(r.json())
        tenant_id = r.json()['items'][0]['id']
        
        r = requests.get(f"{url.rstrip('/')}/api/v1/modules/", headers={"X-API-KEY": superduperapikey})
        for module in r.json()['items']:
            if module['name'] == 'SWE Models':
                module_id = module['id']
                break
        
        r = requests.post(
            f"{url.rstrip('/')}/api/v1/modules/{tenant_id}/",
            headers={"X-API-KEY": superduperapikey},
            json=[{"id": module_id}]
        )
        asyncio.run(init_models())
        
        
        while True:
            time.sleep(86400)  # Sleep for 24 hours at a time
    except KeyboardInterrupt:
        print("\nExiting...")

