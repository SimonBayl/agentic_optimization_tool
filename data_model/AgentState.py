"""Define the state shared by every node of the agent graph."""

from dataclasses import dataclass, field

from langchain_core.messages import AnyMessage

from data_model.BusinessProblemSpec import BusinessProblemSpec
from data_model.ClarificationState import ClarificationState
from data_model.MathematicalStructure import MathematicalStructure


@dataclass
class AgentState:  # pylint: disable=too-many-instance-attributes
    """Create the shared state of the agent.

    Attributes
    ----------
    messages:
        Whole conversation between the user and the agent.
    business_spec:
        Current business understanding of the problem.
    clarification_state:
        Questions pending or resolved.
    asked_questions:
        Texts already asked to the user, by question identifier.
    deferred_question_ids:
        Questions asked too often, replaced by assumptions.
    reply:
        Last answer sent to the user.
    data_schema:
        Columns and meaning of each input file, empty when unknown.
    model_spec:
        Draft of the mathematical structure, reset when the business
        spec changes.
    """

    messages: list[AnyMessage] = field(default_factory=list)
    business_spec: BusinessProblemSpec = field(
        default_factory=BusinessProblemSpec)
    clarification_state: ClarificationState = field(
        default_factory=ClarificationState)
    asked_questions: dict[str, list[str]] = field(default_factory=dict)
    deferred_question_ids: set[str] = field(default_factory=set)
    reply: str = ""
    data_schema: str = ""
    model_spec: MathematicalStructure | None = None
