"""Explain the optimization result to the user in business terms.

The agent receives the business rules, the result, a summary of the data,
the exact constraint margins and the solved scenarios. The graph node
calling it lives in the orchestrator.
"""

from agentic_tools.explain.ExplainOutput import ExplainOutput
from agentic_tools.model.context import items_block
from agentic_tools.utils import MistralAgent, llm_retry
from data_model.AgentState import AgentState
from data_model.ConstraintMargin import ConstraintMargin
from data_model.OptimisationResult import OptimizationResult
from data_model.prompts import EXPLAIN_PROMPT
from data_model.settings import Settings


def data_summary(result: OptimizationResult) -> str:
    """Give the size, range and total of every loaded parameter."""
    lines = []
    for symbol in result.parameters:
        values = [item.value for item in symbol.values]
        if values:
            lines.append(f"- {symbol.name}: {len(values)} values, "
                         f"min {min(values):g}, max {max(values):g}, "
                         f"total {sum(values):g}")
    return "\n".join(lines)


def solution_summary(result: OptimizationResult, settings: Settings) -> str:
    """Count and list the nonzero values of every decision variable."""
    listed = settings.explain.listed_values
    lines = []
    for symbol in result.variables:
        values = [f"{','.join(item.index)}={item.value:g}"
                  for item in symbol.values]
        shown = ", ".join(values[:listed])
        more = " ..." if len(values) > listed else ""
        lines.append(f"- {symbol.name}: {len(values)} nonzero values, "
                     f"total {sum(i.value for i in symbol.values):g}: "
                     f"{shown}{more}")
    return "\n".join(lines) or "no solution"


def margins_text(margins: list[ConstraintMargin]) -> str:
    """Describe the margin left on each rule, or say it is unavailable."""
    lines = [f"- {m.rule}: {m.binding} of {m.constraints} constraints at "
             f"their limit, {m.constraints - m.binding} with room left; "
             f"smallest margin {m.margin:g} ({m.tightest})"
             for m in margins]
    return "\n".join(lines) or "not available"


def explain_context(
    state: AgentState,
    margins: list[ConstraintMargin],
    settings: Settings,
) -> str:
    """Describe the problem, the result and the scenarios to explain."""
    spec, result = state.model_spec, state.optimization_result
    if spec is None or result is None:
        raise ValueError("Nothing to explain without a solved model.")

    business = state.business_spec
    objectives = "\n".join(f"- {o.id}: {o.interpretation or o.original_text}"
                           for o in business.objectives)
    rules = "\n".join(f"- {r.id} ({r.hardness.value}): "
                      f"{r.interpretation or r.original_text}"
                      for r in business.business_constraints)
    scenarios = "\n\n".join(f"{s.id} - {s.description}\n{s.summary}"
                            for s in state.scenarios)

    return "\n\n".join([
        f"PROBLEM: {business.problem_summary or ''}",
        f"OBJECTIVES:\n{objectives}",
        f"BUSINESS RULES:\n{rules}",
        items_block("MODEL PARAMETERS", spec.parameters),
        f"MODEL OBJECTIVE: {spec.direction} {spec.objective}",
        items_block("MODEL CONSTRAINTS", spec.constraints),
        f"STATUS: {result.status}, objective {result.objective_value}",
        "SOLUTION (nonzero values by variable):\n"
        + solution_summary(result, settings),
        f"DATA SUMMARY:\n{data_summary(result)}",
        f"CONSTRAINT MARGINS:\n{margins_text(margins)}",
        f"SCENARIOS:\n{scenarios}",
        f"PREVIOUS ASSISTANT REPLY:\n{state.reply or 'none'}",
        f"USER REQUEST:\n{state.messages[-1].content}"])


class AgentExplain(MistralAgent):
    """Explain the result, its margins and the possible relaxations.

    Its attributes are those of MistralAgent.
    """

    @llm_retry(understanding=True)
    async def explain(
        self,
        state: AgentState,
        margins: list[ConstraintMargin],
    ) -> ExplainOutput:
        """
        Explain the last result in the terms of the user.

        Parameters
        ----------
        state:
            Current state, holding the result and the scenarios.
        margins:
            Margins of the solution on each rule; empty without solution.

        Returns
        -------
        ExplainOutput
            Structured explanation of the result.
        """
        return await self.parse(
            [{"role": "system", "content": EXPLAIN_PROMPT},
             {"role": "user", "content": explain_context(
                 state, margins, self.settings)}],
            ExplainOutput)
