"""Load the global parameters of the agent from parameters.yaml.

The file is read once by main, and the resulting Settings object is passed
to every class and function needing a parameter: no module holds a global
value. To add a parameter, add its key to the YAML file and a typed field
to the matching section below.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Section(BaseModel):
    """Reject unknown keys and forbid changes after loading."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class Models(Section):
    """Name the Mistral model used by each agent.

    Attributes
    ----------
    understanding:
        Model of the understanding and completeness agents.
    code:
        Model writing the optimization code.
    editor:
        Model editing the model spec.
    explain:
        Model explaining the results to the user.
    """

    understanding: str
    code: str
    editor: str
    explain: str


class Llm(Section):
    """Configure the understanding and completeness requests.

    Attributes
    ----------
    temperature:
        Sampling temperature of the structured requests.
    max_tokens:
        Maximum length of an answer.
    """

    temperature: float
    max_tokens: int


class Retry(Section):
    """Configure the retries of transient API errors.

    Attributes
    ----------
    max_retries:
        Retries of the completeness, editor and code requests.
    understanding_max_retries:
        Retries of the understanding request.
    understanding_base_delay:
        First backoff of the understanding retries, in seconds.
    understanding_max_delay:
        Maximum backoff of the understanding retries, in seconds.
    base_delay:
        First backoff of the other retries, in seconds.
    max_delay:
        Maximum backoff of the other retries, in seconds.
    """

    max_retries: int
    base_delay: float
    max_delay: float
    understanding_max_retries: int
    understanding_base_delay: float
    understanding_max_delay: float


class Clarification(Section):
    """Configure the dialogue with the user.

    Attributes
    ----------
    max_asks:
        Times a question is asked before being set aside.
    max_turns:
        Questions asked in total before the remaining business questions
        become optional and the model is built.
    check_prefix:
        Prefix of the identifiers of the questions asked by the checker.
    optional_checks:
        Checker questions that never block the formalization.
    max_result_lines:
        Decision values shown in the reply.
    """

    max_asks: int
    max_turns: int
    check_prefix: str
    optional_checks: tuple[str, ...]
    max_result_lines: int


class ModelBuilder(Section):
    """Configure the generation and execution of the optimization code.

    Attributes
    ----------
    data_dir:
        Folder of the input files, resolved from the parameters file.
    max_attempts:
        Generations per stage, each fed with the previous error.
    max_tokens:
        Maximum length of the generated code.
    temperature:
        Temperature of the first generation.
    retry_temperature:
        Temperature of the corrections, for more variety.
    sample_rows:
        Data rows shown to the code generator per file.
    error_tail:
        Characters of the error trace fed back to the generator.
    timeouts:
        Execution time limit of each stage, in seconds.
    time_limit:
        Time limit of the solver, in seconds.
    allowed_imports:
        Modules the generated code may import.
    forbidden_names:
        Builtins the generated code must not use.
    """

    data_dir: Path
    max_attempts: int
    max_tokens: int
    temperature: float
    retry_temperature: float
    sample_rows: int
    error_tail: int
    timeouts: dict[str, float]
    time_limit: float
    allowed_imports: frozenset[str]
    forbidden_names: frozenset[str]


class ModelEditor(Section):
    """Configure the edition of the model spec.

    Attributes
    ----------
    max_attempts:
        Requests to obtain a valid patch, each fed with the previous
        errors.
    """

    max_attempts: int


class Explain(Section):
    """Configure the explanation of the results.

    Attributes
    ----------
    listed_values:
        Nonzero values of each variable listed to the explainer.
    tolerance:
        Relative margin under which a constraint counts as binding.
    """

    listed_values: int
    tolerance: float


class DataSchema(Section):
    """Describe the input columns given to the agents.

    Attributes
    ----------
    meanings:
        Meaning of each known column name. Optional: when it is empty or
        every entry is commented out, each column is marked as to clarify.
    """

    meanings: dict[str, str] = Field(default_factory=dict)

    @field_validator("meanings", mode="before")
    @classmethod
    def empty_meanings(cls, value: object) -> object:
        """Read a key left without entries as no known meaning."""
        return {} if value is None else value


class Settings(Section):
    """Hold every global parameter of the agent.

    Attributes
    ----------
    models:
        Mistral model of each agent.
    llm:
        Settings of the structured requests.
    retry:
        Retries of transient API errors.
    clarification:
        Dialogue with the user.
    model_builder:
        Generation and execution of the optimization code.
    model_editor:
        Edition of the model spec.
    explain:
        Explanation of the results.
    data_schema:
        Meaning of the input columns.
    """

    models: Models
    llm: Llm
    retry: Retry
    clarification: Clarification
    model_builder: ModelBuilder
    model_editor: ModelEditor
    explain: Explain
    data_schema: DataSchema


def load_settings(path: Path) -> Settings:
    """
    Read and validate a parameters file.

    A relative data folder is resolved from the folder of the file, so the
    agent reads the same data whatever the working directory.

    Parameters
    ----------
    path:
        YAML file holding every section of the settings.

    Returns
    -------
    Settings
        Immutable validated parameters.
    """
    with path.open(encoding="utf-8") as source:
        parameters = yaml.safe_load(source)
    builder = parameters["model_builder"]
    builder["data_dir"] = path.resolve().parent / builder["data_dir"]
    return Settings.model_validate(parameters)
