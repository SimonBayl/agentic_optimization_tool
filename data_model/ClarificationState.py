"""Define the clarification questions exchanged with the user."""

from pydantic import BaseModel, Field


class ClarificationQuestion(BaseModel):
    """Question that must or may be asked to the user.

    Attributes
    ----------
    id:
        Stable identifier: Q_ for business questions, C_ for completeness
        questions and C_CHECK_ for questions created by the checker.
    question:
        Text displayed to the user.
    reason:
        Why the answer is needed to build the model.
    related_to:
        Identifier of the objective, rule or field concerned, if any.
    required:
        True when the model must not be generated before the answer.
    """

    id: str = Field(description="Unique identifier such as Q_001.")
    question: str
    reason: str = Field(description="Why this question is needed.")
    related_to: str | None = Field(
        default=None,
        description=(
            "Identifier of the business objective, rule or concept "
            "associated with the question."))
    required: bool = Field(
        default=True,
        description=(
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
        True when no required question remains and the model can be built.
    """

    pending_questions: list[ClarificationQuestion] = Field(default_factory=list)
    resolved_question_ids: list[str] = Field(default_factory=list)
    ready_for_formalization: bool = False
