# understand

First tool of the dialogue: it retrieves the business information from the user and asks questions until the understanding is complete.

## Behavior

- Input: the AgentState, with the per-turn instruction listing the questions already asked and deferred. Context sent to the LLM: the current business spec, the clarification
  state and the whole conversation (UNDERSTAND_PROMPT and UNDERSTAND_CONTEXT). Output: a full new business spec and the clarification state of the turn.
- Model: `models.understanding`, with the longer retry policy (`llm_retry(understanding=True)`).

The understand node merges the clarifications with the previous ones and resets the model spec, since the business spec may have changed.
Only the Q_ questions are replaced by this merge, the C_ questions of completeness are kept. After the node, `route` sends the turn to completeness unless a required Q_ question is still pending (and not deferred).

What the prompt asks the LLM:
- return the full spec each turn (not a diff) and keep the IDs already given (OBJ_xxx, RULE_xxx, ASM_xxx, Q_xxx), new items are numbered after them,
- only facts said by the user or explicit assumptions, never invented data,
- questions about the business rules only: never about the solver or the modeling, and never ask for numerical values (costs, demands...) since they come later from the data files,
- `required` only when no sensible assumption exists.

## Files

- AgentUnderstand.py: AgentUnderstanding, the LLM call.
- OutputUnderstand.py: UnderstandingOutput, the structured output:
  - business_spec: BusinessProblemSpec
  - clarification_state: ClarificationState

## Known limits (ministral-8b)

Seen while testing in the terminal:
- it marks almost every question as required, even minor ones (transport mode...), which delays the switch to completeness,
- it sometimes drops a pending question or marks it resolved without an answer from the user,
- it can misread a rule (e.g. store capacity instead of warehouse capacity).
The deterministic checks planned in completeness/checker.py should limit the impact of these errors.

