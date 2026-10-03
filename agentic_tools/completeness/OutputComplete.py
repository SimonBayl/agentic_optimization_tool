"""Define the structured output of the completeness agent."""

from pydantic import BaseModel

from data_model.ClarificationState import ClarificationState
from data_model.MathematicalStructure import MathematicalStructure


class CompletenessOutput(BaseModel):
    """Return missing information or a preliminary mathematical structure.

    Attributes
    ----------
    clarification_state:
        Questions on the gaps found, with stable IDs prefixed C_.
    model_spec:
        Best draft of the mathematical structure, unknown parts left empty.
    """

    clarification_state: ClarificationState
    model_spec: MathematicalStructure
