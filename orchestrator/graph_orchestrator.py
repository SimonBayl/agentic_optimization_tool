"""Define every node and route of the turn-based agent graph.

Each user message runs the graph once, from START to END. The routes read
the state to resume where the previous turn stopped: understanding and
completeness while questions remain, then building and explaining, then
editing the model or answering questions about its result.
"""

from dataclasses import replace
from functools import partial
from typing import Literal, cast

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agentic_tools.completeness.AgentComplete import AgentCompleteness
from agentic_tools.completeness.checker import (
    budget_spent,
    business_gaps,
    model_gaps,
    released,
    to_question,
)
from agentic_tools.edit.AgentEdit import AgentModelEditor
from agentic_tools.edit.patch import apply_patch, sync_rules
from agentic_tools.explain.Explain import AgentExplain
from agentic_tools.explain.margins import (
    constraint_activities,
    constraint_margins,
)
from agentic_tools.explain.report import explanation_text, record_scenario
from agentic_tools.model.builder import (
    AgentModelBuilder,
    GenerationError,
    digest,
    kept_code,
    summarize_result,
)
from agentic_tools.understand.AgentUnderstand import AgentUnderstanding
from data_model.AgentState import AgentState
from data_model.ClarificationState import ClarificationState
from data_model.OptimisationResult import OptimizationResult
from data_model.prompts import DEFERRED, EXPLAIN_FAILED, NEXT_STEPS
from data_model.settings import Settings
from orchestrator.dialogue import (
    merge_clarifications,
    pick_question,
    status,
    with_turn_instruction,
)


def route(
    state: AgentState,
    settings: Settings,
) -> Literal["reply", "complete"]:
    """Review completeness unless a required business question remains.

    Once the clarification budget is spent, completeness is reviewed anyway.
    """
    if budget_spent(state, settings):
        return "complete"
    blocking = [
        q for q in state.clarification_state.pending_questions
        if q.required and not q.id.startswith("C_")
        and q.id not in state.deferred_question_ids
    ]
    return "reply" if blocking else "complete"


def route_model(state: AgentState) -> Literal["build", "reply"]:
    """Build the optimization model once the specification is ready."""
    ready = state.clarification_state.ready_for_formalization
    return "build" if ready and state.model_spec is not None else "reply"


def route_turn(state: AgentState) -> Literal["edit", "understand"]:
    """Edit the generated model, or keep understanding the request."""
    built = state.optimization_result is not None
    return "edit" if built and state.model_spec is not None else "understand"


def route_edit(state: AgentState) -> Literal["check", "explain", "reply"]:
    """Rebuild after a spec change or a failed build, unless asking.

    A request changing nothing is a question about the result: it is
    answered by the explanation.
    """
    patch = state.last_model_patch
    if patch is not None and patch.question:
        return "reply"
    if not state.clarification_state.ready_for_formalization:
        return "check"
    result = state.optimization_result
    failed = result is not None and result.status == "error"
    changed = patch is not None and bool(patch.operations)
    return "check" if failed or changed else "explain"


def route_build(state: AgentState) -> Literal["explain", "reply"]:
    """Explain a new result, unless its code could not be generated."""
    result = state.optimization_result
    solved = result is not None and result.status != "error"
    return "explain" if solved else "reply"


class AgentGraph:
    """Hold the agentic tools and expose them as the nodes of the graph.

    Attributes
    ----------
    understander:
        Agent called by the understand node.
    reviewer:
        Agent called by the complete node.
    model_builder:
        Agent called by the build node.
    model_editor:
        Agent called by the edit node.
    explainer:
        Agent called by the explain node.
    settings:
        Global parameters read by the nodes and the routes.
    """

    def __init__(
        self,
        understander: AgentUnderstanding,
        reviewer: AgentCompleteness,
        model_builder: AgentModelBuilder,
        model_editor: AgentModelEditor,
        explainer: AgentExplain,
        settings: Settings) -> None:
        """
        Keep the tools called by the nodes.

        Parameters
        ----------
        understander:
            Agent extracting the business specification and its questions.
        reviewer:
            Agent checking completeness and proposing the model draft.
        model_builder:
            Agent generating and solving the optimization code.
        model_editor:
            Agent patching the model spec on every turn once a model has
            been built.
        explainer:
            Agent explaining the result, its margins and its scenarios.
        settings:
            Global parameters of the agent.
        """
        self.understander = understander
        self.reviewer = reviewer
        self.model_builder = model_builder
        self.model_editor = model_editor
        self.explainer = explainer
        self.settings = settings

    async def understand(self, state: AgentState) -> dict[str, object]:
        """Update the business spec and invalidate any previous model."""

        update = await self.understander.understand(
            with_turn_instruction(state))

        clarification = merge_clarifications(
            state.clarification_state,
            cast(ClarificationState, update["clarification_state"]))

        return {"business_spec": update["business_spec"],
                "clarification_state": clarification,
                "model_spec": None}

    async def complete(self, state: AgentState) -> dict[str, object]:
        """Review gaps and keep the model draft for the checker."""

        update = await self.reviewer.complete(with_turn_instruction(state))
        clarification = merge_clarifications(
            state.clarification_state,
            cast(ClarificationState, update["clarification_state"]))

        return {"clarification_state": clarification,
                "model_spec": update["model_spec"]}

    def check(self, state: AgentState) -> dict[str, object]:
        """Replace previous check questions with the current field gaps."""

        gaps = business_gaps(state.business_spec) + model_gaps(
            state.model_spec, state.data_schema)
        questions = [to_question(gap, state, self.settings) for gap in gaps]
        current = {question.id for question in questions}
        clarification = state.clarification_state
        prefix = self.settings.clarification.check_prefix

        kept = [released(q, state, self.settings)
                for q in clarification.pending_questions
                if not q.id.startswith(prefix)]
        pending = kept + questions

        resolved = [i for i in clarification.resolved_question_ids
                    if not i.startswith(prefix)]
        deferred = {i for i in state.deferred_question_ids
                    if not i.startswith(prefix) or i in current}

        return {
            "clarification_state": ClarificationState(
                pending_questions=pending,
                resolved_question_ids=resolved,
                ready_for_formalization=not any(q.required for q in pending)),
            "deferred_question_ids": deferred}

    async def build(self, state: AgentState) -> dict[str, object]:
        """Solve a new model spec and store its strict result."""

        if state.model_spec is None:
            return {}

        spec_hash = digest(state.model_spec.model_dump_json())
        previous = state.optimization_result

        if (previous is not None and previous.spec_hash == spec_hash
                and previous.status != "error"):
            return {}

        try:
            result = await self.model_builder.solve(
                state.model_spec, state, spec_hash)
        except GenerationError as error:
            result = OptimizationResult(
                status="error",
                spec_hash=spec_hash,
                attempts=error.attempts,
                error=str(error)).model_copy(update=kept_code(previous))

        return {"optimization_result": result}

    async def edit(self, state: AgentState) -> dict[str, object]:
        """Patch the current model spec, or keep it and ask a question."""

        if state.model_spec is None:
            return {}

        patch = await self.model_editor.propose(state, state.model_spec)
        result = state.optimization_result
        failed = result is not None and result.status == "error"

        if failed and not patch.question and not patch.operations:
            return {}

        if patch.question or not patch.operations:
            return {"last_model_patch": patch}

        return {"model_spec": apply_patch(state.model_spec, patch),
                "business_spec": sync_rules(state.business_spec, patch),
                "last_model_patch": patch}

    async def explain(self, state: AgentState) -> dict[str, object]:
        """Record the scenario, compute its margins and explain it."""
        result = state.optimization_result

        if result is None or state.model_spec is None:
            return {}

        scenarios = record_scenario(
            state.scenarios, result, state.last_model_patch, self.settings)
        solved = result.status in ("optimal", "feasible")
        activities = (await constraint_activities(
            result, self.model_builder.data_dir, self.settings)
            if solved else [])

        margins = constraint_margins(
            activities, state.model_spec, self.settings)

        try:
            output = await self.explainer.explain(
                replace(state, scenarios=scenarios), margins)
        # pylint: disable-next=broad-exception-caught
        except Exception as error:  # noqa: BLE001
            return {"scenarios": scenarios,
                    "explanation": EXPLAIN_FAILED.format(type(error).__name__)}

        patch = state.last_model_patch
        changed = patch is not None and bool(patch.operations)
        new = changed or len(scenarios) > len(state.scenarios)

        return {"scenarios": scenarios,
                "explanation": explanation_text(output, full=new)}

    def reply(self, state: AgentState) -> dict[str, object]:
        """Commit the question history and append the user-facing reply."""

        question, deferred = pick_question(state, self.settings)
        built = state.optimization_result is not None

        if built and question is not None and not question.required:
            question = None

        asked = {key: list(texts)
                 for key, texts in state.asked_questions.items()}
        parts = [] if built else [DEFERRED.format(identifier)
                                  for identifier in deferred]

        if question is not None:
            asked.setdefault(question.id, []).append(question.question)
            parts.append(question.question)
        elif state.optimization_result is None:
            parts += [state.business_spec.problem_summary or "",
                      status(state.clarification_state) +
                      "\n\n" + "You can give more details"]

        ready = state.clarification_state.ready_for_formalization
        patch = state.last_model_patch
        changed = patch is None or bool(patch.operations)

        if ready and changed and state.model_spec is not None:
            parts.append(state.model_spec.model_dump_json(indent=2))
        if ready and changed and state.optimization_result is not None:
            parts.append(summarize_result(state.optimization_result,
                                          self.settings))

        parts.append(state.explanation)

        if patch is not None and (patch.question or patch.operations):
            parts.insert(0, patch.question or f"Model change: {patch.summary}")
        if state.optimization_result is not None:
            parts.append(NEXT_STEPS)

        reply = "\n\n".join(part for part in parts if part)

        return {
            "messages": [*state.messages, AIMessage(content=reply)],
            "asked_questions": asked,
            "deferred_question_ids": state.deferred_question_ids
            | set(deferred),
            "reply": reply,
            "explanation": ""}

    def compile(self) -> CompiledStateGraph:
        """
        Wire the nodes into a graph ending each turn on one reply.

        Returns
        -------
        CompiledStateGraph
            Graph processing a single user turn.
        """

        builder = StateGraph(AgentState)
        builder.add_node("understand", self.understand)
        builder.add_node("complete", self.complete)
        builder.add_node("check", self.check)
        builder.add_node("reply", self.reply)
        builder.add_node("edit", self.edit)
        builder.add_node("build", self.build)
        builder.add_node("explain", self.explain)
        builder.add_conditional_edges(START, route_turn)
        builder.add_conditional_edges("edit", route_edit)
        builder.add_conditional_edges(
            "understand", partial(route, settings=self.settings),
            ["reply", "complete"])
        builder.add_edge("complete", "check")
        builder.add_conditional_edges("check", route_model)
        builder.add_conditional_edges("build", route_build)
        builder.add_edge("explain", "reply")
        builder.add_edge("reply", END)

        return builder.compile()
