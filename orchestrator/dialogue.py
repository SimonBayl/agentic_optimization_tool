"""Apply the clarification policy as pure functions used by the graph."""

from dataclasses import replace

from langchain_core.messages import SystemMessage

from data_model.AgentState import AgentState
from data_model.ClarificationState import (
    ClarificationQuestion,
    ClarificationState,
)
from data_model.prompts import TURN_INSTRUCTION
from data_model.settings import Settings


def normalize_question(text: str) -> str:
    """Ignore case and whitespace when detecting repeated questions."""
    return " ".join(text.casefold().split())


def with_turn_instruction(state: AgentState) -> AgentState:
    """Return a transient state ending with the per-turn control message."""
    text = TURN_INSTRUCTION.format(
        asked=state.asked_questions,
        deferred=sorted(state.deferred_question_ids))
    return replace(
        state, messages=[*state.messages, SystemMessage(content=text)])


def merge_clarifications(
    previous: ClarificationState,
    current: ClarificationState,
) -> ClarificationState:
    """Accumulate resolved IDs and keep omitted questions pending."""
    resolved = list(dict.fromkeys(
        previous.resolved_question_ids + current.resolved_question_ids))
    questions = {q.id: q for q in previous.pending_questions}
    questions.update((q.id, q) for q in current.pending_questions)
    pending = [q for q in questions.values() if q.id not in resolved]
    return ClarificationState(
        pending_questions=pending,
        resolved_question_ids=resolved,
        ready_for_formalization=len(pending) == 0)


def pick_question(
    state: AgentState,
    settings: Settings,
) -> tuple[ClarificationQuestion | None, list[str]]:
    """Return the next askable question and the newly deferred IDs."""
    shown = {normalize_question(text)
             for texts in state.asked_questions.values()
             for text in texts}
    deferred: list[str] = []
    for question in state.clarification_state.pending_questions:
        if question.id in state.deferred_question_ids:
            continue
        asks = len(state.asked_questions.get(question.id, []))
        repeated = normalize_question(question.question) in shown
        if asks >= settings.clarification.max_asks or repeated:
            deferred.append(question.id)
            continue
        return question, deferred
    return None, deferred


def status(clarification: ClarificationState) -> str:
    """Summarize the request status once no question can be asked."""
    if not clarification.pending_questions:
        if clarification.ready_for_formalization:
            return "Your request is ready for formalization."
        return "Your request has been updated. You can refine it further."
    message = ("The remaining clarifications have been set aside. "
               "You can still provide them at any time.")
    if any(q.required for q in clarification.pending_questions):
        message += " Formalization remains blocked."
    return message
