"""Define the clarification questions exchanged with the user."""

from pydantic import BaseModel, Field


class ClarificationQuestion(BaseModel):
    """Question that must or may be asked to the user."""

    id: str = Field(description="Unique identifier such as Q_001.")
    question: str
    reason: str = Field(description="Why this question is needed.")
    required: bool = Field(default=True, description=(
        "True when the optimization model should not be generated "
        "before the question is resolved."))


class ClarificationState(BaseModel):
    """Current clarification status of the conversation.

    Attributes
    ----------
    pending_questions:
        Questions still waiting for an answer.
    resolved_question_ids:
        Identifiers of every question answered so far.
    ready_for_formalization:
        True when the problem can be turned into a mathematical model.
    """

    pending_questions: list[ClarificationQuestion] = Field(
        default_factory=list)
    resolved_question_ids: list[str] = Field(default_factory=list)
    ready_for_formalization: bool = False
