"""Define the business understanding of the optimization problem."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class ConstraintHardness(StrEnum):
    """Indicate whether a business rule is mandatory or relaxable."""

    HARD = "hard"
    SOFT = "soft"
    LINK = "link"
    UNKNOWN = "unknown"


class BusinessObjective(BaseModel):
    """Business objective expressed by the user."""

    id: str = Field(description="Unique identifier such as OBJ_001.")
    interpretation: str | None = Field(default=None, description=(
        "Current business interpretation of the objective. "
        "This should not yet contain solver code."))
    direction: Literal["minimize", "maximize"] | None = None


class BusinessConstraint(BaseModel):
    """Define rules or constraints extracted from the conversation."""

    id: str = Field(description="Unique identifier such as RULE_001.")
    interpretation: str | None = Field(
        default=None,
        description="Normalized business interpretation of the constraint.")
    hardness: ConstraintHardness = Field(
        default=ConstraintHardness.UNKNOWN, description=(
            "hard: must hold; soft: may be violated at a cost; "
            "link: ties decisions together; unknown: not stated yet."))


class BusinessAssumption(BaseModel):
    """Assumption made to fill a gap of the user description."""

    id: str = Field(description="Unique identifier such as ASM_001.")
    statement: str = Field(description="What is assumed.")
    status: Literal["proposed", "accepted", "rejected"] = Field(
        default="proposed", description=(
            "accepted or rejected only when the user said so."))


class BusinessProblemSpec(BaseModel):
    """Define the understanding of the problem."""

    problem_summary: str | None = None
    objectives: list[BusinessObjective] = Field(default_factory=list)
    business_constraints: list[BusinessConstraint] = Field(
        default_factory=list)
    assumptions: list[BusinessAssumption] = Field(default_factory=list)
