"""Report generation for Neops scan results."""

from datetime import datetime
from pathlib import Path

from neops.models import Finding, Findings, Severity


def format_findings_as_markdown(findings: Findings) -> str:
    """Format findings as Markdown report.

    Args:
        findings: The Findings model

    Returns:
        Markdown string representation of the findings
    """
    md_lines = []

    # Header
    md_lines.append("# Neops Security Scan Report")
    md_lines.append("")
    md_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_lines.append("")

    # Summary
    md_lines.append("## Summary")
    md_lines.append("")
    summary = findings.summary
    md_lines.append(f"- **Errors:** {summary.get('error', 0)}")
    md_lines.append(f"- **Warnings:** {summary.get('warning', 0)}")
    md_lines.append(f"- **Info:** {summary.get('info', 0)}")
    md_lines.append(f"- **Total Findings:** {len(findings.findings)}")
    md_lines.append("")

    # Configuration
    md_lines.append("## Configuration")
    md_lines.append("")
    config = findings.config
    md_lines.append(f"- **Rules Enabled:** {len(config.get('rules_enabled', []))}")
    md_lines.append(f"- **Rules Disabled:** {len(config.get('rules_disabled', []))}")
    md_lines.append("")

    if config.get("rules_enabled"):
        md_lines.append("### Enabled Rules")
        for rule_id in config["rules_enabled"]:
            md_lines.append(f"- `{rule_id}`")
        md_lines.append("")

    # Findings by severity
    if findings.findings:
        md_lines.append("## Findings")
        md_lines.append("")

        # Group by severity
        errors = [f for f in findings.findings if f.severity == Severity.ERROR]
        warnings = [f for f in findings.findings if f.severity == Severity.WARNING]
        info = [f for f in findings.findings if f.severity == Severity.INFO]

        if errors:
            md_lines.append("### 🔴 Errors")
            md_lines.append("")
            for finding in errors:
                md_lines.append(format_finding_markdown(finding))
                md_lines.append("")

        if warnings:
            md_lines.append("### 🟡 Warnings")
            md_lines.append("")
            for finding in warnings:
                md_lines.append(format_finding_markdown(finding))
                md_lines.append("")

        if info:
            md_lines.append("### 🔵 Info")
            md_lines.append("")
            for finding in info:
                md_lines.append(format_finding_markdown(finding))
                md_lines.append("")
    else:
        md_lines.append("## Findings")
        md_lines.append("")
        md_lines.append("✅ No findings detected. Your code appears to be secure!")
        md_lines.append("")

    return "\n".join(md_lines)


def format_finding_markdown(finding: Finding) -> str:
    """Format a single finding as Markdown.

    Args:
        finding: The Finding to format

    Returns:
        Markdown string for the finding
    """
    lines = []
    severity_emoji = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(finding.severity.value, "⚪")

    lines.append(f"#### {severity_emoji} {finding.rule_id} - {finding.rule_name} ({finding.severity.value.upper()})")
    lines.append("")
    lines.append(f"**File:** `{finding.file}`")
    lines.append(f"**Line:** {finding.line}")
    lines.append(f"**Message:** {finding.message}")
    lines.append("")

    if finding.reasoning:
        lines.append("**Reasoning:**")
        lines.append("")
        lines.append(f"> {finding.reasoning}")
        lines.append("")

    if finding.remediation:
        lines.append("**Remediation:**")
        lines.append("")
        lines.append(f"> {finding.remediation}")
        lines.append("")

    return "\n".join(lines)


def save_findings_as_markdown(findings: Findings, output_dir: Path | None = None) -> Path:
    """Save findings to a timestamped Markdown file.

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
    filename = f"neops_scan_results_{timestamp}.md"
    file_path = output_dir / filename

    # Save as Markdown
    markdown_content = format_findings_as_markdown(findings)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return file_path
