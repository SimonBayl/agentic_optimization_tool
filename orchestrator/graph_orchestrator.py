"""Wire the agentic tools into the LangGraph of the agent."""

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agentic_tools.understand.AgentUnderstand import AgentUnderstanding
from data_model.AgentState import AgentState
from data_model.prompts import DEFERRED, MORE_DETAILS
from orchestrator.clarifications import (
    merge_clarifications,
    pick_question,
    status,
    turn_instruction,
)
from parameters import Settings


class AgentGraph:
    """Hold the agentic tools and expose them as the nodes of the graph.

    Attributes
    ----------
    understander:
        Agent called by the understand node.
    settings:
        Global parameters read by the nodes and the routes.
    """

    def __init__(self, understander: AgentUnderstanding,
                 settings: Settings) -> None:
        """
        Keep the tools called by the nodes.

        Parameters
        ----------
        understander:
            Agent extracting the business specification and its questions.
        settings:
            Global parameters of the agent.
        """
        self.understander = understander
        self.settings = settings

    async def understand(self, state: AgentState) -> dict[str, object]:
        """Update the business spec and merge the clarifications."""
        update = await self.understander.understand(
            state, turn_instruction(state))
        clarification = merge_clarifications(state.clarification_state,
                                             update.clarification_state)
        return {"business_spec": update.business_spec,
                "clarification_state": clarification}

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
        builder.add_node("reply", self.reply)
        builder.add_edge(START, "understand")
        builder.add_edge("understand", "reply")
        builder.add_edge("reply", END)
        return builder.compile()
