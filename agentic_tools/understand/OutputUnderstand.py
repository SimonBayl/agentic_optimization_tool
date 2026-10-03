"""Define the structured output of the understanding agent."""

from pydantic import BaseModel

from data_model.BusinessProblemSpec import BusinessProblemSpec
from data_model.ClarificationState import ClarificationState


class UnderstandingOutput(BaseModel):
    """Structure the output returned by AgentUnderstanding.

    This output deliberately contains only what this node is responsible for.

    Attributes
    ----------
    business_spec:
        Complete updated business specification.
    clarification_state:
        Complete updated questions, pending and resolved.
    """

    business_spec: BusinessProblemSpec
    clarification_state: ClarificationState
