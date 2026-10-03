Formalizes the business spec given by the understanding model into a more mathematical model spec and links it to the available data.

This tool represent an intermediate representation of the optimization problem.

- Input: the AgentState, with the per-turn instruction.
- Context sent to the LLM: the business spec, the clarification state, the data schema (columns and meaning of each file) and the conversation (COMPLETE_PROMPT).
- Output: the best draft of the model spec, unknown parts left empty, and the questions still needed.
- Without a data schema, no LLM is called: the question C_DATA_SCHEMA asks for the format of the data.
- Model: `models.understanding`.
