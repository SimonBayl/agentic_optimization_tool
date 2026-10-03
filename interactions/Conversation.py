"""Keep the agent state across the turns of a conversation."""

from dataclasses import replace

from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph

from data_model.AgentState import AgentState


class ConversationSession:
    """Submit user turns to the graph and keep the state history.

    Attributes
    ----------
    graph:
        Compiled graph processing a single user turn.
    verbose:
        Print the business spec and the clarifications after each turn.
    state:
        Current state of the agent.
    history:
        Previous states, used to undo the last turns.
    """

    def __init__(self, graph: CompiledStateGraph[AgentState],
                 verbose: bool = False) -> None:
        """
        Start an empty conversation.

        Parameters
        ----------
        graph:
            Compiled graph processing a single user turn.
        verbose:
            Print the internal understanding after each turn.
        """
        self.graph = graph
        self.verbose = verbose
        self.state = AgentState()
        self.history: list[AgentState] = []

    async def submit(self, message: str) -> str:
        """
        Run one turn of the graph on a user message.

        Parameters
        ----------
        message:
            Text sent by the user.

        Returns
        -------
        str
            Reply of the agent.
        """
        turn = replace(self.state, messages=[*self.state.messages,
                                             HumanMessage(content=message)])
        result = await self.graph.ainvoke(turn)
        self.history.append(self.state)
        self.state = AgentState(**result)
        if self.verbose:
            self.show_understanding()
        return self.state.reply

    def undo(self) -> bool:
        """Restore the state before the last turn, if any."""
        if not self.history:
            return False
        self.state = self.history.pop()
        return True

    def show_understanding(self) -> None:
        """Print the business spec and the clarification state."""
        print("\n[business spec]\n"
              + self.state.business_spec.model_dump_json(indent=2)
              + "\n\n[clarification state]\n"
              + self.state.clarification_state.model_dump_json(indent=2))
