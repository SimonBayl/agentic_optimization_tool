# model

Generates the optimization code with an LLM specialized in code
(`models.code`), runs it and solves the model with OR-Tools (pywraplp
wrapper, HiGHS solver).

## Two stages

1. data: the LLM writes `load_data(data_dir: Path) -> dict` (DATA_PROMPT),
   returning one key per set and parameter, named after the symbol. A set
   is a list of str in file order, without duplicates; a parameter is a
   float, a dict keyed by str, or a dict keyed by tuples in the index
   order. Each file is read once with csv, pathlib and math only. It is
   given the sets, parameters, data bindings, column meanings and the
   first `sample_rows` rows of each file.
2. solve: the LLM writes `build_model(data) -> (solver, variables)`
   (MODEL_PROMPT). It is given the problem, the Python type, size and
   samples of each loaded symbol, the variables, direction, objective and
   constraints, the business rules and the required return statement.
   The solver is `CreateSolver("HIGHS")`; the objective is set before the
   constraints; each constraint is named `<constraint name>_<indices>`,
   which lets explain group the margins by rule; `variables` maps each
   spec variable name to its OR-Tools variables. The code never solves
   nor prints.

The answer is a fenced block; the last block is kept (extract_code). Each
stage is checked, run and validated; the error is fed back
(CODE_RETRY_PROMPT) until `model_builder.max_attempts`, then a
GenerationError is raised and the build node stores a result with the
status `error`. The first attempt uses `temperature`, the next ones
`retry_temperature`.

## Reuse

- `spec_hash` is the sha256 of the spec JSON; `data_hash` that of its
  sets, parameters and bindings.
- The data code is rerun without LLM when `data_hash` is unchanged and
  still valid (0 attempts counted).
- After an edit, the previous code and the patch summary are given as a
  base to modify rather than rewrite (base_code).
- The build node skips the build when the spec was already solved.

## Checks

- Before running (code_errors): syntax, imports in `allowed_imports`, no
  name of `forbidden_names`, expected function defined at top level. An
  AST check, not a security sandbox.
- During the run: `python -I` subprocess with only PATH in its
  environment, killed after `timeouts.<stage>` seconds; the solver stops
  after `time_limit` seconds with a relative MIP gap of 0. The prints of
  the generated code go to stderr; the last `error_tail` characters of
  stderr are fed back on failure.
- After the data stage (data_errors): every set and parameter of the spec
  is returned, sets and parameters are not empty, values are numeric and
  every index element belongs to a set.
- After the solve stage: every spec variable is a key of `variables`
  (solve_errors), and no constraint is impossible within the variable
  bounds (bound_errors, relative tolerance `explain.tolerance`), which
  usually reveals a unit error.

The solver statuses map to optimal, feasible, infeasible, unbounded,
not_solved, or undefined (abnormal, invalid model). An infeasible or
unbounded model is a valid result, not an error: it is passed to the
explain tool. Only the nonzero variable values are kept.

## Files

- builder.py: AgentModelBuilder, the generation loop of both stages, the
  conversion of the report into an OptimizationResult (to_result) and
  the result summary of the reply (summarize_result, at most
  `max_result_lines` values).
- context.py: the user messages of both stages (spec, data sample,
  previous code, return statement).
- executor.py: the code checks and the subprocess execution.
- runner.py: subprocess entry point
  `runner.py <data|solve> <script> <data_dir> <time_limit>`; the last
  stdout line is a JSON report: data, status, objective, nonzero values
  and impossible rows.
- validation.py: checks of the reports against the spec.
- generated_model.py: last generated code, overwritten on each run;
  excluded from the linters, never edited by hand.
