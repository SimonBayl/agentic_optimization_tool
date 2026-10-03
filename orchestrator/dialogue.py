"""Select, merge and summarize the clarification questions."""

from data_model.AgentState import AgentState
from data_model.ClarificationState import (
    ClarificationQuestion,
    ClarificationState,
)
from data_model.prompts import (
    NOT_READY,
    READY,
    SCHEMA_QUESTION,
    TURN_INSTRUCTION,
)
from parameters import Settings


def turn_instruction(state: AgentState) -> str:
    """Tell the LLM which questions were already asked or deferred."""
    asked = "\n".join(f"- {key} (asked {len(texts)} times): {texts[-1]}"
                      for key, texts in state.asked_questions.items())
    deferred = ", ".join(sorted(state.deferred_question_ids))
    return TURN_INSTRUCTION.format(asked=asked or "none",
                                   deferred=deferred or "none")


def merge_clarifications(previous: ClarificationState,
                         new: ClarificationState,
                         prefix: str) -> ClarificationState:
    """
    Replace the pending questions of one phase and keep the others.

    Parameters
    ----------
    previous:
        Clarification state before the node.
    new:
        Clarification state returned by the LLM.
    prefix:
        Identifier prefix of the questions owned by the phase, such as
        Q_ for understand or C_ for completeness.

    Returns
    -------
    ClarificationState
        Merged state, not ready while a required question is pending.
    """
    resolved = list(dict.fromkeys(previous.resolved_question_ids
                                  + new.resolved_question_ids))
    kept = [question for question in previous.pending_questions
            if not question.id.startswith(prefix)]
    owned = [question for question in new.pending_questions
             if question.id.startswith(prefix)]
    pending = [question for question in kept + owned
               if question.id not in resolved]
    ready = new.ready_for_formalization and not any(
        question.required for question in pending)
    return ClarificationState(pending_questions=pending,
                              resolved_question_ids=resolved,
                              ready_for_formalization=ready)


def schema_answer(state: AgentState) -> str:
    """Return the user answer to the data schema question, if any."""
    messages = state.messages
    asked = (len(messages) >= 2 and messages[-1].type == "human"
             and SCHEMA_QUESTION in messages[-2].text)
    return messages[-1].text if asked else ""


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
        if asks < settings.clarification.max_question_asks:
            return question, deferred
        deferred.append(question.id)
    return None, deferred


def status(clarification: ClarificationState) -> str:
    """Tell the user whether the model can be built."""
    return READY if clarification.ready_for_formalization else NOT_READY
