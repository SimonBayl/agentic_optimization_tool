"""Review model completeness using a dedicated mathematical prompt."""

from agentic_tools.completeness.OutputComplete import CompletenessOutput
from agentic_tools.utils import MistralAgent, llm_retry
from data_model.AgentState import AgentState
from data_model.ClarificationState import (
    ClarificationQuestion,
    ClarificationState,
)
from data_model.MathematicalStructure import MathematicalStructure
from data_model.prompts import COMPLETE_PROMPT, SCHEMA_QUESTION


def ask_schema() -> CompletenessOutput:
    """Ask for the data format instead of calling the LLM."""
    question = ClarificationQuestion(
        id="C_DATA_SCHEMA",
        question=SCHEMA_QUESTION,
        reason="Link the parameters to the data.")
    return CompletenessOutput(
        clarification_state=ClarificationState(pending_questions=[question]),
        model_spec=MathematicalStructure())


class AgentCompleteness(MistralAgent):
    """Review the business specification with an independent prompt.

    Its attributes are those of MistralAgent.
    """

    @llm_retry()
    async def complete(self, state: AgentState, data_schema: str,
                       instruction: str) -> CompletenessOutput:
        """
        Review missing information and propose a mathematical structure.

        Parameters
        ----------
        state:
            Current state of the agent.
        data_schema:
            Columns and meaning of each input file, empty when unknown.
        instruction:
            Turn instruction listing the asked and deferred questions.

        Returns
        -------
        CompletenessOutput
            Questions on the gaps and the best draft of the model spec.
        """
        if not data_schema:
            return ask_schema()
        context = "\n\n".join((
            state.business_spec.model_dump_json(),
            state.clarification_state.model_dump_json(),
            f"DATA SCHEMA: {data_schema}",
            self.format_messages(state.messages),
            instruction,
        ))
        return await self.parse(
            [{"role": "system", "content": COMPLETE_PROMPT},
             {"role": "user", "content": context}],
            CompletenessOutput)
