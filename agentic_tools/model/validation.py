"""Validate the reports of the generated code against the model spec."""

from typing import Any

from data_model.MathematicalStructure import MathematicalStructure


def is_number(value: object) -> bool:
    """Tell whether a JSON value is a number."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def symbol_errors(
    name: str,
    item: dict[str, list[Any]],
    elements: set[str],
) -> list[str]:
    """Check that a loaded set or parameter is filled and consistent."""
    if "elements" in item:
        return [] if item["elements"] else [f"Set {name} is empty."]
    entries = item["entries"]
    if not entries:
        return [(f"Parameter {name} is empty. Usual causes: iterating a "
                 "csv.DictReader that is already exhausted, or a wrong "
                 "column name.")]
    invalid = [index for index, value in entries if not is_number(value)]
    unknown = sorted({e for index, _ in entries for e in index} - elements)
    errors = []
    if invalid:
        errors.append(f"Parameter {name} has {len(invalid)} non-numeric "
                      f"values, e.g. at index {invalid[0]}.")
    if unknown:
        errors.append(f"Parameter {name} uses identifiers missing from "
                      f"every set, e.g. {unknown[:3]}.")
    return errors


def data_errors(
    spec: MathematicalStructure,
    data: dict[str, dict[str, list[Any]]]) -> list[str]:
    """List the problems of the data returned by load_data."""

    elements = {element
        for item in data.values()
        for element in item.get("elements", [])}

    missing = [f"Key {item.name} is missing from the returned dict."
        for item in spec.sets + spec.parameters
        if item.name not in data]

    invalid = [error
               for name, item in data.items()
               for error in symbol_errors(name, item, elements)]

    return missing + invalid


def solve_errors(
    spec: MathematicalStructure,
    report: dict[str, Any],
) -> list[str]:
    """Compare the returned variable names with the expected ones."""
    expected = [item.name for item in spec.variables]
    returned = list(report["variables"])
    if set(expected) <= set(returned):
        return []
    return [
        (f"The returned variables dict has the keys {returned} but it "
         f"must have exactly the keys {expected}. Rename the keys, the "
         "Python variables and the OR-Tools variable names; keep the "
         "model.")
    ]


def bound_errors(rows: list[list[Any]], tolerance: float) -> list[str]:
    """
    Explain the constraints that the variable bounds make impossible.

    Such a constraint fails whatever the decisions, which usually reveals a
    unit error, for example a fraction compared with a quantity.

    Parameters
    ----------
    rows:
        Impossible rows of the solve report: name, lowest and highest
        reachable activity, lower and upper bound.
    tolerance:
        Relative gap under which a row is not reported.

    Returns
    -------
    list[str]
        One error naming the impossible constraints, or none.
    """
    examples = []
    for name, low, high, lower, upper in rows:
        if high < lower and lower - high > tolerance * max(1.0, abs(lower)):
            examples.append(f"{name}: its left-hand side is at most "
                            f"{high:g} but must be at least {lower:g}")
        elif low > upper and low - upper > tolerance * max(1.0, abs(upper)):
            examples.append(f"{name}: its left-hand side is at least "
                            f"{low:g} but must be at most {upper:g}")
    if not examples:
        return []
    return [
        (f"{len(examples)} constraints can never hold, whatever the "
         "decisions, given the bounds of the variables, e.g. "
         f"{'; '.join(examples[:3])}. Check the unit of each term against "
         "the variable descriptions, for example a fraction compared with "
         "a quantity, and fix the expression; keep the variable bounds.")
    ]
