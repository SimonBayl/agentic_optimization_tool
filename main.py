"""Launch a terminal conversation with the optimization backend."""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from agentic_tools.completeness.AgentComplete import AgentCompleteness
from agentic_tools.edit.AgentEdit import AgentModelEditor
from agentic_tools.explain.Explain import AgentExplain
from agentic_tools.model.builder import AgentModelBuilder
from agentic_tools.understand.AgentUnderstand import AgentUnderstanding
from data_model.settings import load_settings
from interactions.ConversationSession import ConversationSession
from interactions.data_schema import load_schema
from interactions.terminal import run_chat
from orchestrator.graph_orchestrator import AgentGraph


def main() -> int:
    """Read the parameters, build the agents, the graph and the session.

    The parameters file can be replaced with the AGENT_PARAMETERS
    environment variable.
    """
    load_dotenv()
    api_key = os.environ.get("MISTRAL_API_KEY", "").strip()
    default = Path(__file__).with_name("parameters.yaml")
    settings = load_settings(Path(os.environ.get("AGENT_PARAMETERS",
                                                 default)))
    models = settings.models
    data_dir = settings.model_builder.data_dir
    graph = AgentGraph(
        AgentUnderstanding(api_key, models.understanding, settings),
        AgentCompleteness(api_key, models.understanding, settings),
        AgentModelBuilder(api_key, data_dir, settings),
        AgentModelEditor(api_key, models.editor, settings),
        AgentExplain(api_key, models.explain, settings),
        settings)
    session = ConversationSession(
        graph.compile(),
        data_schema=load_schema(data_dir, settings),
        verbose=True,
    )
    asyncio.run(run_chat(session))
    return 0


if __name__ == "__main__":
    sys.exit(main())
