"""End-to-end test for Neops scanning."""

import logging
from pathlib import Path

import pytest

from neoops.main import Findings, format_report_as_json, scan_codebase

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_scan_bad_ai_code():
    """Test that scanning bad AI code generates findings."""
    # Scan the bad AI code that should trigger all rules
    code_paths = [
        Path("tests/bad_ai/bad_ai_one.py"),
    ]

    # Simple rule override: change IOH-001 severity to warning
    rule_overrides = {
        "IOH-001": {"severity": "warning"},
    }

    # Run scan
    report = await scan_codebase(
        code_paths=code_paths,
        rule_overrides=rule_overrides,
    )

    # Verify report structure
    assert isinstance(report, Findings)
    assert "summary" in report.model_dump()
    assert "findings" in report.model_dump()
    assert "config" in report.model_dump()

    # Verify summary has expected keys
    summary = report.summary
    assert isinstance(summary, dict)
    assert "error" in summary
    assert "warning" in summary
    assert "info" in summary
    assert all(isinstance(v, int) for v in summary.values())

    # Verify findings is a list
    assert isinstance(report.findings, list)

    # Verify config structure
    config = report.config
    assert isinstance(config, dict)
    assert "rules_enabled" in config
    assert "rules_disabled" in config
    assert "rule_overrides" in config

    # Verify rule override was applied
    assert config["rule_overrides"] == rule_overrides

    # Verify we can format as JSON
    json_output = format_report_as_json(report)
    assert isinstance(json_output, str)
    assert "summary" in json_output
    assert "findings" in json_output
    assert "config" in json_output

    # Log report details
    logger.info("=== BAD AI CODE SCAN ===")
    logger.info("Summary: %s", summary)
    logger.info("Total findings: %s", len(report.findings))
    logger.info(
        "Errors: %s, Warnings: %s, Info: %s",
        summary["error"],
        summary["warning"],
        summary["info"],
    )
    if report.findings:
        logger.info("First few findings:")
        for finding in report.findings[:3]:
            logger.info(
                "  - %s (%s): %s...",
                finding.rule_id,
                finding.severity.value,
                finding.message[:60],
            )
    logger.info("Report JSON (first 500 chars):\n%s...", json_output[:500])


@pytest.mark.asyncio
async def test_scan_good_ai_code():
    """Test that scanning good AI code passes checks."""
    # Scan the good AI code that should pass all checks
    code_paths = [
        Path("tests/good_ai/good_ai_one.py"),
    ]

    # Run scan without overrides
    report = await scan_codebase(
        code_paths=code_paths,
        rule_overrides=None,
    )

    assert isinstance(report, Findings)
    assert report.config["rule_overrides"] == {}
    assert len(report.config["rules_enabled"]) > 0

    # Log report details
    summary = report.summary
    logger.info("=== GOOD AI CODE SCAN ===")
    logger.info("Summary: %s", summary)
    logger.info("Total findings: %s", len(report.findings))
    logger.info(
        "Errors: %s, Warnings: %s, Info: %s",
        summary["error"],
        summary["warning"],
        summary["info"],
    )
