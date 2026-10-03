"""Define the strict output returned by the model builder."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

type SolveStatus = Literal[
    "optimal", "feasible", "infeasible", "unbounded",
    "not_solved", "undefined", "error"]


class SetElements(BaseModel):
    """Store the elements of a set loaded from the input data.

    Attributes
    ----------
    name:
        Symbol of the set in the model spec.
    elements:
        Identifiers of the elements, in file order.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    elements: list[str]


class IndexedValue(BaseModel):
    """Store one value with its index; an empty index means a scalar.

    Attributes
    ----------
    index:
        Set elements identifying the value, in the index order.
    value:
        Numeric value of the parameter or variable at this index.
    """

    model_config = ConfigDict(extra="forbid")

    index: list[str]
    value: float


class SymbolValues(BaseModel):
    """Store every indexed value of a parameter or a decision variable.

    Attributes
    ----------
    name:
        Symbol of the parameter or variable in the model spec.
    values:
        Every value with its index.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    values: list[IndexedValue]


class OptimizationResult(BaseModel):
    """Strict output of the model builder returned to the user.

    Attributes
    ----------
    status:
        Solver status, or error when the code could not be generated.
    objective_value:
        Value of the objective; None without a solution.
    sets:
        Sets loaded from the input data.
    parameters:
        Parameters loaded from the input data.
    variables:
        Nonzero values of the decision variables.
    spec_hash:
        Hash of the solved model spec, to skip an unchanged rebuild.
    attempts:
        Code generations used by both stages.
    error:
        Last error when the generation failed.
    data_code:
        Validated code of load_data, reused by the next builds.
    model_code:
        Validated code of build_model, base of the next modifications.
    data_hash:
        Hash of the data part of the spec, to reuse data_code.
    """

    model_config = ConfigDict(extra="forbid")

    status: SolveStatus
    objective_value: float | None = None
    sets: list[SetElements] = Field(default_factory=list)
    parameters: list[SymbolValues] = Field(default_factory=list)
    variables: list[SymbolValues] = Field(
        default_factory=list,
        description="Nonzero values of the decision variables.")
    spec_hash: str
    attempts: int
    error: str | None = None
    data_code: str = ""
    model_code: str = ""
    data_hash: str = ""
