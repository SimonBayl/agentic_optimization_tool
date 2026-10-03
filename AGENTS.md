The development context is described in Optimization - Simon Bayle.pdf

- The code must pass the linters (ruff, mypy, pylint) and must not exceed 80 columns.
- To run code, use the virtual environment .venv/bin/activate. If you need new dependencies, add them to pyproject.toml, then run uv sync.
- The arguments and return value of every function must be typed.
- Docstrings must follow the format currently in use.
- When developing a feature, keep the code concise: write small functions and do not generate too much code, so that it stays easy to read.
- For all user-interface development, follow the specifications in user_interface/AGENTS.md.
- All text, whether user-facing, specification or prompt, must be written in English.

I designed the following architecture for the agent. You may challenge it, but you must explain and justify your choices.
It must be built step by step, without rushing.



Here is the global design :

                        ┌───────────────────────┐
                        │         USER          │
                        └───────────┬───────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ 1. UNDERSTANDER     │
                         │ business extraction │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ 2. COMPLETENESS     │
                         │ ambiguities / gaps  │
                         └──────┬────────┬─────┘
                                │        │
                    incomplete  │        │ complete
                                ▼        ▼
                              USER   FORMALIZER
                                         │
                                         ▼
                               ┌─────────────────────┐
                               │ 3. MODEL SPEC / IR  │
                               └──────────┬──────────┘
                                          │
                                          ▼
                               ┌─────────────────────┐
                               │ 4. VALIDATOR        │
                               │ math + semantics    │
                               └──────┬────────┬─────┘
                                      │        │
                               error  │        │ OK
                                      ▼        ▼
                                  FORMALIZER  ROUTER
                                               │
                                               ▼
                                    ┌────────────────────┐
                                    │ 5. MODEL BUILDER   │
                                    └─────────┬──────────┘
                                              │
                                              ▼
                                    ┌────────────────────┐
                                    │ 6. SOLVER EXECUTOR │
                                    └─────────┬──────────┘
                                              │
             ┌───────────────┬────────────────┼────────────────┐
             ▼               ▼                ▼                ▼
          OPTIMAL         FEASIBLE       INFEASIBLE       ERROR /
                                           │             UNBOUNDED
                                           ▼
                                    INFEASIBILITY
                                      ANALYZER
             │               │             │
             └───────────────┴──────┬──────┘
                                    ▼
                             RESULT ANALYZER
                                    │
                                    ▼
                              EXPLAINER
                                    │
                                    ▼
                                  USER
                                    │
                          constraint modification
                                    │
                                    ▼
                              MODEL EDITOR
                                    │
                                    └──────► VALIDATOR

Global design in text :

Business Understanding (UNDERSTANDER)
The system extracts the business information provided by the user: objective, constraints, data, parameters, implicit variables, and overall problem context.

Completeness Check (COMPLETENESS)
The system checks whether the information is sufficiently complete and unambiguous.

If some information is missing or ambiguous, a clarification question is sent back to the user.

If the problem description is sufficiently complete, the system proceeds to mathematical formalization.

Formalization and Model Spec / IR Creation (FORMALIZER)
The business problem is transformed into a structured intermediate representation of the optimization problem, including sets, parameters, decision variables, objective function, and constraints.

Model Validation (VALIDATOR)
The Model Spec is checked for both mathematical and semantic consistency.

If an error or inconsistency is detected, the specification is sent back to the Formalizer for correction.

If the model is valid, it is passed to the Router and then to the Model Builder.

Optimization Model Construction (MODEL BUILDER)
The Model Spec is converted into an executable optimization model compatible with the selected solver.

Solver Execution (SOLVER EXECUTOR)
The solver executes the model and may return several statuses:

OPTIMAL: an optimal solution has been found;

FEASIBLE: a feasible solution has been found, without proof of optimality;

INFEASIBLE: no solution satisfies all constraints simultaneously;

ERROR / UNBOUNDED: an execution error occurred or the optimization problem is unbounded.

If the model is INFEASIBLE, an INFEASIBILITY ANALYZER investigates the cause of infeasibility in order to identify the constraints, or combinations of constraints, responsible for the conflict.

The solver output, together with any information produced by the infeasibility analysis, is then passed to the RESULT ANALYZER, which interprets the technical optimization results and extracts the relevant information.

Finally, the EXPLAINER converts these technical results into a user-friendly response, explaining the proposed solution, the main decisions made by the optimization model, and, when applicable, the reasons why the model is infeasible.





Stack: LangGraph to build the agent, Mistral 3B for user interaction and completeness, and devstral to build the OR model and code.



Here are the global specs of the project :

Design and implement an agentic system that lets an end user model, solve, and interrogate operations-research problems through natural 
conversation - with no optimization expertise required from them.
Natural language → model - Turn an ambiguous, plain-language brief into a well-formed model (variables, constraints, objective). 
Ask for clarification when needed. We recommend using an open source optimization framework like OR-Tools or Pyomo.
Solve autonomously - Select and guide an appropriate solver end-to-end, then explain the result back in the user's terms. You can 
pick the open source solver of your choice. 
Handle infeasibilities - Detect infeasible or unbounded models, localize the cause, and propose or apply relaxations with the 
trade-offs made explicit.
Build scenarios - Support problem modifications (e.g. new constraint), and side-by-side comparison of scenarios through 
conversation.
Engineer for trust - Make results verifiable, and describe how you'd evaluate correctness and robustness at scale. 
You choose the architecture, frameworks, models, and solvers - we care about how you reason, what features you develop, how you structure, not a prescribed design.
Test your approach - You should test your approach on the Warehouse Network Optimization problem provided to you. Though, 
your system must not overfit this problem.