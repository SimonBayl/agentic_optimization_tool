"""Describe the margin left by a solution on one business rule."""

from pydantic import BaseModel


class ConstraintMargin(BaseModel):
    """Margin of a solution on the constraints of one business rule.

    Attributes
    ----------
    rule:
        Name of the constraint in the model spec, such as RULE_001.
    constraints:
        Number of constraints generated for this rule.
    binding:
        Number of these constraints without any margin left.
    tightest:
        Name of the constraint with the smallest margin.
    margin:
        Smallest distance between a constraint and its bound.
    """

    rule: str
    constraints: int
    binding: int
    tightest: str
    margin: float
