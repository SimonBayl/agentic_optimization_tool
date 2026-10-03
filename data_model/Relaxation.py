"""Describe a change of a business rule proposed to the user."""

from pydantic import BaseModel, Field


class Relaxation(BaseModel):
    """Change of one business rule, with its expected effect.

    Attributes
    ----------
    rule_id:
        Identifier of the business rule concerned, such as RULE_001.
    proposal:
        Change of the rule, worded in the terms of the user.
    trade_off:
        What the user gains and what they give up with this change.
    """

    rule_id: str = Field(description="Business rule ID such as RULE_001.")
    proposal: str = Field(
        description="Change of the rule, in the terms of the user.")
    trade_off: str = Field(
        description="What the change gains and what it gives up.")
