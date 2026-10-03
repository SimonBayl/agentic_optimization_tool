"""Check the clarification budget before reviewing completeness."""

from data_model.AgentState import AgentState
from parameters import Settings


def budget_spent(state: AgentState, settings: Settings) -> bool:
    """Tell whether the clarification budget of the user is used up."""
    asks = sum(len(texts) for texts in state.asked_questions.values())
    return asks >= settings.clarification.max_turns
