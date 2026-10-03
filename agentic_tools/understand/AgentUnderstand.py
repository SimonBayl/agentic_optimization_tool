"""Extract the business specification from the conversation."""

from langchain_core.messages import AnyMessage
from mistralai.client import Mistral
from mistralai.client.models import SystemMessage, UserMessage

from agentic_tools.understand.OutputUnderstand import UnderstandingOutput
from agentic_tools.utils import llm_retry
from data_model.AgentState import AgentState
from data_model.prompts import UNDERSTAND_CONTEXT, UNDERSTAND_PROMPT
from parameters import Settings

ROLES = {"human": "User", "ai": "Agent"}


def transcript(messages: list[AnyMessage]) -> str:
    """Render the conversation as plain text for the prompt."""
    return "\n\n".join(f"{ROLES.get(message.type, message.type)}: "
                       f"{message.text}" for message in messages)


class AgentUnderstanding:
    """Call the LLM extracting the business spec and its questions."""

    def __init__(self, client: Mistral, settings: Settings) -> None:
        """
        Keep the client and the parameters of the calls.

        Parameters
        ----------
        client:
            Mistral API client.
        settings:
            Global parameters, holding the model name.
        """
        self.client = client
        self.settings = settings

    def context(self, state: AgentState, instruction: str) -> str:
        """Fill the context prompt with the current state."""
        return UNDERSTAND_CONTEXT.format(
            business_spec=state.business_spec.model_dump_json(indent=2),
            clarification_state=state.clarification_state
            .model_dump_json(indent=2),
            conversation=transcript(state.messages),
            instruction=instruction)

    @llm_retry(understanding=True)
    async def understand(self, state: AgentState,
                         instruction: str) -> UnderstandingOutput:
        """
        Extract the full new business spec from the conversation.

        Parameters
        ----------
        state:
            Current state of the agent.
        instruction:
            Turn instruction listing the asked and deferred questions.

        Returns
        -------
        UnderstandingOutput
            New business spec and clarification state of the turn.
        """
        response = await self.client.chat.parse_async(
            UnderstandingOutput,
            model=self.settings.models.understanding,
            temperature=self.settings.temperature,
            messages=[SystemMessage(content=UNDERSTAND_PROMPT),
                      UserMessage(content=self.context(state, instruction))])
        message = response.choices[0].message if response.choices else None
        parsed = message.parsed if message is not None else None
        if parsed is None:
            raise ValueError("The understanding model returned no output.")
        return parsed
