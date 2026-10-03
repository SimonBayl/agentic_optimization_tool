# agentic_tools

The tools called by the nodes of the graph. Each one reads the AgentState
and returns its output; the nodes of orchestrator/graph_orchestrator.py
turn it into a state update.

## Tools

| Tool | Role | Output | Model |
|------|------|--------|-------|
| understand | Extract the business information from the conversation and ask the missing points. | BusinessProblemSpec, ClarificationState | understanding |
| completeness | Draft a mathematical model spec from the business spec and bind it to the data columns; list the required fields left empty. | MathematicalStructure, ClarificationState | understanding |
| model | Generate the data and model code from the spec, run it and solve it. | OptimizationResult | code |
| edit | Turn a request on a built model into the smallest patch of its spec. | ModelPatch | editor |
| explain | Explain the result in the terms of the user: decisions, objective, margins, gains, relaxations, scenario comparison. | ExplainOutput | explain |

The Model column names the key of `models` in parameters.yaml.

## Shared code

utils.py, used by every LLM tool:

- MistralAgent: base class holding the Mistral client, the model name and
  the settings (`llm.temperature`, `llm.max_tokens`). `parse` sends the
  messages with `chat.parse_async` and returns the Pydantic object; it
  raises ValueError without message and TypeError without structured
  answer. `format_messages` writes the conversation as `TYPE:\ncontent`
  blocks.
- llm_retry: decorator reading the policy from `self.settings` at call
  time. Retried: HTTP 429, 500, 502, 503, 504, timeouts and network
  errors; anything else is raised at once, and the last error is raised
  unchanged. The delay before retry n is `2**n + uniform(0, 1) +
  base_delay`; `max_delay` is only validated (`0 < base <= max`).
  `understanding=True` selects the `understanding_*` policy.

## Rules

- Every LLM call is decorated with llm_retry and returns a structured
  output, except the code model, which returns a fenced code block.
- What can be checked without an LLM (code, patch, data, margins) is
  checked by plain functions, and the errors are fed back to the LLM in a
  correction loop bounded by a `max_attempts` parameter.
- A tool never mutates the state it receives and never returns a state
  field it does not own.
- Prompts are imported from data_model/prompts.py; a tool only formats
  the context.
- Each subfolder has its own AGENTS.md: keep it in sync with its code.
