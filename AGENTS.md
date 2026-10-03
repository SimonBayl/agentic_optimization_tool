# Operations-research agent

Standalone conversational agent turning a business request into a linear
optimization model, solving it with OR-Tools (HiGHS) and explaining the
result in the terms of the user. Every LLM call goes to Mistral.

## Running

- Run from this folder: `python main.py`.
- `MISTRAL_API_KEY` is read from a `.env` file.
- Global parameters are in `parameters.yaml`; another file can be given
  with the `AGENT_PARAMETERS` environment variable.
- Input data are the CSV files of `test_data` (`model_builder.data_dir`).
- Tests: `pytest` from this folder (`tests/`, one module per component).

## Pipeline

The LangGraph graph runs once per user message and ends on one reply.

1. understand: extract the business spec and its clarification questions.
2. complete: draft the mathematical model spec and bind it to the data.
3. check: turn the empty required fields into questions.
4. build: generate the data and model code, run it and solve.
5. explain: explain the result, its margins and its scenarios.
6. edit: once a model is built, patch its spec from the next requests.

Questions are asked one at a time until the spec is complete or the
clarification budget is spent.

## Conventions

- The code must pass ruff, mypy and pylint, with lines of at most
  80 columns.
- The arguments and the return value of every function are typed.
- Functions and classes have docstrings (numpy style for public ones).
- All text, whether user-facing, specification or prompt, is in English.
- Parameters live in `parameters.yaml`, never as module constants; the
  Settings object is passed to every class and function needing one.
- Prompts live in `data_model/prompts.py`.
- The tools never update the graph state themselves: they return a value
  and the nodes of the orchestrator build the state update.

## Folders

- data_model: atomic objects, prompts and settings; no logic, no LLM call.
- agentic_tools: the tools (understand, completeness, model, edit,
  explain) built on data_model.
- orchestrator: the LangGraph graph, every node and route, and the
  clarification policy.
- interactions: the conversation session, the terminal and the reading of
  the data schema.
- tests: unit tests; LLM calls are mocked.

Each folder has its own AGENTS.md describing its files.
