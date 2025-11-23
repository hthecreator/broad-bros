"""Prompts for the Neops AI agent."""

SYSTEM_PROMPT = """You are an AI safety code analyzer. Your job is to analyze code and determine if AI safety rules \
apply.

CRITICAL REQUIREMENT: You MUST check ALL provided rules against ALL provided files. Every rule must be checked against \
every file. This is not optional.

You have access to tools to:
- Read a single file (read_file tool)
- Read multiple files at once (read_files tool) - recommended for efficiency when analyzing multiple files
- Parse a single Python file to AST (parse_ast tool)
- Parse multiple Python files to ASTs at once (parse_asts tool) - recommended for batch analysis
- Search for patterns in a single file (search_pattern tool)
- Search for patterns across multiple files (search_patterns tool) - recommended for searching across all files

You decide the best approach to analyze the code. However, you MUST ensure:
- ALL provided files are examined (no file can be skipped)
- ALL provided rules are checked (every rule must be evaluated)
- Every rule is checked against every file
- You provide a result for EVERY rule, even if it doesn't apply (applies: false)
- For each rule that applies, you identify ALL violations in ALL files where they occur

When analyzing code:
- Use the tools strategically - batch tools (read_files, parse_asts, search_patterns) are available and can be more \
efficient
- A single rule may have violations in multiple files - you must find ALL of them
- Be thorough - missing violations is worse than false positives
- Return structured results with a result for EACH rule provided:
  - rule_id: the rule identifier
  - applies: true if the rule applies to ANY file, false if it applies to NONE
  - violations: list of dicts with 'file' (str), 'line' (int), and 'message' (str) for EACH violation found
  - reasoning: detailed explanation for this specific rule
  - remediation: suggested fixes if applicable for this rule

Remember: ALL files must be checked against ALL rules. Choose the most efficient approach using the available tools."""


def build_rule_check_prompt(
    rule_id: str,
    rule_name: str,
    rule_description: str,
    rule_class: str,
    severity: str,
    code_path: str,
    organization: str = "",
    source_name: str = "",
    source_link: str | None = None,
) -> str:
    """Build a prompt for checking a rule against code.

    Args:
        rule_id: The rule identifier
        rule_name: The rule name
        rule_description: The rule description
        rule_class: The rule class (category)
        severity: The rule severity
        code_path: Path to the code file to analyze
        organization: The organization that defined this rule
        source_name: Name of the source
        source_link: Link to the source

    Returns:
        The formatted prompt string
    """
    source_info = f"Source: {source_name}"
    if source_link:
        source_info += f" ({source_link})"

    org_info = f"Organization: {organization}" if organization else ""

    return f"""Analyze the code at {code_path} to determine if the following AI safety rule applies:

Rule ID: {rule_id}
{org_info}
Name: {rule_name}
Description: {rule_description}
Rule Class: {rule_class}
Severity: {severity}
{source_info}

Use the available tools to:
1. Read and examine the code file
2. Parse the code structure if it's Python
3. Search for relevant patterns related to the rule description
4. Determine if the rule applies and identify specific line numbers where violations occur

Provide your analysis with:
- Whether the rule applies (true/false)
- If it applies, the specific line numbers where violations are found
- Clear reasoning for your conclusion
- Suggested remediation if applicable

Format your response as a structured analysis."""


def build_multi_rule_check_prompt(
    rules: list,
    rule_configs: list,
    code_paths: list[str],
    provider_config=None,
) -> str:
    """Build a prompt for checking multiple rules against multiple code files in one pass.

    Args:
        rules: List of Rule objects to check
        rule_configs: List of RuleConfig objects corresponding to the rules
        code_paths: List of paths to code files to analyze
        provider_config: Optional ProviderConfig for MP and DM rules

    Returns:
        The formatted prompt string
    """
    rules_text = []
    for rule, rule_config in zip(rules, rule_configs, strict=True):
        rule_text = f"""
Rule ID: {rule.rule_id}
Organization: {rule.organization}
Name: {rule.name}
Description: {rule.description}
Rule Class: {rule.rule_class.name} ({rule.rule_class.id})
Severity: {rule_config.severity.value}
Source: {rule.source.name}"""
        if rule.source.link:
            rule_text += f" ({rule.source.link})"
        rules_text.append(rule_text)

    rules_section = "\n".join(rules_text)

    paths_section = "\n".join(f"- {path}" for path in code_paths)

    # Add provider/deprecation context for MP and DM rules
    context_section = ""
    if provider_config:
        # Extract provider information for MP rules
        safe_providers = provider_config.get_safe_providers()
        worrying_providers = provider_config.get_worrying_providers()
        dangerous_providers = provider_config.get_dangerous_providers()

        # Check if we have MP rules
        has_mp_rules = any(rule.rule_class.id == "MP" for rule in rules)

        if has_mp_rules:
            context_section = "\n\nProvider and Model Information:\n"
            context_section += "This information is relevant for Model Provider (MP) rules.\n\n"

            context_section += "Provider Safety Levels:\n"
            if safe_providers:
                context_section += f"  Safe providers: {', '.join(safe_providers)}\n"
            if worrying_providers:
                context_section += f"  Worrying providers: {', '.join(worrying_providers)}\n"
            if dangerous_providers:
                context_section += f"  Dangerous providers: {', '.join(dangerous_providers)}\n"
            context_section += "\n"

    return f"""Analyze the following code files to determine which of the AI safety rules apply.

Code files to analyze:
{paths_section}

Total files: {len(code_paths)}
Total rules: {len(rules)}

CRITICAL REQUIREMENT: You MUST check ALL {len(rules)} rules against ALL {len(code_paths)} files. Every rule must be \
checked against every file. This is not optional.

Rules to check:
{rules_section}{context_section}

You decide the best approach to analyze the code using the available tools. However, you MUST ensure:
- ALL {len(code_paths)} files are examined (no file can be skipped)
- ALL {len(rules)} rules are checked (every rule must be evaluated)
- Every rule is checked against every file
- You provide a result for EVERY rule, even if it doesn't apply (applies: false)
- For each rule that applies, you identify ALL violations in ALL files where they occur

Available tools and recommendations:
- read_file(file_path): Read a single file
- read_files(file_paths): Read multiple files at once - recommended when you need to examine all files
- parse_ast(code, file_path): Parse a single Python file to AST
- parse_asts(files): Parse multiple Python files to ASTs at once - recommended for batch analysis
- search_pattern(code, pattern, file_path): Search for a pattern in a single file
- search_patterns(files, pattern): Search for patterns across multiple files - recommended for searching all files

Choose the most efficient approach, but ensure completeness:
- Use batch tools when you need to process multiple files (more efficient)
- Use single-file tools when you need to focus on specific files
- Whatever approach you choose, you MUST check every rule against every file

IMPORTANT: When you read files using read_file or read_files, the content will include line numbers in the format \
"1: line content", "2: line content", etc.
These line numbers correspond to the actual line numbers in the original file. When reporting violations, use the line \
number shown in the file content (the number before the colon).

For each violation found, provide:
- The exact file path (one of the files listed above)
- The exact line number where the violation occurs (use the line number shown in the file content, e.g., if you see \
"25: def foo():", the line number is 25)
- A clear message explaining the violation
- The violation must be included in the 'violations' list for that rule

Provide a separate result for EACH of the {len(rules)} rules with:
- rule_id: the rule identifier
- applies: true if the rule applies to ANY file, false if it applies to NONE
- violations: list of ALL violations found (each with 'file' (str), 'line' (int), 'message' (str))
- reasoning: detailed explanation for why this rule applies or doesn't apply
- remediation: suggested fixes if the rule applies

Remember: ALL files must be checked against ALL rules. Be thorough and systematic."""
