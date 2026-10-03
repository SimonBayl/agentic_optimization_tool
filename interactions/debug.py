"""Print the agent state and its intermediate updates for debugging."""

import json
from dataclasses import fields
from typing import Any

from langchain_core.messages import BaseMessage
from pydantic import BaseModel

from data_model.AgentState import AgentState

HIDDEN = {"messages", "reply"}

Step = tuple[str, dict[str, Any]]


def to_json(value: object) -> object:
    """Convert a state value that json cannot serialize by itself."""
    if isinstance(value, BaseMessage):
        return f"{value.type}: {value.text}"
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(f"Cannot display {type(value).__name__}.")


def to_text(value: object) -> str:
    """Render a state field as indented JSON."""
    return json.dumps(value, indent=2, ensure_ascii=False, default=to_json)


def show_update(node: str, update: dict[str, Any] | None) -> None:
    """
    Print the fields of the state changed by one node.

    Parameters
    ----------
    node:
        Name of the node that ran.
    update:
        Fields returned by the node; the conversation is not repeated.
    """
    print(f"\n{'─' * 30} [{node}] {'─' * 30}")
    for key, value in (update or {}).items():
        if key not in HIDDEN:
            print(f"{key}:\n{to_text(value)}")


def show_steps(steps: list[Step]) -> None:
    """Replay the updates of every node run during the last turn."""
    if not steps:
        print("\nNo step recorded yet.")
    for node, update in steps:
        show_update(node, update)


def show_state(state: AgentState, names: list[str]) -> None:
    """
    Print fields of the state, all but the conversation by default.

    Parameters
    ----------
    state:
        Current state of the agent.
    names:
        Fields to print; empty to print every field but the hidden ones.
    """
    available = [field.name for field in fields(state)]
    unknown = [name for name in names if name not in available]
    if unknown:
        print(f"\nUnknown field: {', '.join(unknown)}. "
              f"Available: {', '.join(available)}.")
        return
    for name in names or [n for n in available if n not in HIDDEN]:
        print(f"\n{name}:\n{to_text(getattr(state, name))}")


def show_turn_state(state: AgentState) -> None:
    """Print every field of the state at the end of a turn."""
    turn = sum(message.type == "human" for message in state.messages)
    print(f"\n{'═' * 25} [agent state after turn {turn}] {'═' * 25}")
    show_state(state, [field.name for field in fields(state)])
