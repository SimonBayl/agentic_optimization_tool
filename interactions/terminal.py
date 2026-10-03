"""Provide multiline terminal input for the existing conversation session."""

from interactions.Conversation import ConversationSession
from interactions.debug import show_state, show_steps, show_turn_state

HELP = (
    "\nPaste your message, then type /send on its own line.\n"
    "/state [field ...]: show the agent state, or some of its fields;\n"
    "/steps: show the intermediate states of the last turn;\n"
    "/debug: show or hide the intermediate states during each turn;\n"
    "/new: start over from scratch; /undo: revert the last turn;\n"
    "/help: show this help; /quit: exit.\n"
    "Ctrl+C or end of input: exit.\n")

COMMANDS = {"/quit", "/new", "/undo", "/state", "/steps", "/debug", "/help"}


def read_message() -> str:
    """Collect a message until /send, or return a session command."""
    lines: list[str] = []
    while True:
        line = input("You > " if not lines else "... > ")
        command = line.strip()
        words = command.split()
        if words and words[0] in COMMANDS:
            return command
        if command == "/send":
            message = "\n".join(lines).strip()
            if message:
                return message
            print("Type a message before sending it.")
            lines.clear()
        else:
            lines.append(line)


def inspect(session: ConversationSession, command: str) -> bool:
    """
    Run a command reading the session, without calling the agent.

    Parameters
    ----------
    session:
        Current conversation session.
    command:
        Command typed by the user, with its arguments.

    Returns
    -------
    bool
        True when the command was an inspection command.
    """
    name, *arguments = command.split()
    if name == "/state":
        show_state(session.state, arguments)
    elif name == "/steps":
        show_steps(session.steps)
    elif name == "/debug":
        session.verbose = not session.verbose
        shown = "shown" if session.verbose else "hidden"
        print(f"\nIntermediate states {shown} during each turn.")
    elif name == "/help":
        print(HELP)
    else:
        return False
    print()
    return True


async def run_chat(session: ConversationSession) -> None:
    """Submit terminal messages while retaining the conversation state."""
    print(HELP)

    while True:
        message = read_message()
        if inspect(session, message):
            continue
        if message == "/quit":
            print("Goodbye!")
            return
        if message == "/new":
            session = ConversationSession(
                session.graph, session.verbose,
                session.state.data_schema)
            print("\nNew conversation.\n")
            continue
        if message == "/undo":
            reverted = session.undo()
            print("\nReverted the last turn.\n" if reverted
                  else "\nNothing to undo.\n")
            continue
        print("\nAgent > Analyzing…", flush=True)
        try:
            reply = await session.submit(message)
        # pylint: disable-next=broad-exception-caught
        except Exception as error:  # noqa: BLE001
            print(f"\nError: {error}")
            print("Send your message again to retry.\n")
        else:
            show_turn_state(session.state)
            print(f"\nAgent > {reply}\n")
