# understand

First tool of the dialogue: it retrieves the business information from the user and asks questions until the understanding is complete.

## Behavior

- Input: the AgentState, with the per-turn instruction listing the questions already asked and deferred. Context sent to the LLM: the current business spec, the clarification
  state and the whole conversation (UNDERSTAND_PROMPT and UNDERSTAND_CONTEXT). Output: a full new business spec and the clarification state of the turn.
- Model: `models.understanding`, with the longer retry policy (`llm_retry(understanding=True)`).

The understand node merges the clarifications with the previous ones and resets the model spec, since the business spec may have changed.

## Files

- AgentUnderstand.py: AgentUnderstanding, the LLM call.
- OutputUnderstand.py: UnderstandingOutput, the structured output:
  - business_spec: BusinessProblemSpec
  - clarification_state: ClarificationState
