"""Extract the business specification from the conversation."""

from agentic_tools.understand.OutputUnderstand import UnderstandingOutput
from agentic_tools.utils import MistralAgent, llm_retry
from data_model.AgentState import AgentState
from data_model.prompts import UNDERSTAND_CONTEXT, UNDERSTAND_PROMPT


class AgentUnderstanding(MistralAgent):
    """Call the LLM extracting the business spec and its questions.

    Its attributes are those of MistralAgent.
    """

    def context(self, state: AgentState, instruction: str) -> str:
        """Fill the context prompt with the current state."""
        return UNDERSTAND_CONTEXT.format(
            business_spec=state.business_spec.model_dump_json(indent=2),
            clarification_state=state.clarification_state
            .model_dump_json(indent=2),
            conversation=self.format_messages(state.messages),
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
        return await self.parse(
            [{"role": "system", "content": UNDERSTAND_PROMPT},
             {"role": "user", "content": self.context(state, instruction)}],
            UnderstandingOutput)
