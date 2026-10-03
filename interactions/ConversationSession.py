"""Connect a chat conversation to the business-understanding graph."""

import json
from copy import deepcopy
from typing import Any, Protocol

from langchain_core.messages import HumanMessage

from data_model.AgentState import AgentState, create_initial_state


class ConversationGraph(Protocol):  # pylint: disable=too-few-public-methods
    """Accept compiled graphs and deterministic graph test doubles."""

    async def ainvoke(self, state: AgentState, /) -> dict[str, Any]:
        """Return the state produced for a user turn."""


def print_state(state: AgentState) -> None:
    """Display the committed business and clarification state."""

    items = [("BUSINESS SPEC", state.business_spec),
        ("CLARIFICATION STATE", state.clarification_state)]

    if state.model_spec is not None:
        draft = not state.clarification_state.ready_for_formalization
        label = "MODEL SPEC (draft)" if draft else "MODEL SPEC"
        items.append((label, state.model_spec))

    for label, value in items:
        print(label)
        print(json.dumps(value.model_dump(mode="json"),
                    indent=2,
                    ensure_ascii=False))

    if state.optimization_result is not None:
        result = state.optimization_result.model_dump(
            exclude={"parameters", "data_code", "model_code"})
        print("OPTIMIZATION RESULT")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    print("Deferred questions:",
        sorted(state.deferred_question_ids))


class ConversationSession:
    """Hold the committed state and forward each user turn to the graph.

    Attributes
    ----------
    graph:
        Compiled graph run once per user message.
    verbose:
        True to print the state after each turn.
    state:
        State committed after the last successful turn.
    history:
        Previous committed states, used by undo.
    """

    def __init__(
        self,
        graph: ConversationGraph,
        data_schema: dict[str, dict[str, str]] | None = None,
        verbose: bool = False,
    ) -> None:
        self.graph = graph
        self.verbose = verbose
        self.state = create_initial_state()
        self.state.data_schema = deepcopy(data_schema or {})
        self.history: list[AgentState] = []

    async def submit(self, message: str) -> str:
        """
        Run the graph on a user turn and commit its state on success.

        Parameters
        ----------
        message:
            User request or answer to the displayed question.

        Returns
        -------
        str
            Next clarification or acknowledgement of the specification.
        """
        prompt = message.strip()
        if not prompt:
            raise ValueError("The message cannot be empty.")
        turn = deepcopy(self.state)
        turn.messages.append(HumanMessage(content=prompt))
        result = await self.graph.ainvoke(turn)
        self.history.append(self.state)
        self.state = AgentState(**result)
        if self.verbose:
            print_state(self.state)
        return self.state.reply

    def undo(self) -> bool:
        """Restore the state preceding the last turn, if there is one."""
        if not self.history:
            return False
        self.state = self.history.pop()
        return True
