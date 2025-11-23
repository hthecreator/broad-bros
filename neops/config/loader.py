"""Configuration loader for Neops that loads from YAML files with pyproject.toml overrides."""

import tomllib
from pathlib import Path
from typing import Any

import yaml

from neops.models import Severity
from neops.rules.models import Rule, RuleClass


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
    """Load rules from the rules.yaml and rule_configuration.yaml files.

    Args:
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        List of Rule objects loaded from the YAML files
    """
    from neops.rules.models import RuleSource

    config_dir = get_config_dir()

    # Load rule configuration (rule classes and organizations)
    config_file = config_dir / "rule_configuration.yaml"
    config_data = load_yaml(config_file)

    # Load rule classes
    rule_classes_map: dict[str, RuleClass] = {}
    for rc_data in config_data.get("rule_classes", []):
        rule_class = RuleClass(**rc_data)
        rule_classes_map[rule_class.id] = rule_class

    # Load rules
    rules_file = config_dir / "rules.yaml"
    rules_data = load_yaml(rules_file)

    rules = []
    for rule_data in rules_data.get("rules", []):
        # Get rule_class from rule_data (it's a string ID)
        rule_class_id = rule_data.pop("rule_class")
        rule_class = rule_classes_map.get(rule_class_id)
        if not rule_class:
            org = rule_data.get("organization")
            code = rule_data.get("code")
            raise ValueError(f"Rule class '{rule_class_id}' not found for rule {org}-{code}")

        # Convert severity string to enum
        severity_str = rule_data.pop("severity", "error")
        severity = Severity(severity_str.lower())

        # Handle source object
        source_data = rule_data.pop("source", {})
        if isinstance(source_data, dict):
            source = RuleSource(
                name=source_data.get("name", ""),
                link=source_data.get("link") if source_data.get("link") not in ["null", None] else None,
            )
        else:
            source = RuleSource(name="", link=None)

        rule = Rule(
            rule_class=rule_class,
            severity=severity,
            source=source,
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
    """Load unified provider configuration from the providers.yaml file.

    Args:
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        ProviderConfig object loaded from the YAML file
    """
    from datetime import datetime

    from neops.providers.models import DeprecatedModel, ProviderConfig, ProviderInfo, ProviderModelConfig

    config_dir = get_config_dir()
    providers_file = config_dir / "providers.yaml"
    data = load_yaml(providers_file)

    providers_dict: dict[str, ProviderInfo] = {}

    for provider_name, provider_data in data.get("providers", {}).items():
        # Parse models
        models_data = provider_data.get("models", {})

        # Parse live models (list of strings)
        live = models_data.get("live", [])
        if not isinstance(live, list):
            live = []

        # Parse deprecated models
        deprecated = []
        deprecated_list = models_data.get("deprecated", [])
        if not isinstance(deprecated_list, list):
            deprecated_list = []
        for model_data in deprecated_list:
            # Convert date strings to date objects
            dep_date = model_data.get("deprecation_date")
            ret_date = model_data.get("retirement_date")
            if isinstance(dep_date, str):
                model_data["deprecation_date"] = datetime.strptime(dep_date, "%Y-%m-%d").date()
            if isinstance(ret_date, str):
                model_data["retirement_date"] = datetime.strptime(ret_date, "%Y-%m-%d").date()

            # Handle null values
            for key in ["replacement", "notes"]:
                if model_data.get(key) in ["null", None]:
                    model_data[key] = None

            deprecated.append(DeprecatedModel(**model_data))

        # Parse legacy models
        legacy = []
        legacy_list = models_data.get("legacy", [])
        if not isinstance(legacy_list, list):
            legacy_list = []
        for model_data in legacy_list:
            # Convert date strings to date objects
            dep_date = model_data.get("deprecation_date")
            ret_date = model_data.get("retirement_date")
            if isinstance(dep_date, str):
                model_data["deprecation_date"] = datetime.strptime(dep_date, "%Y-%m-%d").date()
            if isinstance(ret_date, str):
                model_data["retirement_date"] = datetime.strptime(ret_date, "%Y-%m-%d").date()

            # Handle null values
            for key in ["replacement", "notes"]:
                if model_data.get(key) in ["null", None]:
                    model_data[key] = None

            legacy.append(DeprecatedModel(**model_data))

        providers_dict[provider_name] = ProviderInfo(
            provider=provider_name,
            safety_level=provider_data.get("safety_level", "safe"),
            models=ProviderModelConfig(
                live=live,
                deprecated=deprecated,
                legacy=legacy,
            ),
        )

    return ProviderConfig(providers=providers_dict)


def load_provider_config_with_overrides(project_root: Path | None = None):
    """Load provider configuration with pyproject.toml overrides applied.

    Args:
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        ProviderConfig object with overrides applied
    """
    from datetime import datetime

    from neops.providers.models import DeprecatedModel

    config = load_provider_config(project_root)
    overrides = load_pyproject_toml(project_root)

    # Apply provider overrides from pyproject.toml
    provider_overrides = overrides.get("providers", {})
    if provider_overrides:
        for provider_name, provider_override in provider_overrides.items():
            if provider_name in config.providers:
                provider_info = config.providers[provider_name]

                # Override safety level
                if "safety_level" in provider_override:
                    provider_info.safety_level = provider_override["safety_level"]

                # Override models
                if "models" in provider_override:
                    models_override = provider_override["models"]

                    # Override live models
                    if "live" in models_override:
                        provider_info.models.live = models_override["live"]

                    # Override deprecated models
                    if "deprecated" in models_override:
                        deprecated = []
                        for model_data in models_override["deprecated"]:
                            # Convert date strings if needed
                            if isinstance(model_data.get("deprecation_date"), str):
                                model_data["deprecation_date"] = datetime.strptime(
                                    model_data["deprecation_date"], "%Y-%m-%d"
                                ).date()
                            if isinstance(model_data.get("retirement_date"), str):
                                model_data["retirement_date"] = datetime.strptime(
                                    model_data["retirement_date"], "%Y-%m-%d"
                                ).date()
                            # Handle null values
                            for key in ["replacement", "notes"]:
                                if model_data.get(key) in ["null", None]:
                                    model_data[key] = None
                            deprecated.append(DeprecatedModel(**model_data))
                        provider_info.models.deprecated = deprecated

                    # Override legacy models
                    if "legacy" in models_override:
                        legacy = []
                        for model_data in models_override["legacy"]:
                            # Convert date strings if needed
                            if isinstance(model_data.get("deprecation_date"), str):
                                model_data["deprecation_date"] = datetime.strptime(
                                    model_data["deprecation_date"], "%Y-%m-%d"
                                ).date()
                            if isinstance(model_data.get("retirement_date"), str):
                                model_data["retirement_date"] = datetime.strptime(
                                    model_data["retirement_date"], "%Y-%m-%d"
                                ).date()
                            # Handle null values
                            for key in ["replacement", "notes"]:
                                if model_data.get(key) in ["null", None]:
                                    model_data[key] = None
                            legacy.append(DeprecatedModel(**model_data))
                        provider_info.models.legacy = legacy

    return config


def load_deprecation_config(project_root: Path | None = None):
    """Load deprecation configuration (deprecated - use load_provider_config instead).

    This function is kept for backward compatibility but now uses the unified provider config.

    Args:
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        DeprecationConfig object (converted from ProviderConfig)
    """
    from neops.deprecations.models import DeprecationConfig, ProviderDeprecationConfig

    # Use unified provider config
    provider_config = load_provider_config(project_root)

    # Convert to old DeprecationConfig format for backward compatibility
    providers_dict: dict[str, ProviderDeprecationConfig] = {}
    for provider_name, provider_info in provider_config.providers.items():
        # Convert DeprecatedModel instances to dicts so Pydantic can recreate them
        # as the correct DeprecatedModel type (from neops.deprecations.models)
        deprecated_dicts = [model.model_dump() for model in provider_info.models.deprecated]
        legacy_dicts = [model.model_dump() for model in provider_info.models.legacy]

        providers_dict[provider_name] = ProviderDeprecationConfig(
            provider=provider_name,
            deprecated=deprecated_dicts,
            legacy=legacy_dicts,
        )

    return DeprecationConfig(providers=providers_dict)


def load_deprecation_config_with_overrides(project_root: Path | None = None):
    """Load deprecation configuration with pyproject.toml overrides applied.

    This function is kept for backward compatibility but now uses the unified provider config.

    Args:
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        DeprecationConfig object (converted from ProviderConfig)
    """
    from neops.deprecations.models import DeprecationConfig, ProviderDeprecationConfig

    # Use unified provider config with overrides
    provider_config = load_provider_config_with_overrides(project_root)

    # Convert to old DeprecationConfig format for backward compatibility
    providers_dict: dict[str, ProviderDeprecationConfig] = {}
    for provider_name, provider_info in provider_config.providers.items():
        # Convert DeprecatedModel instances to dicts so Pydantic can recreate them
        # as the correct DeprecatedModel type (from neops.deprecations.models)
        deprecated_dicts = [model.model_dump() for model in provider_info.models.deprecated]
        legacy_dicts = [model.model_dump() for model in provider_info.models.legacy]

        providers_dict[provider_name] = ProviderDeprecationConfig(
            provider=provider_name,
            deprecated=deprecated_dicts,
            legacy=legacy_dicts,
        )

    return DeprecationConfig(providers=providers_dict)
