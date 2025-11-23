#!/usr/bin/env python3
"""Script to update Anthropic deprecations from provided text information."""

from pathlib import Path

import yaml

# Parse deprecation information from the provided text
DEPRECATED_MODELS = {
    # 2025-10-28: Claude Sonnet 3.7 model
    "claude-3-7-sonnet-20250219": {
        "deprecation_date": "2025-10-28",
        "retirement_date": "2026-02-19",
        "replacement": "claude-sonnet-4-5-20250929",
        "notes": None,
    },
    # 2025-08-13: Claude Sonnet 3.5 models
    "claude-3-5-sonnet-20240620": {
        "deprecation_date": "2025-08-13",
        "retirement_date": "2025-10-28",
        "replacement": "claude-sonnet-4-5-20250929",
        "notes": None,
    },
    "claude-3-5-sonnet-20241022": {
        "deprecation_date": "2025-08-13",
        "retirement_date": "2025-10-28",
        "replacement": "claude-sonnet-4-5-20250929",
        "notes": None,
    },
    # 2025-06-30: Claude Opus 3 model
    "claude-3-opus-20240229": {
        "deprecation_date": "2025-06-30",
        "retirement_date": "2026-01-05",
        "replacement": "claude-opus-4-1-20250805",
        "notes": None,
    },
    # 2025-01-21: Claude 2, Claude 2.1, and Claude Sonnet 3 models
    "claude-2.0": {
        "deprecation_date": "2025-01-21",
        "retirement_date": "2025-07-21",
        "replacement": "claude-sonnet-4-5-20250929",
        "notes": None,
    },
    "claude-2.1": {
        "deprecation_date": "2025-01-21",
        "retirement_date": "2025-07-21",
        "replacement": "claude-sonnet-4-5-20250929",
        "notes": None,
    },
    "claude-3-sonnet-20240229": {
        "deprecation_date": "2025-01-21",
        "retirement_date": "2025-07-21",
        "replacement": "claude-sonnet-4-5-20250929",
        "notes": None,
    },
    # 2024-09-04: Claude 1 and Instant models
    "claude-1.0": {
        "deprecation_date": "2024-09-04",
        "retirement_date": "2024-11-06",
        "replacement": "claude-3-5-haiku-20241022",
        "notes": None,
    },
    "claude-1.1": {
        "deprecation_date": "2024-09-04",
        "retirement_date": "2024-11-06",
        "replacement": "claude-3-5-haiku-20241022",
        "notes": None,
    },
    "claude-1.2": {
        "deprecation_date": "2024-09-04",
        "retirement_date": "2024-11-06",
        "replacement": "claude-3-5-haiku-20241022",
        "notes": None,
    },
    "claude-1.3": {
        "deprecation_date": "2024-09-04",
        "retirement_date": "2024-11-06",
        "replacement": "claude-3-5-haiku-20241022",
        "notes": None,
    },
    "claude-instant-1.0": {
        "deprecation_date": "2024-09-04",
        "retirement_date": "2024-11-06",
        "replacement": "claude-3-5-haiku-20241022",
        "notes": None,
    },
    "claude-instant-1.1": {
        "deprecation_date": "2024-09-04",
        "retirement_date": "2024-11-06",
        "replacement": "claude-3-5-haiku-20241022",
        "notes": None,
    },
    "claude-instant-1.2": {
        "deprecation_date": "2024-09-04",
        "retirement_date": "2024-11-06",
        "replacement": "claude-3-5-haiku-20241022",
        "notes": None,
    },
}

# Active models (from the status table)
ACTIVE_MODELS = [
    "claude-3-haiku-20240307",
    "claude-3-5-haiku-20241022",
    "claude-sonnet-4-20250514",
    "claude-opus-4-20250514",
    "claude-opus-4-1-20250805",
    "claude-sonnet-4-5-20250929",
    "claude-haiku-4-5-20251001",
]

# Legacy models - based on the status table, there don't appear to be any
# current legacy models (models that will no longer receive updates but
# haven't been deprecated yet). All deprecated models are already in the
# deprecated list above.
LEGACY_MODELS = {}


def update_providers_yaml(providers_file: Path) -> None:
    """Update providers.yaml with Anthropic deprecation information."""
    # Load existing YAML
    with open(providers_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if "providers" not in data:
        data["providers"] = {}

    if "Anthropic" not in data["providers"]:
        data["providers"]["Anthropic"] = {
            "safety_level": "safe",
            "models": {"live": [], "legacy": [], "deprecated": []},
        }

    # Get current live models
    current_live = data["providers"]["Anthropic"]["models"].get("live", [])

    # Start with active models from the status table
    live_models = list(ACTIVE_MODELS)

    # Add any other models from current_live that aren't deprecated or legacy
    deprecated_model_ids = set(DEPRECATED_MODELS.keys())
    legacy_model_ids = set(LEGACY_MODELS.keys())

    for model in current_live:
        if model not in deprecated_model_ids and model not in legacy_model_ids:
            if model not in live_models:
                live_models.append(model)

    # Remove deprecated models from live list
    live_models = [m for m in live_models if m not in deprecated_model_ids]
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
    data["providers"]["Anthropic"]["models"]["live"] = sorted(live_models)
    data["providers"]["Anthropic"]["models"]["deprecated"] = deprecated_models
    data["providers"]["Anthropic"]["models"]["legacy"] = legacy_models if legacy_models else []

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
