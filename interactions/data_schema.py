"""Expose input column meanings without loading data into LLM context."""

import csv
from pathlib import Path

from data_model.prompts import UNKNOWN_MEANING
from data_model.settings import Settings


def load_schema(
    directory: Path,
    settings: Settings) -> dict[str, dict[str, str]]:
    """Read actual CSV headers and attach the known column meanings."""
    meanings = settings.data_schema.meanings
    schema: dict[str, dict[str, str]] = {}
    for path in sorted(directory.glob("*.csv")):
        with path.open(encoding="utf-8-sig", newline="") as source:
            columns = csv.DictReader(source).fieldnames or []
        schema[path.name] = {
            column: meanings.get(column, UNKNOWN_MEANING)
            for column in columns
        }
    return schema
