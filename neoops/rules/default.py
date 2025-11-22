"""Default rules loaded from YAML configuration."""

from pathlib import Path
from typing import Optional

from neoops.config.loader import load_rules, load_rules_with_overrides
from neoops.rules.models import Rule

# Cache for default rules (loaded on first access)
_default_rules_cache: Optional[list[Rule]] = None


def get_default_rules(project_root: Optional[Path] = None) -> list[Rule]:
    """Get the default list of rules, with pyproject.toml overrides applied.

    Args:
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        List of default Rule objects
    """
    return load_rules_with_overrides(project_root)


def _get_default_rules_cached() -> list[Rule]:
    """Get cached default rules, loading if necessary."""
    global _default_rules_cache
    if _default_rules_cache is None:
        _default_rules_cache = load_rules()
    return _default_rules_cache.copy()


# For backward compatibility, DEFAULT_RULES loads from YAML only (no overrides)
# Users should use get_default_rules() for pyproject.toml overrides
DEFAULT_RULES = _get_default_rules_cached()


def get_rule_by_id(rule_id: str, project_root: Optional[Path] = None) -> Rule | None:
    """Get a rule by its ID.

    Args:
        rule_id: The rule identifier (e.g., 'IOH-001')
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        The Rule object if found, None otherwise
    """
    rules = get_default_rules(project_root)
    for rule in rules:
        if rule.rule_id == rule_id:
            return rule
    return None


def get_rules_by_class(rule_class_id: str, project_root: Optional[Path] = None) -> list[Rule]:
    """Get all rules for a specific rule class.

    Args:
        rule_class_id: The rule class identifier (e.g., 'IOH')
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        List of Rule objects for the specified class
    """
    rules = get_default_rules(project_root)
    return [rule for rule in rules if rule.rule_class.id == rule_class_id]
