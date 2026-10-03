"""Patch the model spec from a user request once code has been generated.

The editor never rebuilds the spec: it asks Mistral for the smallest patch
and validates it, so that unrelated elements stay unchanged. The graph node
applying the patch lives in the orchestrator.
"""

from typing import Any

from agentic_tools.edit.patch import patch_errors
from agentic_tools.model.builder import summarize_result
from agentic_tools.utils import MistralAgent, llm_retry
from data_model.AgentState import AgentState
from data_model.MathematicalStructure import MathematicalStructure
from data_model.ModelPatch import ModelPatch
from data_model.prompts import (
    EDIT_PROMPT,
    FAILED_QUESTION,
    PATCH_RETRY_PROMPT,
)
from data_model.settings import Settings


def edit_context(
    state: AgentState,
    spec: MathematicalStructure,
    settings: Settings,
) -> str:
    """Describe the current model and the latest user request."""
    result = state.optimization_result
    last = summarize_result(result, settings) if result else "none"
    return "\n\n".join([
        f"PROBLEM: {state.business_spec.problem_summary or ''}",
        f"CURRENT MODEL SPEC:\n{spec.model_dump_json(indent=2)}",
        f"DATA SCHEMA: {state.data_schema}",
        f"LAST RESULT:\n{last}",
        f"PREVIOUS ASSISTANT REPLY:\n{state.reply or 'none'}",
        f"USER REQUEST:\n{state.messages[-1].content}"])


class AgentModelEditor(MistralAgent):
    """Ask Mistral for a model patch and validate it before applying.

    Its attributes are those of MistralAgent.
    """

    @llm_retry()
    async def ask(self, messages: list[Any]) -> ModelPatch:
        """Request a structured patch."""
        return await self.parse(messages, ModelPatch)

    async def propose(
        self,
        state: AgentState,
        spec: MathematicalStructure) -> ModelPatch:
        """Return a valid patch, or a question once attempts are spent."""

        messages = [{"role": "system", "content": EDIT_PROMPT},
                    {"role": "user",
                     "content": edit_context(state, spec, self.settings)}]

        errors: list[str] = []
        for _ in range(self.settings.model_editor.max_attempts):

            patch = await self.ask(messages)
            errors = patch_errors(spec, patch)

            if not errors:
                return patch

            messages = [*messages[:2],
                {"role": "assistant", "content": patch.model_dump_json()},
                {"role": "user", "content": PATCH_RETRY_PROMPT.format(
                    errors="\n".join(errors))}]

        return ModelPatch(summary="The requested change could not be applied.",
                    question=FAILED_QUESTION.format(errors="; ".join(errors)))
