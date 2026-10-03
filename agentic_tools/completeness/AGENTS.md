Formalizes the business spec given by the understanding model into a more mathematical model spec and links it to the available data.

This tool represent an intermediate representation of the optimization problem.

- Input: the AgentState, with the per-turn instruction.
- Context sent to the LLM: the business spec, the clarification state, the data schema (columns and meaning of each file) and the conversation (COMPLETE_PROMPT).
- Output: the best draft of the model spec, unknown parts left empty, and the questions still needed.
- Without a data schema, no LLM is called: the question C_DATA_SCHEMA asks for the format of the data.
- Model: `models.understanding`.
- Retry: default policy (`llm_retry()`).

## Details

- The data schema is passed apart from the state: the node gives `state.data_schema`, or the user answer when the last question asked was C_DATA_SCHEMA (`schema_answer` in orchestrator/dialogue.py). With the --data option the schema is built from the CSV headers (interactions/data_files.py): columns, number of rows and one example row per file.
- The prompt asks for a linear model draft: sets and parameters bound to a column (file.column) or given by the user, variables with their domain, the objective, and one constraint per business rule named after its RULE_xxx.
- Questions are about the gaps preventing a correct model (rule without data, ambiguous column meaning or unit, missing decision), asked in business terms, never about values already in the data.
- `ready_for_formalization` is true only when every rule has a constraint and every parameter is bound.
- The complete node merges only the C_ questions and saves model_spec and data_schema in the state, then the turn goes to reply.

## Files

- AgentComplete.py: AgentCompleteness (a MistralAgent), the LLM call. `ask_schema` builds the C_DATA_SCHEMA question without calling the LLM.
- OutputComplete.py: CompletenessOutput, the structured output:
  - clarification_state: ClarificationState (C_ questions)
  - model_spec: MathematicalStructure
- checker.py: deterministic checks, no LLM. For now only `budget_spent`, true when the number of questions asked reaches `clarification.max_turns`. It should also decide if the model is ready (every RULE has a constraint, every binding points to a real column...) instead of trusting the LLM flag.

