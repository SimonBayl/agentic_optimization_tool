"""Ask for required specification fields left empty after completeness.

The checker owns every question prefixed C_CHECK_: it recreates them on each
run from the current state, so a gap disappears as soon as it is filled.
Business gaps are only checked here, after completeness, because questions
prefixed C_ do not stop the graph before the completeness review. The graph
node applying these checks is defined in orchestrator/graph_orchestrator.py.
"""

from data_model.AgentState import AgentState
from data_model.BusinessProblemSpec import (
    BusinessProblemSpec,
    ConstraintHardness,
)
from data_model.ClarificationState import ClarificationQuestion
from data_model.MathematicalStructure import MathematicalStructure
from data_model.prompts import FOLLOW_UP
from data_model.settings import Settings


def keep_gaps(candidates: list[tuple[str, bool, str]]) -> list[tuple[str, str]]:
    """Keep the key and question of every missing field."""
    return [(key, text) for key, missing, text in candidates if missing]


def business_gaps(spec: BusinessProblemSpec) -> list[tuple[str, str]]:
    """List the business information required before modelling."""
    undirected = [o.id for o in spec.objectives if o.direction is None]
    proposed = [a.description for a in spec.assumptions
                if a.status == "proposed" and a.source != "user"]
    unknown = [c.id for c in spec.business_constraints
               if c.hardness == ConstraintHardness.unknown]

    return keep_gaps([
        ("SUMMARY", not spec.problem_summary,
         "Could you summarize the problem you want to optimize?"),
        ("OBJECTIVES", not spec.objectives,
         "Which criterion do you want to optimize (cost, time, service…)?"),
        ("DIRECTION", bool(undirected),
         (f"For {', '.join(undirected)}, should it be minimized or "
          "maximized?")),
        ("ASSUMPTIONS", bool(proposed),
         f"Do you confirm the assumptions {', '.join(proposed)}?"),
        ("HARDNESS", bool(unknown),
         (f"Are the rules {', '.join(unknown)} mandatory, or can they be "
          "relaxed?"))])


def binding_errors(
    model: MathematicalStructure,
    data_schema: dict[str, dict[str, str]],
) -> list[str]:
    """List bindings whose symbol or column is unknown."""
    symbols = {item.name for item in model.sets + model.parameters}
    columns = {f"{table}.{column}" for table, fields in data_schema.items()
                for column in fields}

    return [f"{binding.symbol} → {binding.column}"
            for binding in model.data_bindings
            if binding.symbol not in symbols or binding.column not in columns]


def model_gaps(
    model: MathematicalStructure | None,
    data_schema: dict[str, dict[str, str]],
) -> list[tuple[str, str]]:
    """List the model fields required before formalization."""
    if not data_schema:
        return []
    if model is None:
        return [("MODEL", ("I could not build a model. Which decisions "
                           "must be made, and with which data?"))]
    invalid = binding_errors(model, data_schema)
    return keep_gaps([
        ("SETS", not model.sets,
         ("Which sets of elements (trucks, warehouses, customers…) should the "
          "model consider?")),
        ("PARAMETERS", not model.parameters,
         ("Which numerical data (costs, capacities, demands…) should the "
          "model use?")),
        ("VARIABLES", not model.variables,
         "Which decisions should the model make?"),
        ("OBJECTIVE", not model.objective or model.direction is None,
         ("How is the criterion to optimize computed, and should it be "
          "minimized or maximized?")),
        ("CONSTRAINTS", not model.constraints,
         "Which rules must the decisions comply with?"),
        ("BINDINGS", not model.data_bindings,
         ("Which columns of your files hold the data used by the "
          "model?")),
        ("BINDINGS_INVALID", bool(invalid),
         ("These bindings match no known column: "
          f"{'; '.join(invalid)}. Which columns should be used?"))])


def to_question(
    gap: tuple[str, str],
    state: AgentState,
    settings: Settings,
) -> ClarificationQuestion:
    """Create a check question, reworded once it was already asked."""
    key, text = gap
    identifier = f"{settings.clarification.check_prefix}{key}"
    if identifier in state.asked_questions:
        text = FOLLOW_UP + text
    return ClarificationQuestion(
        id=identifier,
        question=text,
        reason="Required field left empty.",
        related_to=key,
        required=key not in settings.clarification.optional_checks,
    )


def budget_spent(state: AgentState, settings: Settings) -> bool:
    """Tell whether the clarification budget of the user is used up."""
    asks = sum(len(texts) for texts in state.asked_questions.values())
    return asks >= settings.clarification.max_turns


def released(
    question: ClarificationQuestion,
    state: AgentState,
    settings: Settings,
) -> ClarificationQuestion:
    """Make optional a business question deferred or over budget.

    Questions of the checker stay required: the model cannot be built
    without the fields they ask for.
    """
    asks = len(state.asked_questions.get(question.id, []))
    deferred = question.id in state.deferred_question_ids and asks >= 1

    prefix = settings.clarification.check_prefix
    exhausted = ((deferred or budget_spent(state, settings))
                 and not question.id.startswith(prefix))

    if not exhausted:
        return question
    return question.model_copy(update={"required": False})
