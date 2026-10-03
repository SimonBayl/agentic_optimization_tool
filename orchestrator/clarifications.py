"""Select, merge and summarize the clarification questions."""

from data_model.AgentState import AgentState
from data_model.Clarification import ClarificationQuestion, ClarificationState
from data_model.prompts import NOT_READY, READY, TURN_INSTRUCTION
from parameters import Settings


def turn_instruction(state: AgentState) -> str:
    """Tell the LLM which questions were already asked or deferred."""
    asked = "\n".join(f"- {key} (asked {len(texts)} times): {texts[-1]}"
                      for key, texts in state.asked_questions.items())
    deferred = ", ".join(sorted(state.deferred_question_ids))
    return TURN_INSTRUCTION.format(asked=asked or "none",
                                   deferred=deferred or "none")


def merge_clarifications(previous: ClarificationState,
                         new: ClarificationState) -> ClarificationState:
    """
    Keep every resolved question and drop them from the pending ones.

    Parameters
    ----------
    previous:
        Clarification state before the turn.
    new:
        Clarification state returned by the LLM.

    Returns
    -------
    ClarificationState
        Merged state, not ready while a required question is pending.
    """
    resolved = list(dict.fromkeys(previous.resolved_question_ids
                                  + new.resolved_question_ids))
    pending = [question for question in new.pending_questions
               if question.id not in resolved]
    ready = new.ready_for_formalization and not any(
        question.required for question in pending)
    return ClarificationState(pending_questions=pending,
                              resolved_question_ids=resolved,
                              ready_for_formalization=ready)


def pick_question(
    state: AgentState, settings: Settings,
) -> tuple[ClarificationQuestion | None, list[str]]:
    """
    Pick the next question to ask, required ones first.

    Parameters
    ----------
    state:
        Current state of the agent.
    settings:
        Global parameters, holding the maximum number of asks.

    Returns
    -------
    tuple[ClarificationQuestion | None, list[str]]
        Question to ask, if any, and the identifiers newly deferred
        because they were asked too often.
    """
    deferred: list[str] = []
    pending = sorted(state.clarification_state.pending_questions,
                     key=lambda question: not question.required)
    for question in pending:
        if question.id in state.deferred_question_ids:
            continue
        asks = len(state.asked_questions.get(question.id, []))
        if asks < settings.max_question_asks:
            return question, deferred
        deferred.append(question.id)
    return None, deferred


def status(clarification: ClarificationState) -> str:
    """Tell the user whether the model can be built."""
    return READY if clarification.ready_for_formalization else NOT_READY
