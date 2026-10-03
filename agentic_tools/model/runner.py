"""Execute the generated model script and print its report as JSON.

Run as ``python -I runner.py <data|solve> <script> <data_dir> <time_limit>``
with the solver time limit in seconds. Only the
standard library and OR-Tools are imported so the generated code runs
alone. The model built with the pywraplp wrapper is solved by HiGHS.
The generated code output is sent to stderr; the last stdout line is JSON.
"""

import json
import runpy
import sys
from contextlib import redirect_stdout
from pathlib import Path

from ortools.linear_solver import linear_solver_pb2, pywraplp


def flatten(value: object, index: tuple[object, ...] = ()) -> list[list]:
    """Flatten nested or tuple-keyed dictionaries into index-value pairs."""
    if isinstance(value, dict):
        return [
            pair
            for key, item in value.items()
            for pair in flatten(
                item, index + (key if isinstance(key, tuple) else (key,))
            )
        ]
    return [[[str(element) for element in index], value]]


def encode(value: object) -> dict[str, list]:
    """Describe a loaded set as elements and a parameter as entries."""
    if isinstance(value, (list, tuple)):
        return {"elements": [str(element) for element in value]}
    return {"entries": flatten(value)}


def impossible_rows(model: linear_solver_pb2.MPModelProto) -> list[list]:
    """List the constraints that no value within the variable bounds meets.

    Each row is [name, lowest activity, highest activity, lower bound,
    upper bound], the activities being reachable within the variable bounds.
    """
    rows = []
    for row in model.constraint:
        low = high = 0.0
        for index, coefficient in zip(row.var_index, row.coefficient):
            if not coefficient:
                continue
            variable = model.variable[index]
            terms = (coefficient * variable.lower_bound,
                     coefficient * variable.upper_bound)
            low += min(terms)
            high += max(terms)
        if high < row.lower_bound or low > row.upper_bound:
            rows.append([row.name, low, high,
                         row.lower_bound, row.upper_bound])
    return rows


def solve(
    solver: pywraplp.Solver | None,
    variables: dict[str, object],
    time_limit: float,
) -> dict[str, object]:
    """Solve the model with HiGHS and keep the nonzero decision values."""
    statuses = {
        pywraplp.Solver.OPTIMAL: "OPTIMAL",
        pywraplp.Solver.FEASIBLE: "FEASIBLE",
        pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
        pywraplp.Solver.UNBOUNDED: "UNBOUNDED",
        pywraplp.Solver.ABNORMAL: "ABNORMAL",
        pywraplp.Solver.NOT_SOLVED: "NOT_SOLVED",
        pywraplp.Solver.MODEL_INVALID: "MODEL_INVALID",
    }

    if solver is None:
        raise RuntimeError('pywraplp.Solver.CreateSolver("HIGHS") returned '
                           "None: HiGHS is not available in OR-Tools.")

    model = linear_solver_pb2.MPModelProto()
    solver.ExportModelToProto(model)
    invalid = pywraplp.FindErrorInModelProto(model)

    if invalid:
        raise ValueError(f"OR-Tools rejected the model: {invalid}")

    parameters = pywraplp.MPSolverParameters()
    parameters.SetDoubleParam(parameters.RELATIVE_MIP_GAP, 0.0)
    solver.SetTimeLimit(int(time_limit * 1000))
    status = solver.Solve(parameters)
    solved = status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE)

    values = {name: [[index, var.solution_value()]
                     for index, var in flatten(item)
                     if solved and var.solution_value()]
              for name, item in variables.items()}

    return {
        "status": statuses[status],
        "objective": solver.Objective().Value() if solved else None,
        "variables": values,
        "impossible": impossible_rows(model),
    }


def report(
    stage: str,
    script: str,
    data_dir: str,
    time_limit: str,
) -> dict[str, object]:
    """Load the data and, for the solve stage, build and solve the model."""
    with redirect_stdout(sys.stderr):
        namespace = runpy.run_path(script, init_globals={"pywraplp": pywraplp})
        data = namespace["load_data"](Path(data_dir))
        result: dict[str, object] = {
            "data": {name: encode(value) for name, value in data.items()}
        }
        if stage == "solve":
            solver, variables = namespace["build_model"](data)
            result.update(solve(solver, variables, float(time_limit)))
    return result


if __name__ == "__main__":
    print(json.dumps(report(*sys.argv[1:5])))
