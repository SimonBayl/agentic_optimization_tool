"""Build the user messages of the two code generation stages."""

import re
from pathlib import Path
from typing import Any

from data_model.BusinessProblemSpec import BusinessProblemSpec
from data_model.MathematicalStructure import MathematicalStructure, NamedItem
from data_model.settings import Settings


def base_code(code: str, change: str) -> str:
    """Give previously validated code as the base of a modification."""

    if not code:
        return ""
    return (
        "\n\nPREVIOUS CODE (modify it rather than rewriting it, keep every "
        "part unrelated to the change; the specification above takes "
        f"precedence):\n```python\n{code}\n```\n"
        f"REQUESTED CHANGE: {change or 'align the code with the spec'}")


def items_block(title: str, items: list[NamedItem]) -> str:
    """Format named items as a titled list."""
    lines = [f"- {item.name}: {item.description}" for item in items]
    return "\n".join([f"{title}:", *lines])


def file_sample(path: Path, settings: Settings) -> str:
    """Return the header and the first rows of a data file."""
    rows = settings.model_builder.sample_rows
    with path.open(encoding="utf-8-sig") as source:
        return "".join(line for _, line in zip(range(rows + 1), source))


def files_block(
    data_dir: Path,
    schema: dict[str, dict[str, str]],
    settings: Settings,
) -> str:
    """Describe every data file with its column meanings and a sample."""
    blocks = []
    for name, columns in schema.items():
        meanings = "\n".join(
            f"- {column}: {meaning}" for column, meaning in columns.items()
        )
        blocks.append(
            f"FILE {name}\nColumns:\n{meanings}\nFirst rows:\n"
            f"{file_sample(data_dir / name, settings)}"
        )
    return "\n\n".join(blocks)


def data_context(
    spec: MathematicalStructure,
    data_dir: Path,
    schema: dict[str, dict[str, str]],
    settings: Settings,
) -> str:
    """Build the user message of the data loading stage."""
    bindings = "\n".join(
        f"- {binding.symbol} <- {binding.column}"
        for binding in spec.data_bindings)

    return "\n\n".join([items_block("SETS", spec.sets),
        items_block("PARAMETERS", spec.parameters),
        f"DATA BINDINGS (symbol <- file.column):\n{bindings}",
        files_block(data_dir, schema, settings)])


def describe_symbol(
    name: str,
    item: dict[str, list[Any]],
    settings: Settings,
) -> str:
    """Give the Python type of one loaded symbol, its size and samples."""
    if "elements" in item:
        values = item["elements"]
        return f"- {name}: list of {len(values)} str, e.g. {values[:3]}"

    entries = item["entries"]
    first = entries[0][0] if entries else []

    if len(entries) == 1 and not first:
        return f'- {name}: float, read as data["{name}"] == {entries[0][1]}'

    samples = {tuple(index) if len(index) > 1 else index[0]: value
               for index, value
               in entries[:settings.model_builder.sample_rows]}
    keys = ", ".join(f'"{element}"' for element in first)

    return (f"- {name}: dict of {len(entries)} floats, read as "
            f'data["{name}"][{keys}], e.g. {samples}')


def return_statement(spec: MathematicalStructure) -> str:
    """Write the return statement expected at the end of build_model."""
    pairs = ", ".join(
        f'"{item.name}": {re.sub(r"\W", "_", item.name)}'
        for item in spec.variables
    )
    return f"return solver, {{{pairs}}}"


def model_context(
    spec: MathematicalStructure,
    business: BusinessProblemSpec,
    data: dict[str, dict[str, list[Any]]],
    settings: Settings,
) -> str:
    """Build the user message of the optimization model stage."""

    rules = "\n".join(
        f"- {rule.id} ({rule.hardness.value}): "
        f"{rule.interpretation or rule.original_text}"
        for rule in business.business_constraints)

    loaded = "\n".join(
        describe_symbol(name, item, settings) for name, item in data.items())

    return "\n\n".join([
        f"PROBLEM: {business.problem_summary or ''}",
        f"LOADED DATA (keys of data):\n{loaded}",
        items_block("DECISION VARIABLES", spec.variables),
        f"DIRECTION: {spec.direction}\nOBJECTIVE: {spec.objective}",
        items_block("CONSTRAINTS", spec.constraints),
        f"BUSINESS RULES:\n{rules}",
        ("REQUIRED RETURN STATEMENT (copy it unchanged):\n"
         f"{return_statement(spec)}")])
