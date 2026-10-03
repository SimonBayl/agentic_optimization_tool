"""Provide multiline terminal input for the existing conversation session."""

from interactions.Conversation import ConversationSession


def read_message() -> str:
    """Collect a message until /send, or return a session command."""
    lines: list[str] = []
    while True:
        line = input("You > " if not lines else "... > ")
        command = line.strip()
        if command in {"/quit", "/new", "/undo"}:
            return command
        if command == "/send":
            message = "\n".join(lines).strip()
            if message:
                return message
            print("Type a message before sending it.")
            lines.clear()
        else:
            lines.append(line)


async def run_chat(session: ConversationSession) -> None:
    """Submit terminal messages while retaining the conversation state."""
    print(
        "\nPaste your message, then type /send on its own line.\n"
        "/new: start over from scratch; /undo: revert the last turn; "
        "/quit: exit.\n"
        "Ctrl+C or end of input: exit.\n")

    while True:
        message = read_message()
        if message == "/quit":
            print("Goodbye!")
            return
        if message == "/new":
            session = ConversationSession(session.graph, session.verbose)
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
            print(f"\nAgent > {reply}\n")
