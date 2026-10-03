"""Provide the functions shared by every agentic tool."""

import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps

import httpx2
from langchain_core.messages import AnyMessage
from mistralai.client import Mistral
from mistralai.client.errors import MistralError
from pydantic import BaseModel, ValidationError

from parameters import RetryPolicy, Settings, load_settings

RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}

ROLES = {"human": "User", "ai": "Agent"}


def is_retryable(error: Exception) -> bool:
    """
    Tell whether a failed LLM call is worth retrying.

    Parameters
    ----------
    error:
        Exception raised by the call.

    Returns
    -------
    bool
        True for rate limits, server errors, network errors and
        malformed structured outputs.
    """
    if isinstance(error, MistralError):
        return error.status_code in RETRYABLE_STATUS
    return isinstance(error, (httpx2.TransportError, ValidationError))


def retry_policy(understanding: bool) -> RetryPolicy:
    """Return the retry policy read from the parameters."""
    policies = load_settings().retry
    return policies.understanding if understanding else policies.default


def llm_retry[**P, T](
    understanding: bool = False,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Retry an async LLM call with exponential backoff.

    Parameters
    ----------
    understanding:
        Use the longer policy of the understanding calls.

    Returns
    -------
    Callable
        Decorator applying the policy.
    """

    def decorator(
        call: Callable[P, Awaitable[T]],
    ) -> Callable[P, Awaitable[T]]:
        @wraps(call)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            policy = retry_policy(understanding)
            for attempt in range(policy.attempts - 1):
                try:
                    return await call(*args, **kwargs)
                except Exception as error:  # pylint: disable=broad-except
                    if not is_retryable(error):
                        raise
                    await asyncio.sleep(policy.base_delay * 2**attempt)
            return await call(*args, **kwargs)

        return wrapper

    return decorator


class MistralAgent:
    """Call a Mistral model returning a structured output.

    Attributes
    ----------
    client:
        Mistral API client.
    settings:
        Global parameters of the calls.
    model:
        Name of the Mistral model called.
    """

    def __init__(self, client: Mistral, settings: Settings,
                 model: str) -> None:
        """
        Keep the client and the parameters of the calls.

        Parameters
        ----------
        client:
            Mistral API client.
        settings:
            Global parameters of the calls.
        model:
            Name of the Mistral model called.
        """
        self.client = client
        self.settings = settings
        self.model = model

    @staticmethod
    def format_messages(messages: list[AnyMessage]) -> str:
        """Render the conversation as plain text for the prompt."""
        return "\n\n".join(f"{ROLES.get(message.type, message.type)}: "
                           f"{message.text}" for message in messages)

    async def parse[T: BaseModel](self, messages: list[dict[str, str]],
                                  output: type[T]) -> T:
        """
        Call the model and parse its answer into the output model.

        Parameters
        ----------
        messages:
            System and user messages sent to the model.
        output:
            Pydantic model of the expected answer.

        Returns
        -------
        T
            Parsed answer of the model.
        """
        response = await self.client.chat.parse_async(
            output, model=self.model, messages=messages,
            temperature=self.settings.temperature)
        message = response.choices[0].message if response.choices else None
        parsed = message.parsed if message is not None else None
        if parsed is None:
            raise ValueError(f"{self.model} returned no structured output.")
        return parsed
