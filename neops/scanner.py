"""Core scanning functionality for Neops."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import logfire
from pydantic_ai import Agent

from neops.agent import AgentAnalysisResult, NeopsAgent, RuleCheckResult
from neops.cli_utils import aggregate_findings, apply_rule_overrides, create_rule_configs, create_summary
from neops.models import Findings
from neops.prompts import SYSTEM_PROMPT
from neops.rules import get_default_rules
from neops.rules.models import Rule
from neops.settings import NeopsSettings, settings
from neops.tools import parse_ast, parse_asts, read_file, read_files, search_pattern, search_patterns


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

    # Create Pydantic AI agent with batch tools
    pydantic_agent = Agent(
        scan_settings.agent_model,
        output_type=AgentAnalysisResult,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            read_file,  # Single file read
            read_files,  # Batch file read - RECOMMENDED
            parse_ast,  # Single file AST
            parse_asts,  # Batch AST - RECOMMENDED
            search_pattern,  # Single file search
            search_patterns,  # Batch search - RECOMMENDED
        ],
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
