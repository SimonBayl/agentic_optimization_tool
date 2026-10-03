"""Record the solved scenarios and turn an explanation into a reply."""

from agentic_tools.explain.Explain import solution_summary
from agentic_tools.explain.ExplainOutput import ExplainOutput
from data_model.ModelPatch import ModelPatch
from data_model.OptimisationResult import OptimizationResult
from data_model.Relaxation import Relaxation
from data_model.Scenario import Scenario
from data_model.settings import Settings


def record_scenario(
    scenarios: list[Scenario],
    result: OptimizationResult,
    patch: ModelPatch | None,
    settings: Settings,
) -> list[Scenario]:
    """Add the result as a new scenario unless its spec was already solved."""
    if any(s.spec_hash == result.spec_hash for s in scenarios):
        return scenarios

    scenario = Scenario(
        id=f"S{len(scenarios) + 1}",
        description=(patch.summary if patch is not None and patch.operations
                     else "Initial model"),
        spec_hash=result.spec_hash,
        status=result.status,
        objective_value=result.objective_value,
        summary=(f"Status {result.status}, objective "
                 f"{result.objective_value}\n"
                 + solution_summary(result, settings)))

    return [*scenarios, scenario]


def relaxations_text(title: str, relaxations: list[Relaxation]) -> str:
    """List relaxations under a title, or return nothing without any."""
    lines = [f"- {r.rule_id}: {r.proposal} Trade-off: {r.trade_off}"
             for r in relaxations]
    return "\n".join([title, *lines]) if lines else ""


def explanation_text(output: ExplainOutput, full: bool = True) -> str:
    """Write the explanation as the paragraphs of the reply.

    Without full, only the answer and the comparison are written when the
    user asked for them, so that a question gets a focused reply.
    """
    comparison = output.scenario_comparison
    focused = [output.answer or "",
               f"Scenario comparison: {comparison}" if comparison else ""]

    if not full and any(focused):
        return "\n\n".join(part for part in focused if part)

    parts = [
        output.answer or "",
        f"Decisions: {output.variable_explanation}",
        f"Objective: {output.objective_explanation}",
        f"Constraint margins: {output.constraint_gaps}",
        relaxations_text("Possible gains:", output.possible_gains),
        relaxations_text("To find a solution:",
                         output.feasibility_recommendations),
        f"Scenario comparison: {comparison}" if comparison else ""]
    return "\n\n".join(part for part in parts if part)
