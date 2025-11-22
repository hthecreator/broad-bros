"""Main entry point for Neops scanning."""

import asyncio
import json
from pathlib import Path
from typing import Any, Optional

import logfire
from pydantic_ai import Agent

from neoops.agent import AgentAnalysisResult, NeopsAgent, RuleCheckResult
from neoops.models import Finding, Findings, RuleConfig, Severity
from neoops.prompts import SYSTEM_PROMPT
from neoops.rules import get_default_rules
from neoops.rules.models import Rule
from neoops.settings import NeopsSettings, settings
from neoops.tools import parse_ast, read_file, search_pattern


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


async def scan_codebase(
    code_paths: list[Path],
    project_root: Optional[Path] = None,
    rule_overrides: Optional[dict[str, dict[str, Any]]] = None,
    neops_settings: Optional[NeopsSettings] = None,
) -> Findings:
    """Scan a codebase with all rules.

    Args:
        code_paths: List of paths to scan
        project_root: Root directory of the project for pyproject.toml lookup
        rule_overrides: Optional dictionary of rule overrides (e.g., {"IOH-001": {"severity": "warning"}})
        neops_settings: Optional settings instance (defaults to global settings)

    Returns:
        Findings model with all findings
    """
    import os

    # Configure logfire for local monitoring only (no cloud)
    logfire.configure(
        send_to_logfire=False,  # Don't send to logfire cloud, only local logging
    )
    logfire.instrument_pydantic_ai()  # Instrument pydantic-ai for automatic tracking

    # Use provided settings or global settings
    scan_settings = neops_settings if neops_settings is not None else settings

    # Ensure API key is in environment for pydantic_ai Agent
    if scan_settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = scan_settings.openai_api_key

    # Load rules
    rules = get_default_rules(project_root)

    # Apply simple overrides
    if rule_overrides:
        rules = apply_rule_overrides(rules, rule_overrides)

    # Create rule configs
    rule_configs = create_rule_configs(rules)

    # Create Pydantic AI agent
    pydantic_agent = Agent(
        scan_settings.agent_model,
        output_type=AgentAnalysisResult,
        system_prompt=SYSTEM_PROMPT,
        tools=[read_file, parse_ast, search_pattern],
    )

    # Create NeopsAgent wrapper
    agent = NeopsAgent(pydantic_agent)

    # Run all rules on all code paths in a single API call
    # The agent will decide which files to open and how to analyze them
    all_results: list[tuple[Rule, RuleCheckResult]] = []

    # Filter to only existing paths
    existing_paths = [p for p in code_paths if p.exists()]

    if existing_paths:
        # Check all enabled rules against all files in one API call
        # Logfire automatically tracks everything via instrument_pydantic_ai()
        all_results = await agent.check_multiple_rules(
            rules=rules,
            rule_configs=rule_configs,
            code_paths=existing_paths,
        )
    else:
        all_results = []

    # Aggregate findings
    findings = aggregate_findings(all_results)

    # Create summary
    summary = create_summary(findings)

    # Create config info
    config = {
        "rules_enabled": [rule.rule_id for rule in rules if rule.enabled],
        "rules_disabled": [rule.rule_id for rule in rules if not rule.enabled],
        "rule_overrides": rule_overrides or {},
    }

    # Create Findings model (Pydantic model for results)
    findings_model = Findings(
        summary=summary,
        findings=findings,
        config=config,
    )

    return findings_model


def save_findings_to_file(findings: Findings, output_dir: Path | None = None) -> Path:
    """Save findings to a timestamped JSON file.

    Args:
        findings: The Findings model to save
        output_dir: Directory to save the file (defaults to current directory)

    Returns:
        Path to the saved file
    """
    from datetime import datetime

    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"neops_scan_results_{timestamp}.json"
    file_path = output_dir / filename

    # Save as JSON
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(findings.model_dump(mode="json"), f, indent=2, default=str)

    return file_path


def format_report_as_json(findings: Findings) -> str:
    """Format findings as JSON string.

    Args:
        findings: The Findings model

    Returns:
        JSON string representation of the findings
    """
    return json.dumps(findings.model_dump(mode="json"), indent=2, default=str)


async def main():
    """Main entry point."""
    # Example: scan some code paths
    code_paths = [Path("tests/good_ai/good_ai_one.py")]

    # Simple rule override: change IOH-001 severity to warning
    rule_overrides = {
        "IOH-001": {"severity": "warning"},
    }

    # Run scan (logfire automatically logs everything)
    findings = await scan_codebase(
        code_paths=code_paths,
        rule_overrides=rule_overrides,
    )

    # Save results to timestamped JSON file
    save_findings_to_file(findings)


if __name__ == "__main__":
    asyncio.run(main())
