"""Core scanning functionality for Neops."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import logfire
from pydantic_ai import Agent

from neops.agent import AgentAnalysisResult, NeopsAgent
from neops.cli_utils import aggregate_findings, create_rule_configs, create_summary
from neops.config.loader import load_provider_config_with_overrides
from neops.models import Findings
from neops.prompts import SYSTEM_PROMPT
from neops.providers.models import ProviderConfig
from neops.report import save_findings_as_markdown
from neops.rules import get_default_rules
from neops.settings import settings
from neops.tools import parse_ast, parse_asts, read_file, read_files, search_pattern, search_patterns


async def scan_codebase(
    code_paths: list[Path],
    project_root: Optional[Path] = None,
) -> Findings:
    """Scan a codebase with all rules.

    Rules are loaded from YAML configuration with pyproject.toml overrides applied automatically.
    To override rules, add a [tool.neops.rules] section to your pyproject.toml.

    Args:
        code_paths: List of paths to scan
        project_root: Root directory of the project for pyproject.toml lookup

    Returns:
        Findings model with all findings
    """
    # Configure logfire for local monitoring only (no cloud)
    logfire.configure(
        send_to_logfire=False,  # Don't send to logfire cloud, only local logging
    )
    logfire.instrument_pydantic_ai()  # Instrument pydantic-ai for automatic tracking

    # Ensure API key is in environment for pydantic_ai Agent
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key

    # Load rules (pyproject.toml overrides are automatically applied via get_default_rules)
    rules = get_default_rules(project_root)

    # Create rule configs
    rule_configs = create_rule_configs(rules)

    # Load provider configuration (needed for MP and DM rules)
    provider_config: ProviderConfig | None = None
    try:
        provider_config = load_provider_config_with_overrides(project_root)
    except Exception:
        # If provider config can't be loaded, continue without it
        provider_config = None

    # Create Pydantic AI agent with batch tools
    pydantic_agent = Agent(
        settings.agent_model,
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

    # Filter to only existing paths
    existing_paths = [p for p in code_paths if p.exists()]

    if existing_paths:
        # Run agent per organization (groups rules by organization and runs separately)
        # Logfire automatically tracks everything via instrument_pydantic_ai()
        all_results = await agent.check_rules_by_organization(
            rules=rules,
            rule_configs=rule_configs,
            code_paths=existing_paths,
            provider_config=provider_config,
        )
    else:
        all_results = []

    # Aggregate findings
    findings = aggregate_findings(all_results)

    # Create summary
    summary = create_summary(findings)

    # Create config info
    # Load pyproject.toml to get rule overrides that were applied
    rule_overrides_applied = {}
    try:
        from neops.config.loader import load_pyproject_toml

        overrides = load_pyproject_toml(project_root)
        rule_overrides_applied = overrides.get("rules", {})
    except Exception:
        # If we can't load pyproject.toml, that's okay - rules were still loaded
        pass

    config = {
        "rules_enabled": [rule.rule_id for rule in rules if rule.enabled],
        "rules_disabled": [rule.rule_id for rule in rules if not rule.enabled],
        "rule_overrides": rule_overrides_applied,
    }

    # Create Findings model (Pydantic model for results)
    findings_model = Findings(
        summary=summary,
        findings=findings,
        config=config,
    )

    return findings_model


def save_findings_to_file(findings: Findings, output_dir: Path | None = None) -> dict[str, Path]:
    """Save findings to timestamped JSON and Markdown files.

    Args:
        findings: The Findings model to save
        output_dir: Directory to save the files (defaults to current directory)

    Returns:
        Dictionary with keys 'json' and 'markdown' and their file paths
    """
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save as JSON
    json_filename = f"neops_scan_results_{timestamp}.json"
    json_path = output_dir / json_filename
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(findings.model_dump(mode="json"), f, indent=2, default=str)

    # Save as Markdown
    md_path = save_findings_as_markdown(findings, output_dir)

    return {"json": json_path, "markdown": md_path}


def format_report_as_json(findings: Findings) -> str:
    """Format findings as JSON string.

    Args:
        findings: The Findings model

    Returns:
        JSON string representation of the findings
    """
    return json.dumps(findings.model_dump(mode="json"), indent=2, default=str)
