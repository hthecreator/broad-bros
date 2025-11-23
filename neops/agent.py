"""Neops AI agent using Pydantic AI for rule checking."""

import asyncio
from pathlib import Path

import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from neops.models import Finding, RuleConfig
from neops.prompts import SYSTEM_PROMPT, build_multi_rule_check_prompt
from neops.rules.models import Rule
from neops.settings import settings
from neops.tools import parse_ast, parse_asts, read_file, read_files, search_pattern, search_patterns


class RuleCheckInput(BaseModel):
    """Input for checking a rule against code."""

    rule: Rule = Field(..., description="The rule to check")
    code_path: Path = Field(..., description="Path to the code file to check")
    rule_config: RuleConfig = Field(..., description="Configuration for this rule instance")


class RuleCheckResult(BaseModel):
    """Result of checking a rule."""

    applies: bool = Field(..., description="Whether the rule applies to this code")
    findings: list[Finding] = Field(default_factory=list, description="List of findings if the rule applies")
    reasoning: str = Field(..., description="Explanation of why the rule applies or doesn't apply")


class AgentAnalysisResult(BaseModel):
    """Structured result from the AI agent analysis."""

    applies: bool = Field(..., description="Whether the rule applies")
    violations: list[dict[str, int | str]] = Field(
        default_factory=list,
        description="List of violations with line numbers and descriptions",
    )
    reasoning: str = Field(..., description="Detailed reasoning for the analysis")
    remediation: str | None = Field(None, description="Suggested remediation steps")


class RuleAnalysisResult(BaseModel):
    """Result for a single rule check within a multi-rule analysis."""

    rule_id: str = Field(..., description="The rule ID that was checked")
    applies: bool = Field(..., description="Whether the rule applies")
    violations: list[dict[str, int | str]] = Field(
        default_factory=list,
        description=(
            "List of violations with line numbers and descriptions. "
            "Each violation should include 'file' (str), 'line' (int), and 'message' (str)."
        ),
    )
    reasoning: str = Field(..., description="Detailed reasoning for this rule")
    remediation: str | None = Field(None, description="Suggested remediation steps for this rule")


class MultiRuleAnalysisResult(BaseModel):
    """Structured result from the AI agent analyzing multiple rules against multiple files at once."""

    rule_results: list[RuleAnalysisResult] = Field(
        ...,
        description="Analysis results for each rule checked. Each result may contain violations across multiple files.",
    )
    overall_reasoning: str = Field(..., description="Overall reasoning about the code analysis across all files")


class NeopsAgent:
    """Global AI agent for Neops rule checking."""

    def __init__(self, agent: Agent):
        """Initialize the Neops agent.

        Args:
            agent: The Pydantic AI agent to use
        """
        self.agent = agent
        # Create a reusable multi-rule agent to avoid tool registration conflicts
        # when check_multiple_rules is called multiple times (e.g., in parallel for different organizations)
        self.multi_rule_agent = Agent(
            settings.agent_model,
            output_type=MultiRuleAnalysisResult,
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

    async def check_multiple_rules(
        self,
        rules: list[Rule],
        rule_configs: list[RuleConfig],
        code_paths: list[Path],
        provider_config=None,
        organization: str | None = None,
    ) -> list[tuple[Rule, RuleCheckResult]]:
        """Check multiple rules against multiple code files in one pass.

        Args:
            rules: List of rules to check
            rule_configs: List of rule configs corresponding to the rules
            code_paths: List of paths to code files to analyze
            provider_config: Optional ProviderConfig for MP and DM rules

        Returns:
            List of tuples (rule, result) for each rule checked.
            Each result may contain findings across multiple files.
        """
        # Filter to only enabled rules
        enabled_rules_and_configs = [
            (rule, rule_config)
            for rule, rule_config in zip(rules, rule_configs, strict=True)
            if rule.enabled and rule_config.enabled
        ]

        if not enabled_rules_and_configs:
            return []

        # Filter to only existing paths
        existing_paths = [p for p in code_paths if p.exists()]
        if not existing_paths:
            return []

        enabled_rules, enabled_configs = zip(*enabled_rules_and_configs, strict=True)

        # Extract metadata for logging
        rule_ids = [rule.rule_id for rule in enabled_rules]
        organizations = list(set(rule.organization for rule in enabled_rules))
        code_paths_str = [str(p) for p in existing_paths]

        # Use provided organization or derive from rules
        org_str = organization if organization else (", ".join(organizations) if organizations else "unknown")

        # Build prompt with all rules and all code paths
        prompt = build_multi_rule_check_prompt(
            rules=list(enabled_rules),
            rule_configs=list(enabled_configs),
            code_paths=code_paths_str,
            provider_config=provider_config,
        )

        # Use the reusable multi-rule agent (created once in __init__ to avoid tool registration conflicts)
        # Run the agent with logfire span that includes metadata
        # Include org in span name to make it visible in nested logs
        # This will wrap the automatic pydantic-ai instrumentation
        span_name = f"check_multiple_rules:{org_str}" if organization else "check_multiple_rules"
        with logfire.span(
            span_name,
            organization=org_str,
            rule_ids=rule_ids,
            rule_count=len(rule_ids),
            file_paths=code_paths_str,
            file_count=len(code_paths_str),
        ):
            result = await self.multi_rule_agent.run(prompt)

        # Extract structured result
        if isinstance(result.output, MultiRuleAnalysisResult):
            analysis = result.output
        else:
            # Fallback: create empty results
            analysis = MultiRuleAnalysisResult(
                rule_results=[],
                overall_reasoning=str(result.output) if result.output else "No analysis provided",
            )

        # Convert to RuleCheckResult for each rule
        # Each rule result may have violations across multiple files
        results = []
        rule_results_map = {r.rule_id: r for r in analysis.rule_results}

        # Create a mapping of file paths for lookup
        path_map = {str(p): p for p in existing_paths}

        for rule, rule_config in zip(enabled_rules, enabled_configs, strict=True):
            rule_result = rule_results_map.get(rule.rule_id)
            if rule_result:
                # Convert violations to findings
                findings = []
                for violation in rule_result.violations:
                    # Get file path from violation, default to first path if not specified
                    file_path_str = violation.get("file")
                    if file_path_str and file_path_str in path_map:
                        file_path = path_map[file_path_str]
                    else:
                        # If file not specified, try to infer from context or use first file
                        file_path = existing_paths[0]

                    line = violation.get("line", 1)
                    message = violation.get("message", rule.description)
                    findings.append(
                        Finding(
                            rule_id=rule.rule_id,
                            rule_name=rule.name,
                            severity=rule_config.severity,
                            file=file_path,
                            line=int(line) if isinstance(line, (int, str)) else 1,
                            message=message,
                            reasoning=rule_result.reasoning,
                            remediation=rule_result.remediation,
                        )
                    )

                results.append(
                    (
                        rule,
                        RuleCheckResult(
                            applies=rule_result.applies,
                            findings=findings,
                            reasoning=rule_result.reasoning,
                        ),
                    )
                )
            else:
                # Rule was checked but no result found (shouldn't happen, but handle gracefully)
                results.append(
                    (
                        rule,
                        RuleCheckResult(
                            applies=False,
                            findings=[],
                            reasoning=f"No analysis result found for {rule.rule_id}",
                        ),
                    )
                )

        return results

    async def check_rules_by_organization(
        self,
        rules: list[Rule],
        rule_configs: list[RuleConfig],
        code_paths: list[Path],
        provider_config=None,
    ) -> list[tuple[Rule, RuleCheckResult]]:
        """Check rules grouped by organization (runs agent separately for each organization).

        Args:
            rules: List of rules to check
            rule_configs: List of rule configs corresponding to the rules
            code_paths: List of paths to code files to analyze
            provider_config: Optional ProviderConfig for MP and DM rules

        Returns:
            List of tuples (rule, result) for each rule checked.
            Each result may contain findings across multiple files.
        """
        # Group rules by organization
        from collections import defaultdict

        org_rules: dict[str, list[tuple[Rule, RuleConfig]]] = defaultdict(list)
        for rule, rule_config in zip(rules, rule_configs, strict=True):
            if rule.enabled and rule_config.enabled:
                org_rules[rule.organization].append((rule, rule_config))

        # Run agent separately for each organization in parallel
        async def check_org(
            organization: str, org_rule_configs: list[tuple[Rule, RuleConfig]]
        ) -> list[tuple[Rule, RuleCheckResult]]:
            """Check rules for a single organization."""
            org_rules_list, org_configs_list = zip(*org_rule_configs, strict=True)
            rule_ids = [rule.rule_id for rule in org_rules_list]

            # Wrap with logfire span to identify this organization's run
            # Include org in span name to make it visible in logs and trackable through nested spans
            with logfire.span(
                f"check_organization:{organization}",
                organization=organization,
                rule_ids=rule_ids,
                rule_count=len(rule_ids),
                file_count=len(code_paths),
            ):
                return await self.check_multiple_rules(
                    rules=list(org_rules_list),
                    rule_configs=list(org_configs_list),
                    code_paths=code_paths,
                    provider_config=provider_config,
                    organization=organization,  # Pass org to nested function
                )

        # Create tasks for all organizations
        tasks = [check_org(organization, org_rule_configs) for organization, org_rule_configs in org_rules.items()]

        # Run all organization checks in parallel
        org_results_list = await asyncio.gather(*tasks)

        # Flatten results from all organizations
        all_results: list[tuple[Rule, RuleCheckResult]] = []
        for org_results in org_results_list:
            all_results.extend(org_results)

        return all_results
