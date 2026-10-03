Wires the agentic tools into the LangGraph and holds the logic of the dialogue (which question to ask, when to move on).

## graph_orchestrator.py

AgentGraph keeps the tools (understander, reviewer) and the settings, and exposes them as nodes:
- understand: calls the understander, merges the Q_ questions, resets model_spec.
- complete: calls the reviewer, merges the C_ questions, saves model_spec and data_schema.
- reply: picks the question to ask and writes the answer of the turn (appended to messages and stored in reply).

`route` is called after understand: complete if no required Q_ question is pending or if the budget is spent, reply otherwise.

`compile()` builds the graph for a single user turn, every turn ends on reply. New nodes (validator, builder...) will be added here, one at a time.

## dialogue.py

- turn_instruction: tells the LLM which questions were already asked (and how many times) and which are deferred.
- merge_clarifications(previous, new, prefix): resolved IDs are accumulated, pending questions of the phase (prefix Q_ or C_) are replaced, the others kept. Not ready while a required question is pending.
- pick_question: one question per turn, required ones first. A question asked `clarification.max_question_asks` times is deferred: the user is told an assumption will be made, and it is never asked again.
- schema_answer: the user answer when the last question was the data schema one.
- status: the sentence telling if the model can be built.

When there is no question left, the reply gives the problem summary, the status and invites the user to give more details.
