"""Define the structured output of the explanation agent."""

from pydantic import BaseModel, Field

from data_model.Relaxation import Relaxation


class ExplainOutput(BaseModel):
    """Explain the optimization result in the terms of the user.

    Attributes
    ----------
    variable_explanation:
        Decisions of the solution, summarized in business terms.
    objective_explanation:
        What is optimized and the value reached.
    constraint_gaps:
        Rules fully used and rules leaving room, from the margins.
    possible_gains:
        Relaxations of binding rules likely to improve the objective.
    feasibility_recommendations:
        Relaxations restoring a solution when the model is infeasible
        or unbounded.
    scenario_comparison:
        Comparison of the scenarios, only when the user asks for it.
    answer:
        Direct answer to the latest question of the user, if any.
    """

    variable_explanation: str
    objective_explanation: str
    constraint_gaps: str
    possible_gains: list[Relaxation] = Field(default_factory=list)
    feasibility_recommendations: list[Relaxation] = Field(
        default_factory=list)
    scenario_comparison: str | None = None
    answer: str | None = None
