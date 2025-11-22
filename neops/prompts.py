"""Prompts for the Neops AI agent."""

SYSTEM_PROMPT = """You are an AI safety code analyzer. Your job is to analyze code and determine if AI safety rules \
apply.

You have access to tools to:
- Read files and examine their contents (read_file tool)
- Parse Python code into ASTs to understand structure (parse_ast tool)
- Search for specific patterns in code (search_pattern tool)

When analyzing code:
1. You will be given multiple code files and multiple rules to check
2. Use the tools strategically - decide which files to read based on the rules
3. You may not need to read all files for all rules - be efficient
4. Check ALL provided rules against ALL provided files in a single analysis pass
5. For each rule, determine if it applies to any file and identify specific file paths and line numbers where \
violations occur
6. Provide clear reasoning for each rule's findings
7. If a rule applies, create findings with:
   - The exact file path where the issue occurs
   - The exact line number(s) where the issue occurs
   - A clear message explaining the issue
   - Reasoning for why this violates the rule
   - Suggested remediation if applicable

Be thorough and precise in your analysis. When checking multiple rules across multiple files:
- Read file content efficiently - only read files that are relevant to the rules
- Analyze code structure once per file and apply all relevant rules to it
- A single rule may have violations in multiple files - include all of them
- Return structured results with a result for EACH rule provided:
  - rule_id: the rule identifier
  - applies: true if the rule applies to any file, false otherwise
  - violations: list of dicts with 'file' (str), 'line' (int), and 'message' (str) for each violation
  - reasoning: detailed explanation for this specific rule
  - remediation: suggested fixes if applicable for this rule"""


def build_rule_check_prompt(
    rule_id: str, rule_name: str, rule_description: str, category: str, severity: str, code_path: str
) -> str:
    """Build a prompt for checking a rule against code.

    Args:
        rule_id: The rule identifier
        rule_name: The rule name
        rule_description: The rule description
        category: The rule category
        severity: The rule severity
        code_path: Path to the code file to analyze

    Returns:
        The formatted prompt string
    """
    return f"""Analyze the code at {code_path} to determine if the following AI safety rule applies:

Rule ID: {rule_id}
Name: {rule_name}
Description: {rule_description}
Category: {category}
Severity: {severity}

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


def build_multi_rule_check_prompt(rules: list, rule_configs: list, code_paths: list[str]) -> str:
    """Build a prompt for checking multiple rules against multiple code files in one pass.

    Args:
        rules: List of Rule objects to check
        rule_configs: List of RuleConfig objects corresponding to the rules
        code_paths: List of paths to code files to analyze

    Returns:
        The formatted prompt string
    """
    rules_text = []
    for rule, rule_config in zip(rules, rule_configs, strict=True):
        rules_text.append(
            f"""
Rule ID: {rule.rule_id}
Name: {rule.name}
Description: {rule.description}
Category: {rule.category}
Severity: {rule_config.severity.value}
Rule Class: {rule.rule_class.name} ({rule.rule_class.id})
"""
        )

    rules_section = "\n".join(rules_text)

    paths_section = "\n".join(f"- {path}" for path in code_paths)

    return f"""Analyze the following code files to determine which of the AI safety rules apply.

Code files to analyze:
{paths_section}

You need to check ALL of these rules against ALL of these files in a single analysis pass:

{rules_section}

Use the available tools to:
1. Read and examine the code files as needed (use read_file tool for each file you need to analyze)
2. Parse the code structure if needed (use parse_ast for Python files)
3. Search for patterns across files if needed (use search_pattern)
4. For EACH rule above, determine if it applies to ANY of the code files
5. Identify specific file paths and line numbers where violations occur for each applicable rule

IMPORTANT:
- You have access to multiple files - decide which ones to open based on the rules
- Read file content efficiently - you may not need to read all files for all rules
- Analyze code structure once per file and apply all relevant rules to it
- Check every rule against every file - some rules may apply to some files, not others
- For each violation, specify which file it's in (include the file path in the violation)
- Provide a separate result for EACH rule with:
  - Whether that specific rule applies to any file (true/false)
  - If it applies, the specific file paths and line numbers where violations are found
    (each violation should include 'file' (str), 'line' (int), and 'message' (str))
  - Clear reasoning for that rule
  - Suggested remediation if applicable for that rule

Format your response as a structured analysis with results for each rule. Each rule result may contain violations \
across multiple files."""
