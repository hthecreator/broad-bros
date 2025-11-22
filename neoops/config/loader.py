"""Configuration loader for Neops that loads from YAML files with pyproject.toml overrides."""

import tomllib
from pathlib import Path
from typing import Any

import yaml

from neoops.models import Severity
from neoops.rules.models import Rule, RuleClass


def get_config_dir() -> Path:
    """Get the path to the config directory.

    Returns:
        Path to the config directory
    """
    return Path(__file__).parent


def load_yaml(file_path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dictionary.

    Args:
        file_path: Path to the YAML file

    Returns:
        Dictionary containing the YAML contents

    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the YAML is invalid
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_pyproject_toml(project_root: Path | None = None) -> dict[str, Any]:
    """Load pyproject.toml and extract [tool.neops] section.

    Args:
        project_root: Root directory of the project. If None, searches from current directory.

    Returns:
        Dictionary containing the [tool.neops] section, or empty dict if not found
    """
    if project_root is None:
        # Try to find pyproject.toml by walking up from current directory
        current = Path.cwd()
        while current != current.parent:
            toml_file = current / "pyproject.toml"
            if toml_file.exists():
                project_root = current
                break
            current = current.parent
        else:
            return {}

    toml_file = project_root / "pyproject.toml"
    if not toml_file.exists():
        return {}

    try:
        with open(toml_file, "rb") as f:
            data = tomllib.load(f)
            return data.get("tool", {}).get("neops", {})
    except (FileNotFoundError, KeyError, tomllib.TOMLDecodeError):
        return {}


def load_rules(project_root: Path | None = None) -> list[Rule]:
    """Load rules from the rules.yaml configuration file.

    Args:
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        List of Rule objects loaded from the YAML file
    """
    config_dir = get_config_dir()
    rules_file = config_dir / "rules.yaml"
    data = load_yaml(rules_file)

    # Load rule classes
    rule_classes_map: dict[str, RuleClass] = {}
    for rc_data in data.get("rule_classes", []):
        rule_class = RuleClass(**rc_data)
        rule_classes_map[rule_class.id] = rule_class

    # Load rules
    rules = []
    for rule_data in data.get("rules", []):
        rule_class_id = rule_data.pop("rule_class_id")
        rule_class = rule_classes_map.get(rule_class_id)
        if not rule_class:
            raise ValueError(f"Rule class '{rule_class_id}' not found for rule {rule_data.get('rule_id')}")

        # Convert severity string to enum
        severity_str = rule_data.pop("severity", "error")
        severity = Severity(severity_str.lower())

        # Handle null source_link
        source_link = rule_data.pop("source_link")
        if source_link == "null" or source_link is None:
            source_link = None

        rule = Rule(
            rule_class=rule_class,
            severity=severity,
            source_link=source_link,
            **rule_data,
        )
        rules.append(rule)

    return rules


def load_rules_with_overrides(project_root: Path | None = None) -> list[Rule]:
    """Load rules with pyproject.toml overrides applied.

    Args:
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        List of Rule objects with overrides applied
    """
    rules = load_rules(project_root)
    overrides = load_pyproject_toml(project_root)

    # Apply rule overrides from pyproject.toml
    rule_overrides = overrides.get("rules", {})
    if rule_overrides:
        rules_dict = {rule.rule_id: rule for rule in rules}

        for rule_id, override_config in rule_overrides.items():
            if rule_id in rules_dict:
                rule = rules_dict[rule_id]
                # Override enabled status
                if "enabled" in override_config:
                    rule.enabled = override_config["enabled"]
                # Override severity
                if "severity" in override_config:
                    rule.severity = Severity(override_config["severity"].lower())

        rules = list(rules_dict.values())

    return rules


def load_provider_config(project_root: Path | None = None):
    """Load provider configuration from the providers.yaml file.

    Args:
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        ProviderConfig object loaded from the YAML file
    """
    from neoops.providers.models import ProviderConfig

    config_dir = get_config_dir()
    providers_file = config_dir / "providers.yaml"
    data = load_yaml(providers_file)

    return ProviderConfig(
        dangerous=data.get("dangerous", []),
        safe=data.get("safe", []),
        worrying=data.get("worrying", []),
    )


def load_provider_config_with_overrides(project_root: Path | None = None):
    """Load provider configuration with pyproject.toml overrides applied.

    Args:
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        ProviderConfig object with overrides applied
    """
    config = load_provider_config(project_root)
    overrides = load_pyproject_toml(project_root)

    # Apply provider overrides from pyproject.toml
    provider_overrides = overrides.get("providers", {})
    if provider_overrides:
        if "dangerous" in provider_overrides:
            config.dangerous = provider_overrides["dangerous"]
        if "safe" in provider_overrides:
            config.safe = provider_overrides["safe"]
        if "worrying" in provider_overrides:
            config.worrying = provider_overrides["worrying"]

    return config


def load_deprecation_config(project_root: Path | None = None):
    """Load deprecation configuration from the deprecations.yaml file.

    Args:
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        DeprecationConfig object loaded from the YAML file
    """
    from neoops.deprecations.models import (
        DeprecatedModel,
        DeprecationConfig,
        ProviderDeprecationConfig,
    )

    config_dir = get_config_dir()
    deprecations_file = config_dir / "deprecations.yaml"
    data = load_yaml(deprecations_file)

    providers_dict: dict[str, ProviderDeprecationConfig] = {}

    for provider_name, provider_data in data.get("providers", {}).items():
        # Parse deprecated models
        deprecated = []
        deprecated_list = provider_data.get("deprecated")
        if deprecated_list is None or not isinstance(deprecated_list, list):
            deprecated_list = []
        for model_data in deprecated_list:
            # Convert date strings to date objects
            dep_date = model_data.get("deprecation_date")
            ret_date = model_data.get("retirement_date")
            if isinstance(dep_date, str):
                from datetime import datetime

                model_data["deprecation_date"] = datetime.strptime(dep_date, "%Y-%m-%d").date()
            if isinstance(ret_date, str):
                from datetime import datetime

                model_data["retirement_date"] = datetime.strptime(ret_date, "%Y-%m-%d").date()

            # Handle null values
            for key in ["replacement", "notes"]:
                if model_data.get(key) == "null" or model_data.get(key) is None:
                    model_data[key] = None

            deprecated.append(DeprecatedModel(**model_data))

        # Parse legacy models
        legacy = []
        legacy_list = provider_data.get("legacy")
        if legacy_list is None:
            legacy_list = []
        elif not isinstance(legacy_list, list):
            legacy_list = []
        for model_data in legacy_list:
            # Convert date strings to date objects
            dep_date = model_data.get("deprecation_date")
            ret_date = model_data.get("retirement_date")
            if isinstance(dep_date, str):
                from datetime import datetime

                model_data["deprecation_date"] = datetime.strptime(dep_date, "%Y-%m-%d").date()
            if isinstance(ret_date, str):
                from datetime import datetime

                model_data["retirement_date"] = datetime.strptime(ret_date, "%Y-%m-%d").date()

            # Handle null values
            for key in ["replacement", "notes"]:
                if model_data.get(key) == "null" or model_data.get(key) is None:
                    model_data[key] = None

            legacy.append(DeprecatedModel(**model_data))

        providers_dict[provider_name] = ProviderDeprecationConfig(
            provider=provider_data.get("provider", provider_name),
            deprecated=deprecated,
            legacy=legacy,
        )

    return DeprecationConfig(providers=providers_dict)


def load_deprecation_config_with_overrides(project_root: Path | None = None):
    """Load deprecation configuration with pyproject.toml overrides applied.

    Args:
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        DeprecationConfig object with overrides applied
    """
    from neoops.deprecations.models import DeprecatedModel

    config = load_deprecation_config(project_root)
    overrides = load_pyproject_toml(project_root)

    # Apply deprecation overrides from pyproject.toml
    deprecation_overrides = overrides.get("deprecations", {})
    if deprecation_overrides:
        # Merge provider-specific deprecation overrides
        for provider_name, provider_overrides in deprecation_overrides.items():
            if provider_name in config.providers:
                provider_config = config.providers[provider_name]
                # Update deprecated models
                if "deprecated" in provider_overrides:
                    # Parse override models
                    deprecated = []
                    for model_data in provider_overrides["deprecated"]:
                        # Convert date strings if needed
                        if isinstance(model_data.get("deprecation_date"), str):
                            from datetime import datetime

                            model_data["deprecation_date"] = datetime.strptime(
                                model_data["deprecation_date"], "%Y-%m-%d"
                            ).date()
                        if isinstance(model_data.get("retirement_date"), str):
                            from datetime import datetime

                            model_data["retirement_date"] = datetime.strptime(
                                model_data["retirement_date"], "%Y-%m-%d"
                            ).date()
                        deprecated.append(DeprecatedModel(**model_data))
                    provider_config.deprecated = deprecated

                # Update legacy models
                if "legacy" in provider_overrides:
                    legacy = []
                    for model_data in provider_overrides["legacy"]:
                        # Convert date strings if needed
                        if isinstance(model_data.get("deprecation_date"), str):
                            from datetime import datetime

                            model_data["deprecation_date"] = datetime.strptime(
                                model_data["deprecation_date"], "%Y-%m-%d"
                            ).date()
                        if isinstance(model_data.get("retirement_date"), str):
                            from datetime import datetime

                            model_data["retirement_date"] = datetime.strptime(
                                model_data["retirement_date"], "%Y-%m-%d"
                            ).date()
                        legacy.append(DeprecatedModel(**model_data))
                    provider_config.legacy = legacy

    return config
