"""Compute the constraint activities of a reported solution as JSON.

Run as ``python -I inspector.py <script> <data_dir>`` with the solution
values on stdin as ``{symbol: [[index, value], ...]}``. The model is
rebuilt but not solved again: each constraint activity is evaluated from
the reported values. The generated code output is sent to stderr; the
last stdout line is JSON.
"""

import json
import runpy
import sys
from contextlib import redirect_stdout
from pathlib import Path

from ortools.linear_solver import linear_solver_pb2, pywraplp


def solution(
    solver: pywraplp.Solver,
    variables: dict[str, object],
    values: dict[str, list[list]],
) -> list[float]:
    """Order the reported values like the solver variables, 0 if missing."""
    runner = Path(__file__).parent.parent / "model" / "runner.py"
    flatten = runpy.run_path(str(runner))["flatten"]
    known = {(name, tuple(index)): value
             for name, pairs in values.items() for index, value in pairs}
    point = [0.0] * solver.NumVariables()
    for name, item in variables.items():
        for index, var in flatten(item):
            point[var.index()] = known.get((name, tuple(index)), 0.0)
    return point


def activities(
    model: linear_solver_pb2.MPModelProto,
    point: list[float],
) -> list[dict[str, object]]:
    """Evaluate every constraint of the model at the given point."""
    return [{"name": row.name,
             "activity": sum(point[i] * c for i, c in zip(
                 row.var_index, row.coefficient, strict=True)),
             "lower": row.lower_bound,
             "upper": row.upper_bound}
            for row in model.constraint]


def inspect(script: str, data_dir: str) -> list[dict[str, object]]:
    """Rebuild the model and evaluate its constraints on the solution."""
    values = json.load(sys.stdin)
    with redirect_stdout(sys.stderr):
        namespace = runpy.run_path(script, init_globals={"pywraplp": pywraplp})
        data = namespace["load_data"](Path(data_dir))
        solver, variables = namespace["build_model"](data)
    model = linear_solver_pb2.MPModelProto()
    solver.ExportModelToProto(model)
    return activities(model, solution(solver, variables, values))


if __name__ == "__main__":
    print(json.dumps(inspect(*sys.argv[1:3])))
