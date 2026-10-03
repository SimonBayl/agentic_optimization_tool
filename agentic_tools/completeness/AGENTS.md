# completeness

Formalizes the business spec into a first mathematical model spec and
links it to the available data, then lists the required fields still
empty.

## Behavior

- Input: the AgentState, with the per-turn instruction.
- Messages sent to the LLM: COMPLETE_PROMPT as system message, then the
  business spec, the clarification state, the data schema (columns and
  meaning of each file) and the conversation.
- Output: the best draft of the model spec, unknown parts left empty, and
  the questions still needed, prefixed `C_`.
- Without a data schema, no LLM is called: the required question
  C_DATA_SCHEMA asks for the format of the data and the spec is None.
- Model: `models.understanding`, default retry policy.

## Expected model spec

- Sets, parameters and variables named with short Python identifiers
  without index suffix (x, cost, demand); indices, domain, bounds and
  units in the description, for example `x[w, c]: fraction of demand of
  c served by w`.
- Linear objective and constraints, integer variables allowed; never a
  product or quotient of two decision variables.
- Each constraint named after its business rule ID.
- Every set and parameter bound to an existing `file.column`.
- Units consistent with the column meanings; multiobjective priorities
  and assumptions affecting the model are asked, never chosen.

## Checker

After the LLM, the check node applies the functions of checker.py without
any LLM. The checker owns the questions prefixed `C_CHECK_` and recreates
them on each run, so a gap disappears as soon as it is filled.

| Key | Gap |
|-----|-----|
| SUMMARY | no problem summary |
| OBJECTIVES | no objective |
| DIRECTION | an objective without direction |
| ASSUMPTIONS | an assumption proposed by the agent, not confirmed |
| HARDNESS | a rule of unknown hardness |
| MODEL | no model spec although a data schema exists |
| SETS, PARAMETERS, VARIABLES, CONSTRAINTS, BINDINGS | field empty |
| OBJECTIVE | no objective expression or no direction |
| BINDINGS_INVALID | a binding to an unknown symbol or `file.column` |

- Model gaps are checked only when a data schema exists.
- A question already asked is prefixed with FOLLOW_UP; its ID, reason
  ("Required field left empty.") and related_to (the key) do not change.
- Keys listed in `clarification.optional_checks` are never required.

## Budget

- budget_spent: the questions asked in total reach
  `clarification.max_turns`.
- released: a business or completeness question becomes optional once
  the budget is spent, or once it was asked and deferred. Checker
  questions stay required, since the model cannot be built without these
  fields.

## Files

- AgentComplete.py: AgentCompleteness, the LLM call.
- OutputComplete.py: CompletenessOutput, the structured output:
  - clarification_state: ClarificationState
  - model_spec: MathematicalStructure
- checker.py: the gap functions, the check questions and the clarification
  budget.
