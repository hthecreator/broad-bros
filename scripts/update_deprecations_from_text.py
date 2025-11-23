#!/usr/bin/env python3
"""Script to update OpenAI deprecations from provided text information."""

from pathlib import Path

import yaml

# Parse deprecation information from the provided text
DEPRECATED_MODELS = {
    # 2025-11-18: chatgpt-4o-latest snapshot
    "chatgpt-4o-latest": {
        "deprecation_date": "2025-11-18",
        "retirement_date": "2026-02-17",
        "replacement": "gpt-5.1-chat-latest",
        "notes": None,
    },
    # 2025-11-17: codex-mini-latest model snapshot
    "codex-mini-latest": {
        "deprecation_date": "2025-11-17",
        "retirement_date": "2026-01-16",
        "replacement": "gpt-5-codex-mini",
        "notes": None,
    },
    # 2025-11-14: DALL·E model snapshots
    "dall-e-2": {
        "deprecation_date": "2025-11-14",
        "retirement_date": "2026-05-12",
        "replacement": "gpt-image-1 or gpt-image-1-mini",
        "notes": None,
    },
    "dall-e-3": {
        "deprecation_date": "2025-11-14",
        "retirement_date": "2026-05-12",
        "replacement": "gpt-image-1 or gpt-image-1-mini",
        "notes": None,
    },
    # 2025-09-26: Legacy GPT model snapshots
    "gpt-4-0314": {
        "deprecation_date": "2025-09-26",
        "retirement_date": "2026-03-26",
        "replacement": "gpt-5 or gpt-4.1*",
        "notes": None,
    },
    "gpt-4-1106-preview": {
        "deprecation_date": "2025-09-26",
        "retirement_date": "2026-03-26",
        "replacement": "gpt-5 or gpt-4.1*",
        "notes": None,
    },
    "gpt-4-0125-preview": {
        "deprecation_date": "2025-09-26",
        "retirement_date": "2026-03-26",
        "replacement": "gpt-5 or gpt-4.1*",
        "notes": None,
    },
    "gpt-4-turbo-preview": {
        "deprecation_date": "2025-09-26",
        "retirement_date": "2026-03-26",
        "replacement": "gpt-5 or gpt-4.1*",
        "notes": "Points to gpt-4-0125-preview",
    },
    "gpt-4-turbo-preview-completions": {
        "deprecation_date": "2025-09-26",
        "retirement_date": "2026-03-26",
        "replacement": "gpt-5 or gpt-4.1*",
        "notes": "Points to gpt-4-0125-preview",
    },
    "gpt-3.5-turbo-instruct": {
        "deprecation_date": "2025-09-26",
        "retirement_date": "2026-09-28",
        "replacement": "gpt-5-mini or gpt-4.1-mini*",
        "notes": None,
    },
    "babbage-002": {
        "deprecation_date": "2025-09-26",
        "retirement_date": "2026-09-28",
        "replacement": "gpt-5-mini or gpt-4.1-mini*",
        "notes": None,
    },
    "davinci-002": {
        "deprecation_date": "2025-09-26",
        "retirement_date": "2026-09-28",
        "replacement": "gpt-5-mini or gpt-4.1-mini*",
        "notes": None,
    },
    "gpt-3.5-turbo-1106": {
        "deprecation_date": "2025-09-26",
        "retirement_date": "2026-09-28",
        "replacement": "gpt-5-mini or gpt-4.1-mini*",
        "notes": None,
    },
    # 2025-09-15: gpt-4o-realtime-preview models
    "gpt-4o-realtime-preview": {
        "deprecation_date": "2025-09-15",
        "retirement_date": "2026-02-27",
        "replacement": "gpt-realtime",
        "notes": None,
    },
    "gpt-4o-realtime-preview-2025-06-03": {
        "deprecation_date": "2025-09-15",
        "retirement_date": "2026-02-27",
        "replacement": "gpt-realtime",
        "notes": None,
    },
    "gpt-4o-realtime-preview-2024-12-17": {
        "deprecation_date": "2025-09-15",
        "retirement_date": "2026-02-27",
        "replacement": "gpt-realtime",
        "notes": None,
    },
    # 2025-06-10: gpt-4o-realtime-preview-2024-10-01
    "gpt-4o-realtime-preview-2024-10-01": {
        "deprecation_date": "2025-06-10",
        "retirement_date": "2025-10-10",
        "replacement": "gpt-realtime",
        "notes": None,
    },
    # 2025-06-10: gpt-4o-audio-preview-2024-10-01
    "gpt-4o-audio-preview-2024-10-01": {
        "deprecation_date": "2025-06-10",
        "retirement_date": "2025-10-10",
        "replacement": "gpt-4o-audio-preview",
        "notes": None,
    },
    # 2025-04-28: text-moderation
    "text-moderation-007": {
        "deprecation_date": "2025-04-28",
        "retirement_date": "2025-10-27",
        "replacement": "omni-moderation",
        "notes": None,
    },
    "text-moderation-stable": {
        "deprecation_date": "2025-04-28",
        "retirement_date": "2025-10-27",
        "replacement": "omni-moderation",
        "notes": None,
    },
    "text-moderation-latest": {
        "deprecation_date": "2025-04-28",
        "retirement_date": "2025-10-27",
        "replacement": "omni-moderation",
        "notes": None,
    },
    # 2025-04-28: o1-preview and o1-mini
    "o1-preview": {
        "deprecation_date": "2025-04-28",
        "retirement_date": "2025-07-28",
        "replacement": "o3",
        "notes": None,
    },
    "o1-mini": {
        "deprecation_date": "2025-04-28",
        "retirement_date": "2025-10-27",
        "replacement": "o4-mini",
        "notes": None,
    },
    # 2025-04-14: GPT-4.5-preview
    "gpt-4.5-preview": {
        "deprecation_date": "2025-04-14",
        "retirement_date": "2025-07-14",
        "replacement": "gpt-4.1",
        "notes": None,
    },
    # 2024-10-02: Assistants API beta v1 (not a model, but included for completeness)
    # 2024-08-29: Fine-tuning training on babbage-002 and davinci-002 (not models themselves)
    # 2024-06-06: GPT-4-32K and Vision Preview models
    "gpt-4-32k": {
        "deprecation_date": "2024-06-06",
        "retirement_date": "2025-06-06",
        "replacement": "gpt-4o",
        "notes": None,
    },
    "gpt-4-32k-0613": {
        "deprecation_date": "2024-06-06",
        "retirement_date": "2025-06-06",
        "replacement": "gpt-4o",
        "notes": None,
    },
    "gpt-4-32k-0314": {
        "deprecation_date": "2024-06-06",
        "retirement_date": "2025-06-06",
        "replacement": "gpt-4o",
        "notes": None,
    },
    "gpt-4-vision-preview": {
        "deprecation_date": "2024-06-06",
        "retirement_date": "2024-12-06",
        "replacement": "gpt-4o",
        "notes": None,
    },
    "gpt-4-1106-vision-preview": {
        "deprecation_date": "2024-06-06",
        "retirement_date": "2024-12-06",
        "replacement": "gpt-4o",
        "notes": None,
    },
    # 2023-11-06: Chat model updates
    "gpt-3.5-turbo-0613": {
        "deprecation_date": "2023-11-06",
        "retirement_date": "2024-09-13",
        "replacement": "gpt-3.5-turbo",
        "notes": None,
    },
    "gpt-3.5-turbo-16k-0613": {
        "deprecation_date": "2023-11-06",
        "retirement_date": "2024-09-13",
        "replacement": "gpt-3.5-turbo",
        "notes": None,
    },
    # 2023-08-22: Fine-tunes endpoint (not models)
    # 2023-07-06: GPT and embeddings
    "text-ada-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "gpt-3.5-turbo-instruct",
        "notes": None,
    },
    "text-babbage-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "gpt-3.5-turbo-instruct",
        "notes": None,
    },
    "text-curie-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "gpt-3.5-turbo-instruct",
        "notes": None,
    },
    "text-davinci-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "gpt-3.5-turbo-instruct",
        "notes": None,
    },
    "text-davinci-002": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "gpt-3.5-turbo-instruct",
        "notes": None,
    },
    "text-davinci-003": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "gpt-3.5-turbo-instruct",
        "notes": None,
    },
    "ada": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "babbage-002",
        "notes": None,
    },
    "babbage": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "babbage-002",
        "notes": None,
    },
    "curie": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "davinci-002",
        "notes": None,
    },
    "davinci": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "davinci-002",
        "notes": None,
    },
    "code-davinci-002": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "gpt-3.5-turbo-instruct",
        "notes": None,
    },
    "text-davinci-edit-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "gpt-4o",
        "notes": None,
    },
    "code-davinci-edit-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "gpt-4o",
        "notes": None,
    },
    # First-generation text embedding models
    "text-similarity-ada-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "text-embedding-3-small",
        "notes": None,
    },
    "text-search-ada-doc-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "text-embedding-3-small",
        "notes": None,
    },
    "text-search-ada-query-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "text-embedding-3-small",
        "notes": None,
    },
    "code-search-ada-code-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "text-embedding-3-small",
        "notes": None,
    },
    "code-search-ada-text-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "text-embedding-3-small",
        "notes": None,
    },
    "text-similarity-babbage-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "text-embedding-3-small",
        "notes": None,
    },
    "text-search-babbage-doc-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "text-embedding-3-small",
        "notes": None,
    },
    "text-search-babbage-query-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "text-embedding-3-small",
        "notes": None,
    },
    "code-search-babbage-code-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "text-embedding-3-small",
        "notes": None,
    },
    "code-search-babbage-text-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "text-embedding-3-small",
        "notes": None,
    },
    "text-similarity-curie-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "text-embedding-3-small",
        "notes": None,
    },
    "text-search-curie-doc-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "text-embedding-3-small",
        "notes": None,
    },
    "text-search-curie-query-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "text-embedding-3-small",
        "notes": None,
    },
    "text-similarity-davinci-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "text-embedding-3-small",
        "notes": None,
    },
    "text-search-davinci-doc-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "text-embedding-3-small",
        "notes": None,
    },
    "text-search-davinci-query-001": {
        "deprecation_date": "2023-07-06",
        "retirement_date": "2024-01-04",
        "replacement": "text-embedding-3-small",
        "notes": None,
    },
    # 2023-06-13: Updated chat models
    "gpt-3.5-turbo-0301": {
        "deprecation_date": "2023-06-13",
        "retirement_date": "2024-09-13",
        "replacement": "gpt-3.5-turbo",
        "notes": None,
    },
    # 2023-03-20: Codex models
    "code-davinci-001": {
        "deprecation_date": "2023-03-20",
        "retirement_date": "2023-03-23",
        "replacement": "gpt-4o",
        "notes": None,
    },
    "code-cushman-002": {
        "deprecation_date": "2023-03-20",
        "retirement_date": "2023-03-23",
        "replacement": "gpt-4o",
        "notes": None,
    },
    "code-cushman-001": {
        "deprecation_date": "2023-03-20",
        "retirement_date": "2023-03-23",
        "replacement": "gpt-4o",
        "notes": None,
    },
}

# Legacy models (no longer receiving updates, scheduled for future deprecation)
# From the page: "at earliest 2024-06-13" for gpt-4-0314 was marked as legacy
# But it's now deprecated, so we'll check if there are any current legacy models
LEGACY_MODELS = {
    # Note: Most models that were legacy are now deprecated
    # Add any current legacy models here if needed
}


def update_providers_yaml(providers_file: Path) -> None:
    """Update providers.yaml with deprecation information."""
    # Load existing YAML
    with open(providers_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if "providers" not in data:
        data["providers"] = {}

    if "OpenAI" not in data["providers"]:
        data["providers"]["OpenAI"] = {
            "safety_level": "safe",
            "models": {"live": [], "legacy": [], "deprecated": []},
        }

    # Get current live models
    live_models = data["providers"]["OpenAI"]["models"].get("live", [])

    # Remove deprecated models from live list
    deprecated_model_ids = set(DEPRECATED_MODELS.keys())
    live_models = [m for m in live_models if m not in deprecated_model_ids]

    # Also remove legacy models from live list
    legacy_model_ids = set(LEGACY_MODELS.keys())
    live_models = [m for m in live_models if m not in legacy_model_ids]

    # Build deprecated models list
    deprecated_models = []
    for model_id, info in sorted(DEPRECATED_MODELS.items()):
        deprecated_models.append(
            {
                "model_id": model_id,
                "deprecation_date": info["deprecation_date"],
                "retirement_date": info["retirement_date"],
                "replacement": info["replacement"],
                "notes": info["notes"],
            }
        )

    # Build legacy models list
    legacy_models = []
    for model_id, info in sorted(LEGACY_MODELS.items()):
        legacy_models.append(
            {
                "model_id": model_id,
                "deprecation_date": info.get("deprecation_date"),
                "retirement_date": info.get("retirement_date"),
                "replacement": info.get("replacement"),
                "notes": info.get("notes"),
            }
        )

    # Update the data structure
    data["providers"]["OpenAI"]["models"]["live"] = sorted(live_models)
    data["providers"]["OpenAI"]["models"]["deprecated"] = deprecated_models
    data["providers"]["OpenAI"]["models"]["legacy"] = legacy_models if legacy_models else []

    # Custom YAML representer for None values
    def represent_none(self, _):
        return self.represent_scalar("tag:yaml.org,2002:null", "null")

    yaml.add_representer(type(None), represent_none)

    # Write back to file
    with open(providers_file, "w", encoding="utf-8") as f:
        f.write("# Provider Configuration\n")
        f.write("# Unified configuration for all providers including safety levels and model status\n")
        f.write("\n")
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=120,
        )


def main() -> None:
    """Main function."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    providers_file = project_root / "neops" / "config" / "providers.yaml"

    if not providers_file.exists():
        raise FileNotFoundError(f"providers.yaml not found at {providers_file}")

    update_providers_yaml(providers_file)


if __name__ == "__main__":
    main()
