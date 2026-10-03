In the data model folder there are 2 types of objects, state (AgentState object) is a dataclass taht represent the backbone of the agentic framework. It's a dataclass shared by every node of the graph. It holds the conversation messages, the business spec and the clarification state.

AgentState fields:
- messages: the whole conversation (langchain HumanMessage / AIMessage).
- business_spec: BusinessProblemSpec, written by understand.
- clarification_state: ClarificationState, merged by understand (Q_ questions) and completeness (C_ questions).
- asked_questions: texts already asked to the user, by question ID. Used to count how many times a question was asked.
- deferred_question_ids: questions asked too often, the LLM must replace them with an assumption.
- reply: last answer sent to the user.
- data_schema: columns of each input file, empty until the user gives the data (--data option or answer to C_DATA_SCHEMA).
- model_spec: MathematicalStructure drafted by completeness. understand resets it to None since the business spec may have changed.

The nodes never modify the state in place, they return a dict with the fields to update (LangGraph overwrites them).

## Specifications (Pydantic)

BusinessProblemSpec and Clarificaton are 2 objects that represent attribute of AgentState.

- BusinessProblemSpec.py: business understanding of the problem: summary, objectives (with direction), business rules `RULE_xxx` (with hardness: hard, soft, link or unknown) and assumptions (proposed, accepted or rejected).

- ClarificationState.py: pending questions (ID, text, reason, required),resolved question IDs and the `ready_for_formalization` flag.
  `ready_for_formalization` is forced to false while a required question is still pending, whatever the LLM says.

- MathematicalStructure.py: solver-independent draft of the model: sets, parameters, variables (with domain and bounds), direction, objective, constraints named after their RULE_xxx and data_bindings (symbol → file.column, e.g. customers.csv.demand). Lists are used instead of dicts because the Mistral SDK doesn't accept free keys in structured outputs.

The descriptions of the pydantic fields are sent to the LLM in the JSON schema, so they are part of the prompt: keep them short and precise.

## Prompts

prompts.py holds every prompt and every text shown to the user:
- UNDERSTAND_PROMPT / UNDERSTAND_CONTEXT: system prompt and context template of understand.
- COMPLETE_PROMPT: system prompt of completeness.
- TURN_INSTRUCTION: questions already asked and deferred, added to the context at each turn.
- SCHEMA_QUESTION, DEFERRED, READY, NOT_READY, MORE_DETAILS: texts of the replies.

The prompts must stay generic: nothing specific to the warehouse problem, the system must not overfit it.

