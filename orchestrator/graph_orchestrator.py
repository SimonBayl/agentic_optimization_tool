"""Wire the agentic tools into the LangGraph of the agent."""

from functools import partial
from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agentic_tools.completeness.AgentComplete import AgentCompleteness
from agentic_tools.completeness.checker import budget_spent
from agentic_tools.understand.AgentUnderstand import AgentUnderstanding
from data_model.AgentState import AgentState
from data_model.prompts import DEFERRED, MORE_DETAILS
from orchestrator.dialogue import (
    merge_clarifications,
    pick_question,
    schema_answer,
    status,
    turn_instruction,
)
from parameters import Settings


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


class AgentGraph:
    """Hold the agentic tools and expose them as the nodes of the graph.

    Attributes
    ----------
    understander:
        Agent called by the understand node.
    reviewer:
        Agent called by the complete node.
    settings:
        Global parameters read by the nodes and the routes.
    """

    def __init__(self, understander: AgentUnderstanding,
                 reviewer: AgentCompleteness, settings: Settings) -> None:
        """
        Keep the tools called by the nodes.

        Parameters
        ----------
        understander:
            Agent extracting the business specification and its questions.
        reviewer:
            Agent checking completeness and proposing the model draft.
        settings:
            Global parameters of the agent.
        """
        self.understander = understander
        self.reviewer = reviewer
        self.settings = settings

    async def understand(self, state: AgentState) -> dict[str, object]:
        """Update the business spec and invalidate any previous model."""
        update = await self.understander.understand(
            state, turn_instruction(state))
        clarification = merge_clarifications(state.clarification_state,
                                             update.clarification_state,
                                             "Q_")
        return {"business_spec": update.business_spec,
                "clarification_state": clarification,
                "model_spec": None}

    async def complete(self, state: AgentState) -> dict[str, object]:
        """Review gaps and keep the model draft for the formalizer."""
        data_schema = state.data_schema or schema_answer(state)
        update = await self.reviewer.complete(state, data_schema,
                                              turn_instruction(state))
        clarification = merge_clarifications(state.clarification_state,
                                             update.clarification_state,
                                             "C_")
        return {"clarification_state": clarification,
                "model_spec": update.model_spec,
                "data_schema": data_schema}

    def reply(self, state: AgentState) -> dict[str, object]:
        """Commit the question history and append the user-facing reply."""
        question, deferred = pick_question(state, self.settings)
        asked = {key: list(texts)
                 for key, texts in state.asked_questions.items()}
        parts = [DEFERRED.format(identifier) for identifier in deferred]

        if question is not None:
            asked.setdefault(question.id, []).append(question.question)
            parts.append(question.question)
        else:
            parts += [state.business_spec.problem_summary or "",
                      status(state.clarification_state),
                      MORE_DETAILS]

        reply = "\n\n".join(part for part in parts if part)
        return {"messages": [*state.messages, AIMessage(content=reply)],
                "asked_questions": asked,
                "deferred_question_ids": state.deferred_question_ids
                | set(deferred),
                "reply": reply}

    def compile(self) -> CompiledStateGraph[AgentState]:
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
        builder.add_node("reply", self.reply)
        builder.add_edge(START, "understand")
        builder.add_conditional_edges(
            "understand", partial(route, settings=self.settings),
            ["reply", "complete"])
        builder.add_edge("complete", "reply")
        builder.add_edge("reply", END)
        return builder.compile()
