#!/usr/bin/env python3
"""Script to update OpenAI model deprecations from the OpenAI API and deprecations page.

This script:
1. Fetches available models from the OpenAI API
2. Scrapes deprecation information from the OpenAI deprecations page
3. Updates providers.yaml with the latest information
"""

import os
import re
from pathlib import Path
from typing import Any

import requests
import yaml
from openai import OpenAI


def get_openai_models() -> list[str]:
    """Get list of available models from OpenAI API.

    Returns:
        List of model IDs
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    client = OpenAI(api_key=api_key)
    models = client.models.list()

    model_ids = [model.id for model in models]
    return sorted(model_ids)


def scrape_deprecations_page() -> dict[str, Any]:
    """Scrape deprecation information from OpenAI deprecations page.

    Note: The OpenAI deprecations page may be JavaScript-rendered, so this is a best-effort
    attempt. Manual review and updates may be needed.

    Returns:
        Dictionary with deprecated and legacy model information
    """
    url = "https://platform.openai.com/docs/deprecations"
    deprecated_models = {}
    legacy_models = {}

    try:
        # Use a user agent to avoid being blocked
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()

        content = response.text

        # Extract deprecated models from the page
        # Look for patterns that indicate deprecated models
        date_pattern = r"(\d{4}-\d{2}-\d{2})"
        model_patterns = [
            r"text-davinci-\d+",
            r"code-davinci-\d+",
            r"gpt-\d+",
            r"gpt-\d+\.\d+",
            r"gpt-\d+-turbo",
            r"gpt-\d+-turbo-instruct",
            r"gpt-\d+-turbo-\d+",
        ]

        # Extract potential deprecated models
        for pattern in model_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                model_id = match.group(0).lower()
                # Look for dates near the model mention
                context_start = max(0, match.start() - 300)
                context_end = min(len(content), match.end() + 300)
                context = content[context_start:context_end]

                # Check if this looks like a deprecation notice
                deprecation_keywords = ["deprecated", "retired", "removed", "sunset"]
                legacy_keywords = ["legacy", "scheduled", "future"]

                is_deprecated = any(keyword in context.lower() for keyword in deprecation_keywords)
                is_legacy = any(keyword in context.lower() for keyword in legacy_keywords)

                if is_deprecated or is_legacy:
                    dates = re.findall(date_pattern, context)
                    if dates:
                        if is_deprecated:
                            deprecated_models[model_id] = {
                                "deprecation_date": dates[0],
                                "retirement_date": dates[-1] if len(dates) > 1 else dates[0],
                            }
                        elif is_legacy:
                            legacy_models[model_id] = {
                                "deprecation_date": dates[0] if dates else None,
                                "retirement_date": dates[-1] if len(dates) > 1 else None,
                            }
    except Exception:
        pass

    return {"deprecated": deprecated_models, "legacy": legacy_models}


def categorize_models(
    all_models: list[str],
    deprecated_from_page: dict[str, Any],
    existing_deprecated: list[dict[str, Any]],
    existing_legacy: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]], list[dict[str, Any]]]:
    """Categorize models into live, deprecated, and legacy.

    Args:
        all_models: List of all model IDs from API
        deprecated_from_page: Deprecated models from scraping
        existing_deprecated: Existing deprecated models from YAML
        existing_legacy: Existing legacy models from YAML

    Returns:
        Tuple of (live_models, deprecated_models, legacy_models)
    """
    # Create a set of known deprecated model IDs
    existing_deprecated_ids = {m.get("model_id") for m in existing_deprecated}
    existing_legacy_ids = {m.get("model_id") for m in existing_legacy}
    deprecated_from_page_ids = set(deprecated_from_page.get("deprecated", {}).keys())
    legacy_from_page_ids = set(deprecated_from_page.get("legacy", {}).keys())

    # Combine all known deprecated and legacy models
    all_deprecated_ids = existing_deprecated_ids | deprecated_from_page_ids
    all_legacy_ids = existing_legacy_ids | legacy_from_page_ids

    # Known deprecated models that should not appear in live list
    # These are models that are definitely deprecated but might not be in the API response
    known_deprecated = {
        "text-davinci-003",
        "text-davinci-002",
        "text-davinci-001",
        "code-davinci-002",
        "code-davinci-001",
        "gpt-3.5-turbo-0301",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-3.5-turbo-0613",
        "gpt-4-0613",
        "gpt-4-32k-0613",
    }

    all_deprecated_ids.update(known_deprecated)

    # Filter out deprecated and legacy models from live list
    # Also filter out old model families that are no longer available
    excluded_patterns = ["davinci", "curie", "babbage", "ada", "embedding-ada"]
    excluded_suffixes = ["-0314", "-0301", "-0613"]

    live_models = [
        model
        for model in all_models
        if model not in all_deprecated_ids
        and model not in all_legacy_ids
        and not any(pattern in model.lower() for pattern in excluded_patterns)
        and not any(model.endswith(suffix) for suffix in excluded_suffixes)
    ]

    # Build deprecated models list, preserving existing information
    deprecated_models = []
    for model_id in sorted(all_deprecated_ids):
        # Check if we have info from page
        if model_id in deprecated_from_page.get("deprecated", {}):
            info = deprecated_from_page["deprecated"][model_id]
            # Try to preserve existing replacement/notes if available
            existing = next((m for m in existing_deprecated if m.get("model_id") == model_id), None)
            deprecated_models.append(
                {
                    "model_id": model_id,
                    "deprecation_date": info.get("deprecation_date")
                    or (existing.get("deprecation_date") if existing else None),
                    "retirement_date": info.get("retirement_date")
                    or (existing.get("retirement_date") if existing else None),
                    "replacement": existing.get("replacement") if existing else None,
                    "notes": existing.get("notes") if existing else None,
                }
            )
        else:
            # Use existing info if available
            existing = next((m for m in existing_deprecated if m.get("model_id") == model_id), None)
            if existing:
                deprecated_models.append(existing)
            else:
                # Default entry for known deprecated models
                deprecated_models.append(
                    {
                        "model_id": model_id,
                        "deprecation_date": None,
                        "retirement_date": None,
                        "replacement": None,
                        "notes": "Deprecated model - please update with dates from deprecations page",
                    }
                )

    # Build legacy models list
    legacy_models = []
    for model_id in sorted(all_legacy_ids):
        if model_id in deprecated_from_page.get("legacy", {}):
            info = deprecated_from_page["legacy"][model_id]
            existing = next((m for m in existing_legacy if m.get("model_id") == model_id), None)
            legacy_models.append(
                {
                    "model_id": model_id,
                    "deprecation_date": info.get("deprecation_date")
                    or (existing.get("deprecation_date") if existing else None),
                    "retirement_date": info.get("retirement_date")
                    or (existing.get("retirement_date") if existing else None),
                    "replacement": existing.get("replacement") if existing else None,
                    "notes": existing.get("notes") if existing else None,
                }
            )
        else:
            existing = next((m for m in existing_legacy if m.get("model_id") == model_id), None)
            if existing:
                legacy_models.append(existing)

    return live_models, deprecated_models, legacy_models


def update_providers_yaml(
    live_models: list[str],
    deprecated_models: list[dict[str, Any]],
    legacy_models: list[dict[str, Any]],
    providers_file: Path,
) -> None:
    """Update providers.yaml with new model information.

    Args:
        live_models: List of live model IDs
        deprecated_models: List of deprecated model dictionaries
        legacy_models: List of legacy model dictionaries
        providers_file: Path to providers.yaml file
    """
    # Load existing YAML
    with open(providers_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Update OpenAI section
    if "providers" not in data:
        data["providers"] = {}

    if "OpenAI" not in data["providers"]:
        data["providers"]["OpenAI"] = {
            "safety_level": "safe",
            "models": {"live": [], "legacy": [], "deprecated": []},
        }

    # Update models
    data["providers"]["OpenAI"]["models"]["live"] = sorted(live_models)
    data["providers"]["OpenAI"]["models"]["deprecated"] = deprecated_models
    data["providers"]["OpenAI"]["models"]["legacy"] = legacy_models if legacy_models else []

    # Custom YAML representer for None values
    def represent_none(self, _):
        return self.represent_scalar("tag:yaml.org,2002:null", "null")

    yaml.add_representer(type(None), represent_none)

    # Write back to file with proper formatting
    with open(providers_file, "w", encoding="utf-8") as f:
        # Write header comment
        f.write("# Provider Configuration\n")
        f.write("# Unified configuration for all providers including safety levels and model status\n")
        f.write("\n")
        # Dump the data
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=120,
        )


def main() -> None:
    """Main function to update OpenAI deprecations."""
    # Get script directory and find providers.yaml
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    providers_file = project_root / "neops" / "config" / "providers.yaml"

    if not providers_file.exists():
        raise FileNotFoundError(f"providers.yaml not found at {providers_file}")

    try:
        all_models = get_openai_models()
    except Exception as e:
        raise ValueError(f"Error fetching models from API: {e}") from e

    try:
        deprecated_from_page = scrape_deprecations_page()
    except Exception:
        deprecated_from_page = {"deprecated": {}, "legacy": {}}

    # Load existing deprecated and legacy models
    with open(providers_file, "r", encoding="utf-8") as f:
        existing_data = yaml.safe_load(f) or {}
    existing_deprecated = existing_data.get("providers", {}).get("OpenAI", {}).get("models", {}).get("deprecated", [])
    existing_legacy = existing_data.get("providers", {}).get("OpenAI", {}).get("models", {}).get("legacy", [])

    live_models, deprecated_models, legacy_models = categorize_models(
        all_models, deprecated_from_page, existing_deprecated, existing_legacy
    )

    update_providers_yaml(live_models, deprecated_models, legacy_models, providers_file)


if __name__ == "__main__":
    main()
