# Operations-research agent

A conversational agent that turns a business request, written in plain
language, into a linear optimization model, solves it and explains the
result in the terms of the user.

You describe what you want to decide and optimize ("which warehouses
should I open to serve my customers at the lowest cost?"); the agent asks
the questions it needs, links the model to your data files, writes and
runs the optimization code with OR-Tools (HiGHS solver), then explains the
decisions, the rules that limit the result and the changes that could
improve it. Every language model call goes to Mistral.

## How it works

Each message runs one turn of a LangGraph graph, which ends on a single
reply:

1. **Understand**: the request becomes a business specification:
   objectives, business rules and assumptions.
2. **Complete**: this specification becomes a mathematical model (sets,
   parameters, variables, objective, constraints) bound to the columns of
   the data files.
3. **Check**: every required piece still missing becomes a question.
   Questions are asked one at a time, within a limited budget, so the
   dialogue always reaches a model.
4. **Build**: the code loading the data and the code of the model are
   generated, checked, run and corrected until the model is solved.
5. **Explain**: the result is explained with the margin left on each
   rule, possible relaxations and, on request, a comparison of the
   solved scenarios.
6. **Edit**: once a model exists, each new request ("add a limit of 3
   warehouses") becomes a small patch of the model, which is solved and
   explained again.

## Getting started

Requirements: [uv](https://docs.astral.sh/uv/) and a Mistral API key.

1. Create a `.env` file next to `main.py`:

   ```
   MISTRAL_API_KEY=<your key>
   ```

2. Launch the agent on LINUX:

   ```
   cd agentic_optimization_tool
   uv venv
   source .venv/bin/activate
   uv sync
   python main.py
   ```

   The script creates the virtual environment, installs the dependencies
   and runs `python main.py`.

In the terminal, write your message and type `/send` on its own line.
`/undo` reverts the last turn, `/new` starts over and `/quit` exits.

## What you can change

- **Data files** (`test_data/` by default): the CSV files the model reads.
  Any set of CSV files with a header row can be used; the folder is set
  in `parameters.yaml`.
- **`parameters.yaml`**: the global parameters, among others the Mistral
  model of each agent, the clarification budget, the attempts and time
  limits of the code generation, and the meaning of the data columns
  (`data_schema.meanings`). A column without meaning is asked to the user.
  Another file can be used with the `AGENT_PARAMETERS` environment
  variable.
- **`data_model/prompts.py`**: the instructions given to each language
  model and the fixed texts of the replies.
- **`.env`**: the Mistral API key.

## Example

The files of `test_data/` describe a warehouse location problem: 16
candidate warehouses with a capacity and an opening cost, 50 customers
with a demand, and the cost of serving each customer from each warehouse.
A request such as "Choose which warehouses to open and how to serve the
customers at minimum total cost, without exceeding the capacities" leads
the agent to build, solve and explain this model.

## Project layout

| Folder | Content |
|--------|---------|
| `data_model/` | Shared data structures, prompts and settings |
| `agentic_tools/` | The agents: understand, completeness, model, edit, explain |
| `orchestrator/` | The LangGraph graph and the clarification policy |
| `interactions/` | The conversation session, the terminal and the data schema reader |

Each folder has an `AGENTS.md` file describing its files in detail.
