"""Launch the optimization agent and chat with it from the terminal."""

import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from mistralai.client import Mistral

from agentic_tools.completeness.AgentComplete import AgentCompleteness
from agentic_tools.understand.AgentUnderstand import AgentUnderstanding
from interactions.Conversation import ConversationSession
from interactions.data_files import describe_folder
from interactions.terminal import run_chat
from orchestrator.graph_orchestrator import AgentGraph
from parameters import load_settings


def parse_arguments() -> argparse.Namespace:
    """Read the command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="print the state changed by each node")
    parser.add_argument("-d", "--data", type=Path,
                        help="folder of the CSV input files")
    return parser.parse_args()


def main() -> None:
    """Build the agent graph and start the terminal chat."""
    arguments = parse_arguments()
    load_dotenv()
    settings = load_settings()
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    model = settings.models.understanding
    graph = AgentGraph(AgentUnderstanding(client, settings, model),
                       AgentCompleteness(client, settings, model),
                       settings).compile()
    data_schema = describe_folder(arguments.data) if arguments.data else ""
    session = ConversationSession(graph, arguments.verbose, data_schema)
    try:
        asyncio.run(run_chat(session))
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
