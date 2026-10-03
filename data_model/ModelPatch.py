"""Describe a modification of an existing model spec."""

from typing import Literal

from pydantic import BaseModel, Field


class PatchOperation(BaseModel):
    """Add, replace or remove one element of the model spec.

    Attributes
    ----------
    target:
        Field of the model spec to modify.
    action:
        Whether the element is added, replaced or removed.
    name:
        Exact name of the element; minimize or maximize for the objective;
        the symbol for a data binding.
    description:
        New description; the expression for the objective; the
        file.column for a data binding; empty for a removal.
    """

    target: Literal[
        "sets", "parameters", "variables", "constraints", "data_bindings",
        "objective"]
    action: Literal["add", "replace", "remove"]
    name: str = Field(
        description="Exact name of the element; for objective, the "
        "direction minimize or maximize; for data_bindings, the symbol.")
    description: str = Field(
        description="New description; for objective, the expression; for "
        "data_bindings, the file.column; empty for remove.")


class ModelPatch(BaseModel):
    """Smallest set of operations implementing a user request.

    Attributes
    ----------
    operations:
        Operations applied in order; empty for a question or a retry.
    summary:
        One English sentence describing the change.
    question:
        Question asked when the request is ambiguous; no operation is
        applied then.
    """

    operations: list[PatchOperation] = Field(default_factory=list)
    summary: str = Field(
        description="One English sentence describing the change.")
    question: str | None = Field(
        default=None,
        description="Question asked when the request is ambiguous; no "
        "operation is applied then.")
