"""Keep the agent state across the turns of a conversation."""

from dataclasses import replace
from typing import Any, cast

from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph

from data_model.AgentState import AgentState
from interactions.debug import Step, show_update


class ConversationSession:
    """Submit user turns to the graph and keep the state history.

    Attributes
    ----------
    graph:
        Compiled graph processing a single user turn.
    verbose:
        Print the state changed by each node of the graph.
    state:
        Current state of the agent.
    history:
        Previous states, used to undo the last turns.
    steps:
        Updates returned by each node during the last turn.
    """

    def __init__(self, graph: CompiledStateGraph[AgentState],
                 verbose: bool = False, data_schema: str = "") -> None:
        """
        Start an empty conversation.

        Parameters
        ----------
        graph:
            Compiled graph processing a single user turn.
        verbose:
            Print the state changed by each node of the graph.
        data_schema:
            Columns of the input files, empty when not given yet.
        """
        self.graph = graph
        self.verbose = verbose
        self.state = AgentState(data_schema=data_schema)
        self.history: list[AgentState] = []
        self.steps: list[Step] = []

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
        result: dict[str, Any] = {}
        self.steps = []
        async for mode, chunk in self.graph.astream(
                turn, stream_mode=["updates", "values"]):
            data = cast(dict[str, Any], chunk)
            if mode == "values":
                result = data
            else:
                self.record(data)
        self.history.append(self.state)
        self.state = AgentState(**result)
        return self.state.reply

    def undo(self) -> bool:
        """Restore the state before the last turn, if any."""
        if not self.history:
            return False
        self.state = self.history.pop()
        self.steps = []
        return True

    def record(self, updates: dict[str, Any]) -> None:
        """Keep the updates of the nodes, printed live when verbose."""
        for node, update in updates.items():
            self.steps.append((node, update or {}))
            if self.verbose:
                show_update(node, update)
