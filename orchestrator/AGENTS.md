# orchestrator

The LangGraph graph: every node, every route, and the clarification
policy. The graph runs once per user message, from START to END, and
resumes from the state where the previous turn stopped. Only this folder
turns the outputs of the tools into state updates.

## Routes

```
START ─┬─ no model built ─> understand ─┬─ required question ─> reply
       │                                └─> complete ─> check
       │   check ─┬─ spec ready ─> build ─┬─ solved ─> explain ─> reply
       │          └─ otherwise ─> reply   └─ error ─> reply
       └─ model built ─> edit ─┬─ question ─> reply
                               ├─ spec changed, failed build or spec
                               │  not ready ─> check
                               └─ nothing changed ─> explain
reply ─> END
```

- route_turn: edit once `optimization_result` and `model_spec` both
  exist, understand otherwise.
- route (after understand): reply when a pending question is required,
  not prefixed `C_` and not deferred; complete otherwise, and always once
  the clarification budget is spent.
- route_model (after check): build when `ready_for_formalization` is true
  and `model_spec` exists.
- route_build: explain unless the result status is `error`.
- route_edit: reply for a patch question; check when the spec is not
  ready, the last build failed or the patch has operations; explain
  otherwise (the message is a question about the result).

## State fields written by each node

| Field | Written by |
|-------|------------|
| business_spec | understand (full replacement), edit (sync_rules) |
| clarification_state | understand, complete (merged), check |
| model_spec | understand (reset to None), complete, edit |
| optimization_result | build |
| last_model_patch | edit |
| scenarios | explain |
| explanation | explain; emptied by reply |
| messages, reply, asked_questions | reply |
| deferred_question_ids | reply (added), check (stale C_CHECK_ dropped) |

The session writes the user message and the data schema. A node returns
only the fields it changes, as a dict; an empty dict changes nothing.

## Nodes

- understand, complete: call the tools on `with_turn_instruction(state)`
  and merge their clarifications with the previous ones.
- check: recreates the `C_CHECK_` questions from the current gaps, drops
  the previous ones from pending, resolved and deferred (a deferred check
  is kept only if its gap remains), releases over-budget business
  questions, and sets `ready_for_formalization` to no required pending.
- build: skips when the spec hash equals that of a non-error result; a
  GenerationError becomes a result with the status `error` keeping the
  previous code (`kept_code`).
- edit: a failed build with an empty patch changes nothing, so check
  rebuilds; a question or an empty patch only stores the patch; otherwise
  the patch is applied and the business rules synced.
- explain: margins are computed only for `optimal` and `feasible`; an
  exception of the explainer becomes the EXPLAIN_FAILED text. The full
  explanation is written for a new scenario or a spec change, the focused
  one otherwise.
- reply: once a model is built, optional questions are no longer asked
  and deferral notices are hidden. The reply joins, in order: patch
  question or change, deferral notices, question (or summary and status
  before any build), spec JSON and result when ready and changed,
  explanation, NEXT_STEPS once built. The question asked is appended to
  `asked_questions` under its ID.

## Files

- graph_orchestrator.py: the route functions and AgentGraph, which holds
  the five tools and the settings, defines every node and compiles the
  graph.
- dialogue.py: pure functions of the clarification policy:
  - merge_clarifications: union of resolved IDs, in order; questions
    merged by ID, the current wording replacing the previous; resolved
    IDs removed from pending; ready when nothing is pending.
  - pick_question: first pending question, in order, not deferred; a
    question is deferred instead after `max_asks` asks, or when its
    normalized wording (case and spaces ignored) was already shown under
    any ID.
  - status: message shown when no question can be asked.
  - with_turn_instruction: transient copy of the state ending with the
    TURN_INSTRUCTION system message (asked and deferred IDs); it is never
    committed.

The clarification budget (`max_turns` questions asked in total)
guarantees the dialogue reaches a model.
