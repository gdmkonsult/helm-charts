import yaml

models = { "completion_models": [], "embedding_models": [] }

models["completion_models"].append({
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
})

models["completion_models"].append({
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

# Write models to YAML file
output_path = "/app/data/ai_models.yml"

with open(output_path, 'w') as f:
    yaml.dump(models, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f"Models written to {output_path}")


