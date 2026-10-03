# data_model

Atomic objects shared by every tool, the prompts and the settings. The
modules hold structures only: no LLM call, no graph logic, no I/O except
the reading of parameters.yaml. Every other folder may import it; it
imports none of them.

## Identifiers

| Prefix | Object | Created by |
|--------|--------|------------|
| OBJ_xxx | business objective | understand |
| RULE_xxx | business rule, and name prefix of its constraints | understand, edit |
| Q_xxx | business question | understand |
| C_xxx | completeness question | completeness |
| C_DATA_SCHEMA | question asked without data schema | completeness |
| C_CHECK_<KEY> | gap of a required field | checker |
| Sn | solved scenario, in order of resolution | explain |

An ID is stable across turns: a reworded question keeps its ID.

## State

- AgentState.py: dataclass shared by every node of the graph (see
  orchestrator/AGENTS.md for the node writing each field): messages,
  business_spec, clarification_state, model_spec (None until
  completeness, reset when the business spec changes), data_schema
  `{file: {column: meaning}}`, asked_questions `{ID: [wordings shown]}`,
  deferred_question_ids, reply, optimization_result, last_model_patch,
  scenarios, explanation. `create_initial_state` returns an empty state.
  A new field needs a default so that `create_initial_state` stays valid.

## Specifications (Pydantic)

- BusinessProblemSpec.py: business level only, never solver terms:
  summary, objectives (direction minimize, maximize or None), business
  rules (hardness hard, soft, link or unknown), assumptions (status
  proposed, accepted or rejected; source user, agent or derived). Every
  objective and rule keeps the user wording and an InformationStatus:
  confirmed, inferred, ambiguous or missing.
- ClarificationState.py:
  - ClarificationQuestion: ID, text, reason, related_to (objective, rule
    or field concerned), required (default true).
  - ClarificationState: pending questions, resolved IDs and the
    `ready_for_formalization` flag.
- MathematicalStructure.py: solver-independent model spec: sets,
  parameters, variables and constraints as NamedItem (short symbol,
  description with indices, domain and unit), direction, objective
  expression, and DataBinding `symbol <- file.column`. Lists replace
  dictionaries because Mistral structured outputs forbid free keys.
- ModelPatch.py: PatchOperation (target, action add, replace or remove,
  name, description) applied in order, a one-sentence summary, or a
  question when no operation applies. For the objective, the name is the
  direction and the description the expression; for a binding, the name
  is the symbol and the description the column.

## Results

- OptimisationResult.py: strict result (`extra="forbid"`): SolveStatus
  (optimal, feasible, infeasible, unbounded, not_solved, undefined,
  error), objective value, loaded sets and parameters, nonzero variable
  values as `[index] -> value`, `spec_hash` and `data_hash` (sha256), the
  validated `data_code` and `model_code`, attempts and last error.
- ConstraintMargin.py: margin of one rule: constraint count, binding
  count, tightest constraint and its margin.
- Relaxation.py: rule ID, proposal and trade-off, in user terms.
- Scenario.py: ID, description (patch summary or Initial model), spec
  hash, status, objective value and summary.

## Configuration

- prompts.py: every LLM prompt (`*_PROMPT`, UNDERSTAND_CONTEXT,
  TURN_INSTRUCTION) and every fixed text of the replies, in English.
  Templates use `str.format` fields; literal braces must be doubled.
- settings.py: Settings, read once by `load_settings` and passed down.
  Sections: models, llm, retry, clarification, model_builder,
  model_editor, explain, data_schema. Each one is a frozen Section
  rejecting unknown keys; every key is required except
  `data_schema.meanings` (an empty or fully commented mapping is
  allowed). To add a parameter, add its key to parameters.yaml and a
  typed, documented field to its section.
