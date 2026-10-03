"""Extract the business sense of the user's request."""

from agentic_tools.understand.OutputUnderstand import UnderstandingOutput
from agentic_tools.utils import MistralAgent, llm_retry
from data_model.AgentState import AgentState
from data_model.BusinessProblemSpec import BusinessProblemSpec
from data_model.ClarificationState import ClarificationState
from data_model.prompts import UNDERSTAND_CONTEXT, UNDERSTAND_PROMPT


class AgentUnderstanding(MistralAgent):
    """Define the agent interacting with the user to formalize the request.

    Its attributes are those of MistralAgent.
    """

    @llm_retry(understanding=True)
    async def understand(
        self, state: AgentState
    ) -> dict[str, BusinessProblemSpec | ClarificationState]:
        """
        Analyze the current conversation and update the business understanding.

        Parameters
        ----------
        state:
            Current LangGraph state.

        Returns
        -------
        dict
            Partial state update understood by LangGraph.
        """
        context = UNDERSTAND_CONTEXT.format(
            business_spec=state.business_spec.model_dump_json(indent=2),
            clarification_state=state.clarification_state.model_dump_json(
                indent=2),
            conversation=self.format_messages(state.messages))
        parsed = await self.parse(
            [{"role": "system", "content": UNDERSTAND_PROMPT},
             {"role": "user", "content": context}],
            UnderstandingOutput)
        return {
            "business_spec": parsed.business_spec,
            "clarification_state": parsed.clarification_state,
        }
