"""Core Pydantic models for Neops."""

from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity levels for findings."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleConfig(BaseModel):
    """Configuration for a specific rule instance."""

    rule_id: str = Field(..., description="Rule identifier")
    enabled: bool = Field(default=True, description="Whether this rule is enabled")
    severity: Severity = Field(..., description="Severity level for this rule instance")


class Finding(BaseModel):
    """A finding from rule checking."""

    rule_id: str = Field(..., description="ID of the rule that triggered this finding")
    rule_name: str = Field(..., description="Name of the rule that triggered this finding")
    severity: Severity = Field(..., description="Severity of the finding")
    file: Path = Field(..., description="Path to the file where the finding was detected")
    line: int = Field(..., description="Line number where the finding was detected")
    message: str = Field(..., description="Human-readable message describing the finding")
    reasoning: str = Field(..., description="AI-generated reasoning for why this rule applies")
    remediation: Optional[str] = Field(None, description="Suggested remediation steps")


class ScanConfig(BaseModel):
    """Configuration for a scan operation."""

    rules: list[RuleConfig] = Field(..., description="List of rule configurations")
    paths: list[Path] = Field(..., description="Paths to scan")
    exclude: list[str] = Field(default_factory=list, description="Patterns to exclude")


class Findings(BaseModel):
    """Complete findings report model for Neops scan results."""

    summary: dict[str, int] = Field(..., description="Summary counts by severity")
    findings: list[Finding] = Field(..., description="List of all findings")
    config: dict[str, Any] = Field(..., description="Configuration used for the scan")
