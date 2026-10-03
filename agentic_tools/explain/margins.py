"""Measure the margin left by a solution on each business rule.

The model is rebuilt in a subprocess and each constraint is evaluated on
the reported solution values, without solving again: the margins are
exact for this solution and anyone can verify them from the values.
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from data_model.ConstraintMargin import ConstraintMargin
from data_model.MathematicalStructure import MathematicalStructure
from data_model.OptimisationResult import OptimizationResult
from data_model.settings import Settings


def solution_values(result: OptimizationResult) -> bytes:
    """Encode the nonzero variable values as the inspector input."""
    return json.dumps({
        symbol.name: [[item.index, item.value] for item in symbol.values]
        for symbol in result.variables}).encode()


async def inspect(
    script: Path,
    data_dir: Path,
    values: bytes,
    settings: Settings,
) -> bytes:
    """Run the inspector and return its output, empty on any failure."""
    inspector = Path(__file__).with_name("inspector.py")
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-I", str(inspector), str(script),
        str(data_dir.resolve()),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={"PATH": os.environ.get("PATH", "")})
    timeout = settings.model_builder.timeouts["data"]

    try:
        output, _ = await asyncio.wait_for(
            process.communicate(values), timeout)
    except TimeoutError:
        process.kill()
        await process.wait()
        return b""

    return output if process.returncode == 0 else b""


async def constraint_activities(
    result: OptimizationResult,
    data_dir: Path,
    settings: Settings,
) -> list[dict[str, Any]]:
    """
    Evaluate every constraint of the model on the reported solution.

    Parameters
    ----------
    result:
        Solved result holding the generated code and the variable values.
    data_dir:
        Folder containing the input files.
    settings:
        Global parameters, giving the time limit of the inspector.

    Returns
    -------
    list[dict[str, Any]]
        Name, activity, lower and upper bound of each constraint; empty
        when the evaluation fails, since margins are optional.
    """
    with tempfile.TemporaryDirectory() as folder:
        script = Path(folder) / "model.py"
        script.write_text(f"{result.data_code}\n\n{result.model_code}\n",
                          encoding="utf-8")
        output = await inspect(
            script, data_dir, solution_values(result), settings)
    lines = output.decode(errors="replace").splitlines()
    return json.loads(lines[-1]) if lines else []


def rule_of(name: str, rules: list[str]) -> str:
    """Return the longest rule name prefixing a constraint name."""
    return max((rule for rule in rules if name.startswith(rule)),
               key=len, default=name)


def margin(row: dict[str, Any]) -> float:
    """Return the distance between a constraint activity and its bounds."""
    return max(0.0, float(min(row["upper"] - row["activity"],
                              row["activity"] - row["lower"])))


def is_binding(row: dict[str, Any], tolerance: float) -> bool:
    """Tell whether a constraint is tight, relative to its closest bound."""
    upper_gap = row["upper"] - row["activity"]
    bound = row["upper"] if upper_gap <= margin(row) else row["lower"]
    return margin(row) <= tolerance * max(1.0, abs(bound))


def rule_margin(
    rule: str,
    rows: list[dict[str, Any]],
    settings: Settings,
) -> ConstraintMargin:
    """Summarize the margins of the constraints of one rule."""
    tightest = min(rows, key=margin)
    tolerance = settings.explain.tolerance
    return ConstraintMargin(
        rule=rule, constraints=len(rows),
        binding=sum(is_binding(row, tolerance) for row in rows),
        tightest=tightest["name"], margin=margin(tightest))


def constraint_margins(
    activities: list[dict[str, Any]],
    spec: MathematicalStructure,
    settings: Settings,
) -> list[ConstraintMargin]:
    """
    Group the constraint activities by rule and summarize their margins.

    A constraint is binding when its margin is at most the tolerance of
    the settings times the absolute value of its closest bound, or the
    tolerance itself for bounds below 1.

    Parameters
    ----------
    activities:
        Constraint activities returned by constraint_activities.
    spec:
        Model spec naming the rules, in the order of the report.
    settings:
        Global parameters, giving the binding tolerance.

    Returns
    -------
    list[ConstraintMargin]
        Margin of each rule, spec rules first, then unmatched constraints.
    """
    rules = [constraint.name for constraint in spec.constraints]
    groups: dict[str, list[dict[str, Any]]] = {rule: [] for rule in rules}
    for row in activities:
        groups.setdefault(rule_of(row["name"], rules), []).append(row)
    return [rule_margin(rule, rows, settings)
            for rule, rows in groups.items() if rows]
