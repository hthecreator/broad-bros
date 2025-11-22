"""Pydantic models for rules."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity levels for findings."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleClass(BaseModel):
    """Definition of a rule class (e.g., IOH, MP, DM)."""

    id: str = Field(..., description="Unique identifier for the rule class (e.g., 'IOH')")
    name: str = Field(..., description="Human-readable name of the rule class")
    description: str = Field(..., description="Description of what this rule class covers")


class Rule(BaseModel):
    """Definition of an AI safety rule."""

    rule_id: str = Field(..., description="Unique identifier for the rule (e.g., IOH-001)")
    rule_class: RuleClass = Field(..., description="The rule class this rule belongs to")
    name: str = Field(..., description="Human-readable name of the rule")
    description: str = Field(..., description="Detailed description of what the rule checks")
    category: str = Field(..., description="Category of the rule (e.g., 'output_handling', 'guardrails')")
    severity: Severity = Field(default=Severity.ERROR, description="Default severity level")
    enabled: bool = Field(default=True, description="Whether the rule is enabled")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering rules")
    source_framework: Optional[str] = Field(None, description="Framework or standard this rule is based on")
    source_link: Optional[str] = Field(None, description="URL or reference link to the source of this rule")
