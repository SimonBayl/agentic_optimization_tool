# explain

Explains the result of the solver to the user in business terms, never
with mathematical symbols. It follows the format of the other LLM tools:
a Mistral model (`models.explain`) with the longer retry policy
(`llm_retry(understanding=True)`), returning a Pydantic structured
output.

## Context of the LLM

EXPLAIN_PROMPT as system message, then, in order: problem, objectives,
business rules with their hardness, model parameters, objective and
constraints, status and objective value, nonzero solution values (at most
`explain.listed_values` per variable, with their count and total), data
summary (count, min, max and total of each parameter), constraint margins
("not available" without them), scenarios, previous reply and user
request. The LLM copies figures from this context and never computes
them; an effect it cannot derive is called an estimate. Without model
spec or result, explain_context raises ValueError.

## Structured output (ExplainOutput.py)

- variable_explanation: the decisions, summarized in business terms.
- objective_explanation: what is optimized and the value reached.
- constraint_gaps: the rules fully used and the rules leaving room, from
  the computed margins only; an equality is never a bottleneck.
- possible_gains: Relaxation list on the binding rules likely to improve
  the objective, with their trade-off; empty without solution. The dual
  is not used: the gains are estimates.
- feasibility_recommendations: when the model is infeasible or unbounded,
  the rules most likely in conflict, one Relaxation per rule.
- scenario_comparison: only when asked and two scenarios exist.
- answer: direct answer to a question of the user, null otherwise.

## Margins

- Computed only for the statuses optimal and feasible.
- The data and model code are written to a temporary script; inspector.py
  rebuilds the model in a `python -I` subprocess, reads the nonzero values
  on stdin as `{symbol: [[index, value], ...]}` (missing values are 0) and
  evaluates each constraint without solving again: the margins are exact
  and verifiable. Its time limit is `model_builder.timeouts.data`; any
  failure gives no margin, since margins are optional.
- margin = distance between the activity and its closest bound, at least
  0. A constraint is binding when its margin is at most `explain.tolerance`
  times `max(1, |closest bound|)`.
- A constraint belongs to the longest spec constraint name prefixing its
  own; rules come in spec order, then unmatched constraints alone.

## Scenarios and reply

- record_scenario adds a scenario `S<n>` for each spec hash not yet
  solved, described by the patch summary or "Initial model".
- explanation_text writes the full explanation (answer, decisions,
  objective, margins, gains, feasibility, comparison) for a new scenario
  or a spec change; for a question, only the answer and the comparison,
  unless both are empty.
- If the LLM fails, the reply is EXPLAIN_FAILED with the error type, and
  the user can ask again.

## Files

- Explain.py: AgentExplain, the context it receives and the summaries
  of the data and of the solution.
- ExplainOutput.py: the structured output.
- margins.py: computes the constraint activities and groups the margins by
  rule (data_model/ConstraintMargin.py).
- inspector.py: subprocess entry point `inspector.py <script> <data_dir>`
  printing the activity, lower and upper bound of each constraint as the
  last stdout line.
- report.py: records the scenarios (data_model/Scenario.py) and writes
  the explanation as reply text.
