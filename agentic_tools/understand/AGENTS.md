# understand

First tool of the dialogue: it retrieves the business information from
the user and asks questions until the understanding is complete. It runs
on every turn until a model is built; afterwards the edit tool takes over.

## Behavior

- Input: the AgentState, with the per-turn instruction (TURN_INSTRUCTION)
  listing the questions already asked and deferred.
- Messages sent to the LLM: UNDERSTAND_PROMPT as system message, then
  UNDERSTAND_CONTEXT holding, in order, the current business spec (JSON),
  the clarification state (JSON) and the whole conversation, including
  the turn instruction.
- Output: a full new business spec and the clarification state of the
  turn, never a partial update.
- Model: `models.understanding`, with the longer retry policy
  (`llm_retry(understanding=True)`).

## Expected answer of the LLM

- Stay at the business level: no Python, no mathematical expression, no
  solver choice.
- Never invent information; keep confirmed items unless the user changes
  them, and update an element rather than duplicating it; mark the
  uncertain ones inferred, ambiguous or missing.
- Keep the IDs of objectives (OBJ_), rules (RULE_) and questions (Q_).
- Ask a question for every ambiguity that may change the model; a
  required question keeps `ready_for_formalization` false.
- Record every answered question ID in `resolved_question_ids`, with the
  previous ones. A question answered partly keeps its ID and is reworded:
  acknowledge the answer, say what is missing, never repeat the wording.
- An explicit absence of further constraints is a valid answer.
- Optional unanswered questions must not block formalization.
- Every text field is in English.

## Node

The understand node merges the clarifications with the previous ones
(merge_clarifications), so an omitted question stays pending and a
resolved ID stays resolved. It resets the model spec, since the business
spec may have changed.

## Files

- AgentUnderstand.py: AgentUnderstanding, the LLM call.
- OutputUnderstand.py: UnderstandingOutput, the structured output:
  - business_spec: BusinessProblemSpec
  - clarification_state: ClarificationState
