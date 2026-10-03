"""Describe a solved version of the model kept for comparisons."""

from pydantic import BaseModel

from data_model.OptimisationResult import SolveStatus


class Scenario(BaseModel):
    """Solved version of the model, kept to compare it with later ones.

    Attributes
    ----------
    id:
        Identifier such as S1, in the order of resolution.
    description:
        Change that led to this version, or Initial model.
    spec_hash:
        Hash of the solved model spec, to record each version once.
    status:
        Solver status of this version.
    objective_value:
        Value of the objective; None without a solution.
    summary:
        Status, objective value and main decisions of this version.
    """

    id: str
    description: str
    spec_hash: str
    status: SolveStatus
    objective_value: float | None = None
    summary: str
