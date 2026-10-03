"""Define the solver-independent structure of the optimization model."""

from typing import Literal

from pydantic import BaseModel, Field


class NamedItem(BaseModel):
    """Name and describe one element of the mathematical structure.

    Attributes
    ----------
    name:
        Short symbol such as W, d_c or x_wc.
    description:
        Meaning, indices, domain or unit of the element.
    """

    name: str = Field(description="Short symbol such as W, d_c or x_wc.")
    description: str = Field(description="Meaning, indices, domain or unit.")


class DataBinding(BaseModel):
    """Link a set or parameter symbol to an input data column.

    Attributes
    ----------
    symbol:
        Name of a set or a parameter.
    column:
        Input column written as file.column, such as customers.csv.demand.
    """

    symbol: str = Field(description="Name of a set or a parameter.")
    column: str = Field(
        description="Input column written as file.column, such as "
        "customers.csv.demand.")


class MathematicalStructure(BaseModel):
    """Store equations, domains and mappings to available input columns.

    Lists replace dictionaries because the Mistral SDK forbids free keys in
    structured outputs.

    Attributes
    ----------
    sets:
        Sets of elements indexing the parameters and variables.
    parameters:
        Fixed values or coefficients, read from the data or given by the
        user.
    variables:
        Decision variables, with their domain and bounds.
    direction:
        Whether the objective is minimized or maximized.
    objective:
        Linear expression of the objective.
    constraints:
        Constraints, each named after its business rule ID.
    data_bindings:
        Links between the sets and parameters and the input columns.
    """

    sets: list[NamedItem] = Field(
        default_factory=list,
        description="Sets of elements indexing parameters and variables of "
        "a linear optimization model, related to the input data.")
    parameters: list[NamedItem] = Field(
        default_factory=list,
        description="Fixed values or coefficients of the linear "
        "optimization model, related to the input data.")
    variables: list[NamedItem] = Field(
        default_factory=list,
        description="Decision variables matching the business decisions, "
        "or auxiliary variables helping the model to be feasible.")
    direction: Literal["minimize", "maximize"] | None = None
    objective: str | None = Field(
        default=None,
        description="Linear combination of variables and parameters to be "
        "minimized or maximized.")
    constraints: list[NamedItem] = Field(
        default_factory=list,
        description="Rules the optimization model must follow, named after "
        "the business rule ID they come from.")
    data_bindings: list[DataBinding] = Field(
        default_factory=list,
        description="Mapping between the sets and parameters of the model "
        "and the columns of the input data provided by the user.")
