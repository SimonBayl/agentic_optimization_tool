"""Generate, execute and correct the optimization code in two stages.

Stage ``data`` writes load_data, which builds the sets and parameters of
the model spec. Once the loaded data is valid, stage ``solve`` writes
build_model, which formulates the model solved by the runner. Each failure
is fed back to the code generator until the attempts are exhausted.
The graph node calling the builder lives in the orchestrator.
"""

from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from typing import Any

from mistralai.client import Mistral

from agentic_tools.model.context import (
    base_code,
    data_context,
    model_context,
)
from agentic_tools.model.executor import code_errors, extract_code, run_stage
from agentic_tools.model.validation import (
    bound_errors,
    data_errors,
    solve_errors,
)
from agentic_tools.utils import llm_retry
from data_model.AgentState import AgentState
from data_model.MathematicalStructure import MathematicalStructure
from data_model.OptimisationResult import (
    IndexedValue,
    OptimizationResult,
    SetElements,
    SolveStatus,
    SymbolValues,
)
from data_model.prompts import (
    CODE_RETRY_PROMPT,
    DATA_PROMPT,
    MODEL_PROMPT,
    RETRY_HINT,
)
from data_model.settings import Settings

type Validator = Callable[[dict[str, Any]], list[str]]


def digest(text: str) -> str:
    """Hash a text to detect a changed specification."""
    return sha256(text.encode()).hexdigest()


def kept_code(previous: OptimizationResult | None) -> dict[str, str]:
    """Carry the last validated code over to a failed result."""
    if previous is None:
        return {}
    return previous.model_dump(include={"data_code", "model_code",
                                        "data_hash"})


class GenerationError(RuntimeError):
    """Signal a stage still failing after every attempt.

    Attributes
    ----------
    attempts:
        Generations spent on the failing stage.
    """

    def __init__(self, stage: str, error: str, attempts: int) -> None:
        super().__init__(f"{stage} stage: {error}")
        self.attempts = attempts


def change(state: AgentState) -> str:
    """Return the summary of the last model edit, if any."""
    patch = state.last_model_patch
    return patch.summary if patch is not None else ""


def symbol_values(name: str, pairs: list[list[Any]]) -> SymbolValues:
    """Convert runner index-value pairs into a strict symbol."""
    return SymbolValues(
        name=name,
        values=[IndexedValue(index=index, value=value)
                for index, value in pairs],
    )


def to_result(
    report: dict[str, Any],
    spec_hash: str,
    attempts: int,
) -> OptimizationResult:
    """Convert the solve report into the strict optimization result."""
    statuses: dict[str, SolveStatus] = {
        "OPTIMAL": "optimal",
        "FEASIBLE": "feasible",
        "INFEASIBLE": "infeasible",
        "UNBOUNDED": "unbounded",
        "NOT_SOLVED": "not_solved",
        "ABNORMAL": "undefined",
        "MODEL_INVALID": "undefined",
    }
    data = report["data"]
    return OptimizationResult(
        status=statuses[report["status"]],
        objective_value=report["objective"],
        sets=[SetElements(name=name, elements=item["elements"])
              for name, item in data.items() if "elements" in item],
        parameters=[symbol_values(name, item["entries"])
                    for name, item in data.items() if "entries" in item],
        variables=[symbol_values(name, pairs)
                   for name, pairs in report["variables"].items()],
        spec_hash=spec_hash,
        attempts=attempts,
    )


def summarize_result(result: OptimizationResult, settings: Settings) -> str:
    """Report the status, objective value and nonzero decisions."""
    max_lines = settings.clarification.max_result_lines
    lines = [f"Optimization status: {result.status}"]
    if result.error:
        lines.append(f"Error: {result.error[-500:]}")
        lines.append(RETRY_HINT)
    if result.objective_value is not None:
        lines.append(f"Objective value: {result.objective_value:,.2f}")
    decisions = [f"{symbol.name}[{', '.join(item.index)}] = {item.value:g}"
                 for symbol in result.variables
                 for item in symbol.values]
    lines += decisions[:max_lines]
    if len(decisions) > max_lines:
        lines.append(f"... {len(decisions) - max_lines} more values")
    return "\n".join(lines)


class AgentModelBuilder:
    """Write the optimization code with Mistral and correct it on errors.

    Attributes
    ----------
    client:
        Asynchronous Mistral client.
    data_dir:
        Folder of the input files read by the generated code.
    model:
        Name of the Mistral code model.
    max_attempts:
        Generations per stage before giving up.
    script:
        File where the generated code is written before its execution.
    max_tokens:
        Maximum length of the generated code.
    settings:
        Global parameters of the agent, read by llm_retry.
    """

    def __init__(
        self,
        api_key: str,
        data_dir: Path,
        settings: Settings) -> None:

        self.client = Mistral(api_key=api_key)
        self.data_dir = data_dir
        self.model = settings.models.code
        self.max_attempts = settings.model_builder.max_attempts
        self.script = Path(__file__).with_name("generated_model.py")
        self.max_tokens = settings.model_builder.max_tokens
        self.settings = settings

    @llm_retry()
    async def ask(self, messages: list[Any], attempt: int) -> str:
        """Request code, with more variety once a first attempt failed."""

        builder = self.settings.model_builder
        response = await self.client.chat.complete_async(
            model=self.model,
            messages=messages,
            temperature=(builder.temperature if attempt == 1
                         else builder.retry_temperature),
            max_tokens=self.max_tokens)

        message = response.choices[0].message
        content = message.content if message is not None else None

        if not isinstance(content, str):
            raise TypeError("Mistral returned no code")

        return content

    async def execute(
        self,
        stage: str,
        code: str,
        prefix: str,
        validate: Validator) -> tuple[dict[str, Any], str]:
        """Write the script, run it and validate its report."""
        function = {"data": "load_data", "solve": "build_model"}[stage]
        error = code_errors(code, function, self.settings)

        if error:
            return {}, error

        self.script.write_text(
            "\n\n".join(part for part in (prefix, code) if part) + "\n",
            encoding="utf-8")

        report, error = await run_stage(stage,
                                        self.script,
                                        self.data_dir,
                                        self.settings)

        return report, error or "\n".join(validate(report))

    async def generate(
        self,
        stage: str,
        context: str,
        validate: Validator,
        prefix: str = "",
    ) -> tuple[str, dict[str, Any], int]:
        """
        Generate a stage until its code runs and its report is valid.

        Parameters
        ----------
        stage:
            ``data`` for load_data or ``solve`` for build_model.
        context:
            Model spec and data description given to the generator.
        validate:
            Return the problems found in the execution report.
        prefix:
            Previously validated code written before the generated one.

        Returns
        -------
        tuple[str, dict[str, Any], int]
            Validated code, its execution report and the attempts used.
        """
        prompt = {"data": DATA_PROMPT, "solve": MODEL_PROMPT}[stage]
        messages = [{"role": "system", "content": prompt},
                    {"role": "user", "content": context}]

        code, error = "", ""
        for attempt in range(1, self.max_attempts + 1):
            feedback = [
                {"role": "assistant", "content": f"```python\n{code}\n```"},
                {"role": "user",
                 "content": CODE_RETRY_PROMPT.format(error=error)},
            ] if error else []
            code = extract_code(await self.ask([*messages, *feedback],
                                               attempt))
            report, error = await self.execute(stage, code, prefix, validate)
            if not error:
                return code, report, attempt

        raise GenerationError(stage, error, self.max_attempts)

    async def load_data(
        self,
        spec: MathematicalStructure,
        state: AgentState,
        data_hash: str) -> tuple[str, dict[str, Any], int]:
        """Reuse the data code when the data spec is unchanged."""

        previous = state.optimization_result
        if previous is not None and previous.data_hash == data_hash:
            report, error = await self.execute(
                "data", previous.data_code, "",
                lambda report: data_errors(spec, report["data"]))
            if not error:
                return previous.data_code, report, 0

        return await self.generate(
            "data",
            data_context(spec, self.data_dir, state.data_schema,
                         self.settings)
            + base_code(previous.data_code if previous else "", change(state)),
            lambda report: data_errors(spec, report["data"]))

    async def solve(
        self,
        spec: MathematicalStructure,
        state: AgentState,
        spec_hash: str) -> OptimizationResult:
        """Load and validate the data, then formulate and solve the model."""

        data_hash = digest(spec.model_dump_json(
            include={"sets", "parameters", "data_bindings"}))
        data_code, report, data_attempts = await self.load_data(
            spec, state, data_hash)

        previous = state.optimization_result

        model_code, report, model_attempts = await self.generate(
            "solve",
            model_context(spec, state.business_spec, report["data"],
                          self.settings)
            + base_code(previous.model_code if previous else "",
                        change(state)),
            lambda report: solve_errors(spec, report) + bound_errors(
                report["impossible"], self.settings.explain.tolerance),
            prefix=data_code)

        return to_result(report, spec_hash, data_attempts +
                         model_attempts).model_copy(
                update={"data_code": data_code,
                        "model_code": model_code,
                        "data_hash": data_hash})
