"""Review model completeness using a dedicated mathematical prompt."""

from agentic_tools.completeness.OutputComplete import CompletenessOutput
from agentic_tools.utils import MistralAgent, llm_retry
from data_model.AgentState import AgentState
from data_model.ClarificationState import (
    ClarificationQuestion,
    ClarificationState,
)
from data_model.prompts import COMPLETE_PROMPT, SCHEMA_QUESTION


class AgentCompleteness(MistralAgent):
    """Review the business specification with an independent prompt.

    Its attributes are those of MistralAgent.
    """

    @llm_retry()
    async def complete(self, state: AgentState) -> dict[str, object]:
        """Review missing information and propose a mathematical structure."""
        if not state.data_schema:
            question = ClarificationQuestion(
                id="C_DATA_SCHEMA",
                question=SCHEMA_QUESTION,
                reason="Link the parameters to the data.")
            return {
                "clarification_state": ClarificationState(
                    pending_questions=[question]),
                "model_spec": None,
            }
        context = "\n\n".join((
            state.business_spec.model_dump_json(),
            state.clarification_state.model_dump_json(),
            f"DATA SCHEMA: {state.data_schema}",
            self.format_messages(state.messages),
        ))
        parsed = await self.parse(
            [{"role": "system", "content": COMPLETE_PROMPT},
             {"role": "user", "content": context}],
            CompletenessOutput)
        return {
            "clarification_state": parsed.clarification_state,
            "model_spec": parsed.model_spec,
        }
