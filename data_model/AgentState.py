"""Define the state shared by every node of the agent graph."""

from dataclasses import dataclass, field

from langchain_core.messages import BaseMessage

from data_model.BusinessProblemSpec import BusinessProblemSpec
from data_model.ClarificationState import ClarificationState
from data_model.MathematicalStructure import MathematicalStructure
from data_model.ModelPatch import ModelPatch
from data_model.OptimisationResult import OptimizationResult
from data_model.Scenario import Scenario


@dataclass
class AgentState:  # pylint: disable=too-many-instance-attributes
    """Complete shared state of the optimization agent.

    Attributes
    ----------
    messages:
        Conversation history, user and agent messages.
    business_spec:
        Business understanding of the problem.
    clarification_state:
        Pending and resolved questions.
    model_spec:
        Mathematical structure of the model; None until completeness
        produces it, and reset whenever the business spec changes.
    data_schema:
        Columns of each input file with their meaning, by file name.
    asked_questions:
        Every wording displayed for each question ID.
    deferred_question_ids:
        Questions set aside after too many asks.
    reply:
        Last message returned to the user.
    optimization_result:
        Result of the last build, including the generated code.
    last_model_patch:
        Last modification requested on the built model.
    scenarios:
        Every solved version of the model, for comparisons.
    explanation:
        Explanation of the result written this turn, empty otherwise.
    """

    messages: list[BaseMessage]
    business_spec: BusinessProblemSpec
    clarification_state: ClarificationState
    model_spec: MathematicalStructure | None = None
    data_schema: dict[str, dict[str, str]] = field(default_factory=dict)
    asked_questions: dict[str, list[str]] = field(default_factory=dict)
    deferred_question_ids: set[str] = field(default_factory=set)
    reply: str = ""
    optimization_result: OptimizationResult | None = None
    last_model_patch: ModelPatch | None = None
    scenarios: list[Scenario] = field(default_factory=list)
    explanation: str = ""


def create_initial_state() -> AgentState:
    """
    Create a clean initial state for a new optimization conversation.

    Returns
    -------
    AgentState
        Empty state ready to be passed to the LangGraph workflow.
    """
    return AgentState(
        messages=[],
        business_spec=BusinessProblemSpec(),
        clarification_state=ClarificationState(),
    )
