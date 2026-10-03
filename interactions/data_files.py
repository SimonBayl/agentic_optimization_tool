"""Describe the CSV files given by the user as a data schema."""

import csv
from pathlib import Path


def describe_file(path: Path) -> str:
    """Give the columns, the row count and a sample row of a CSV file."""
    with path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))
    header, body = rows[0], rows[1:]
    sample = ", ".join(f"{name}={value}"
                       for name, value in zip(header, body[0] if body else []))
    return (f"- {path.name}: columns {', '.join(header)}; "
            f"{len(body)} rows; example: {sample}")


def describe_folder(folder: Path) -> str:
    """
    Describe every CSV file of a folder.

    Parameters
    ----------
    folder:
        Folder holding the input data.

    Returns
    -------
    str
        One line per file, empty when the folder has no CSV file.
    """
    return "\n".join(describe_file(path)
                     for path in sorted(folder.glob("*.csv")))
