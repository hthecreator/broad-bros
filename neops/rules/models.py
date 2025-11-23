"""Pydantic models for rules."""

from typing import Optional

from pydantic import BaseModel, Field, computed_field

from neops.models import Severity


class RuleClass(BaseModel):
    """Definition of a rule class (e.g., IOH, MP, DM)."""

    id: str = Field(..., description="Unique identifier for the rule class (e.g., 'IOH')")
    name: str = Field(..., description="Human-readable name of the rule class")
    description: str = Field(..., description="Description of what this rule class covers")


class RuleSource(BaseModel):
    """Source information for a rule."""

    name: str = Field(..., description="Name of the source organization or framework")
    link: Optional[str] = Field(None, description="URL or reference link to the source")


class Rule(BaseModel):
    """Definition of an AI safety rule."""

    organization: str = Field(
        ..., description="Organization/guideline source (e.g., 'OWASP', 'NEOps', 'OpenAI', 'Anthropic')"
    )
    code: str = Field(..., description="Rule code within the organization (e.g., '001', '002')")
    rule_class: RuleClass = Field(..., description="The rule class this rule belongs to (this is the category)")
    name: str = Field(..., description="Human-readable name of the rule")
    description: str = Field(..., description="Detailed description of what the rule checks")
    severity: Severity = Field(default=Severity.ERROR, description="Default severity level")
    enabled: bool = Field(default=True, description="Whether the rule is enabled")
    source: RuleSource = Field(..., description="Source information for this rule")

    @computed_field
    @property
    def rule_id(self) -> str:
        """Auto-generated rule ID from organization and code."""
        return f"{self.organization}-{self.code}"
