"""Define the structured output of the understanding tool."""

from pydantic import BaseModel

from data_model.BusinessProblemSpec import BusinessProblemSpec
from data_model.Clarification import ClarificationState


class UnderstandingOutput(BaseModel):
    """Full new business spec and clarification state of the turn."""

    business_spec: BusinessProblemSpec
    clarification_state: ClarificationState
