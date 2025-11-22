"""CLI utility functions for Neops."""

from typing import Any

from neops.agent import RuleCheckResult
from neops.models import Finding, RuleConfig, Severity
from neops.rules.models import Rule


def apply_rule_overrides(rules: list[Rule], overrides: dict[str, dict[str, Any]]) -> list[Rule]:
    """Apply simple rule overrides to rules.

    Args:
        rules: List of rules to apply overrides to
        overrides: Dictionary mapping rule_id to override config (e.g., {"IOH-001": {"severity": "warning"}})

    Returns:
        List of rules with overrides applied
    """
    rules_dict = {rule.rule_id: rule for rule in rules}

    for rule_id, override_config in overrides.items():
        if rule_id in rules_dict:
            rule = rules_dict[rule_id]
            # Override severity if specified
            if "severity" in override_config:
                rule.severity = Severity(override_config["severity"].lower())
            # Override enabled if specified
            if "enabled" in override_config:
                rule.enabled = override_config["enabled"]

    return list(rules_dict.values())


def create_rule_configs(rules: list[Rule]) -> list[RuleConfig]:
    """Create RuleConfig objects from rules.

    Args:
        rules: List of rules

    Returns:
        List of RuleConfig objects
    """
    return [
        RuleConfig(
            rule_id=rule.rule_id,
            enabled=rule.enabled,
            severity=rule.severity,
        )
        for rule in rules
    ]


def aggregate_findings(all_results: list[tuple[Rule, RuleCheckResult]]) -> list[Finding]:
    """Aggregate findings from all rule check results.

    Args:
        all_results: List of tuples of (rule, RuleCheckResult)

    Returns:
        List of all findings
    """
    findings = []
    for _, result in all_results:
        findings.extend(result.findings)
    return findings


def create_summary(findings: list[Finding]) -> dict[str, int]:
    """Create summary statistics from findings.

    Args:
        findings: List of findings

    Returns:
        Dictionary with counts by severity
    """
    summary = {"error": 0, "warning": 0, "info": 0}
    for finding in findings:
        severity = finding.severity.value
        summary[severity] = summary.get(severity, 0) + 1
    return summary
