"""Define the business understanding of the optimization problem."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class InformationStatus(str, Enum):
    """Define the status of a piece of information extracted from the user.

    Attributes
    ----------
    confirmed:
        Stated explicitly by the user.
    inferred:
        Deduced by the agent from the conversation, not stated as such.
    ambiguous:
        Mentioned by the user but open to several interpretations.
    missing:
        Needed to build the model but not provided yet.
    """

    # pylint: disable=invalid-name
    confirmed = "confirmed"
    inferred = "inferred"
    ambiguous = "ambiguous"
    missing = "missing"


class ConstraintHardness(str, Enum):
    """Indicate whether a business rule is mandatory or relaxable.

    Attributes
    ----------
    hard:
        Rule that every solution must satisfy.
    soft:
        Rule that may be violated, usually at a penalty cost.
    link:
        Rule tying decisions together, such as affecting a ressource only
        if a demand is needed.
    unknown:
        Nature not stated by the user yet.
    """

    # pylint: disable=invalid-name
    hard = "hard"
    soft = "soft"
    link = "link"
    unknown = "unknown"


class BusinessObjective(BaseModel):
    """Business objective expressed by the user.

    Attributes
    ----------
    id:
        Stable identifier such as OBJ_001, kept across turns.
    original_text:
        Wording of the user, as close as possible to the original.
    interpretation:
        Business reading of the objective, without solver code.
    direction:
        Whether the criterion is minimized or maximized; None when unknown.
    status:
        Confidence in this objective.
    """

    id: str = Field(description="Unique identifier such as OBJ_001.")
    original_text: str = Field(
        description="Original or close-to-original formulation from the user.")
    interpretation: str | None = Field(
        default=None,
        description=(
            "Current business interpretation of the objective. "
            "This should not yet contain solver code."))
    direction: Literal["minimize", "maximize"] | None = None
    status: InformationStatus


class BusinessConstraint(BaseModel):
    """Define rules or constraints extracted from the conversation.

    Attributes
    ----------
    id:
        Stable identifier such as RULE_001, reused to name the constraints
        of the mathematical model.
    original_text:
        Wording of the user, as close as possible to the original.
    interpretation:
        Normalized business reading of the rule.
    hardness:
        Whether the rule is mandatory, relaxable or a linking rule.
    status:
        Confidence in this rule.
    """

    id: str = Field(description="Unique identifier such as RULE_001.")
    original_text: str = Field(
        description="Original or close-to-original user formulation.")
    interpretation: str | None = Field(
        default=None,
        description="Normalized business interpretation of the constraints.")
    hardness: ConstraintHardness = ConstraintHardness.unknown
    status: InformationStatus


class Assumption(BaseModel):
    """Define assumptions introduced while understanding the problem.

    Attributes
    ----------
    id:
        Stable identifier of the assumption.
    description:
        Content of the assumption.
    status:
        Whether the user has accepted or rejected it, or not answered yet.
    source:
        Who introduced it: the user, the agent, or a deduction from
        other information.
    """

    id: str
    description: str
    status: Literal["proposed", "accepted", "rejected"] = "proposed"
    source: Literal["user", "agent", "derived"] = "agent"


class BusinessProblemSpec(BaseModel):
    """Define the semantic understanding of the optimization problem.

    This object deliberately stays at the business level.
    It must not contain technical informations.

    Attributes
    ----------
    problem_summary:
        Short description of the problem in business terms.
    objectives:
        Criteria the user wants to optimize.
    business_constraints:
        Rules the solutions must follow.
    assumptions:
        Hypotheses made to fill the gaps of the request.
    """

    problem_summary: str | None = None
    objectives: list[BusinessObjective] = Field(default_factory=list)
    business_constraints: list[BusinessConstraint] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
