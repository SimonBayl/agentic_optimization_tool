In the data model folder there are 2 types of objects, state (AgentState object) is a dataclass taht represent the backbone of the agentic framework. It's a dataclass shared by every node of the graph. It holds the conversation messages, the business spec and the clarification state.

## Specifications (Pydantic)

BusinessProblemSpec and Clarificaton are 2 objects that represent attribute of AgentState.

- BusinessProblemSpec.py: business understanding of the problem: summary, objectives (with direction), business rules `RULE_xxx` (with hardness: hard, soft, link or unknown) and assumptions (proposed, accepted or rejected).

- ClarificationState.py: pending questions (ID, text, reason, required),resolved question IDs and the `ready_for_formalization` flag.

