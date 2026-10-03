"""Load the global parameters of the agent from parameters.yaml."""

from functools import cache
from pathlib import Path

import yaml
from pydantic import BaseModel

PARAMETERS_FILE = Path(__file__).parent / "parameters.yaml"


class Models(BaseModel):
    """Mistral model names used by each agentic tool."""

    understanding: str


class RetryPolicy(BaseModel):
    """Exponential backoff policy of an LLM call."""

    attempts: int
    base_delay: float


class RetryPolicies(BaseModel):
    """Retry policies, the understanding one being longer."""

    default: RetryPolicy
    understanding: RetryPolicy


class ClarificationBudget(BaseModel):
    """Limits on the questions asked to the user."""

    max_question_asks: int
    max_turns: int


class Settings(BaseModel):
    """Global parameters read by the nodes and the routes."""

    models: Models
    temperature: float
    clarification: ClarificationBudget
    retry: RetryPolicies


@cache
def load_settings(path: Path = PARAMETERS_FILE) -> Settings:
    """
    Read and validate the parameters file once.

    Parameters
    ----------
    path:
        YAML file holding the parameters.

    Returns
    -------
    Settings
        Validated global parameters.
    """
    with path.open(encoding="utf-8") as file:
        return Settings.model_validate(yaml.safe_load(file))
