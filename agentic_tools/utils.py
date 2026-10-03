"""Define the shared retry policy and Mistral client of the agents."""

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

import httpx
from langchain_core.messages import BaseMessage
from mistralai.client import Mistral
from pydantic import BaseModel

from data_model.settings import Settings


def default_should_retry(error: Exception) -> bool:
    """Identify transient HTTP errors, timeouts, and connection failures.

    HTTP 400 and 404, validation errors, and other permanent failures are
    propagated immediately. Support SDK ``status_code`` and HTTPX responses.
    """
    response = getattr(error, "response", None)
    status = getattr(error, "status_code", None)
    if status is None:
        status = getattr(response, "status_code", None)
    if status is not None:
        return status in (429, 500, 502, 503, 504)
    return isinstance(
        error,
        (TimeoutError, ConnectionError,
         httpx.TimeoutException, httpx.NetworkError)
    )


def retry_policy(
    settings: Settings,
    understanding: bool,
) -> tuple[int, float, float]:
    """Return the retries and the backoff bounds of a call."""
    retry = settings.retry
    if understanding:
        policy = (retry.understanding_max_retries,
                  retry.understanding_base_delay,
                  retry.understanding_max_delay)
    else:
        policy = (retry.max_retries, retry.base_delay, retry.max_delay)

    if not 0 < policy[1] <= policy[2] < float("inf"):
        raise ValueError("delays must be finite "
                         "with 0 < base_delay <= max_delay")
    return policy


def llm_retry[**P, R](
    understanding: bool = False,
    should_retry: Callable[[Exception], bool] = default_should_retry,
    ) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Retry asynchronous calls with capped exponential backoff and jitter.

    The retries and delays are read from the ``settings`` attribute of the
    decorated method's object, when the call is made.

    Parameters
    ----------
    understanding:
        True to use the longer retry policy of the understanding requests.
    should_retry:
        Predicate selecting which exceptions can be retried.

    Returns
    -------
    Callable
        Decorator preserving the call signature and original exceptions.
    """

    def decorator(func: Callable[P, Awaitable[R]]
                  ) -> Callable[P, Awaitable[R]]:
        """Wrap an asynchronous LLM call with the retry policy."""

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """Run the call, retrying only transient failures."""

            agent: Any = args[0]
            retries, base_delay, _ = retry_policy(agent.settings,
                                                  understanding)
            logger = logging.getLogger(__name__)
            for attempt in range(retries + 1):
                try:
                    return await func(*args, **kwargs)
                # pylint: disable-next=broad-exception-caught
                except Exception as error:
                    if attempt == retries or not should_retry(error):
                        raise
                    delay = (2 ** attempt +
                             random.uniform(0, 1) + base_delay)
                    logger.warning(
                        "%s: %s, retry %d/%d in %.2fs",
                        func.__qualname__,
                        type(error).__name__,
                        attempt + 1,
                        retries,
                        delay,
                    )
                    await asyncio.sleep(delay)

            raise AssertionError("Unreachable: the final "
                                 "attempt returns or raises")

        return wrapper

    return decorator


class MistralAgent:
    """Request structured outputs from a Mistral model.

    Attributes
    ----------
    client:
        Asynchronous Mistral client.
    model:
        Name of the Mistral model.
    settings:
        Global parameters of the agent, read by llm_retry.
    temperature:
        Sampling temperature of the requests.
    max_tokens:
        Maximum length of an answer.
    """

    def __init__(self, api_key: str, model: str, settings: Settings) -> None:
        self.client = Mistral(api_key=api_key)
        self.model = model
        self.settings = settings
        self.temperature = settings.llm.temperature
        self.max_tokens = settings.llm.max_tokens

    async def parse[T: BaseModel](
        self,
        messages: list[Any],
        response_format: type[T],
    ) -> T:
        """
        Send the messages and validate the structured answer.

        Parameters
        ----------
        messages:
            Chat messages given to the model.
        response_format:
            Pydantic model the answer must follow.

        Returns
        -------
        T
            Parsed answer of the model.
        """
        response = await self.client.chat.parse_async(
            model=self.model,
            messages=messages,
            response_format=response_format,
            temperature=self.temperature,
            max_tokens=self.max_tokens)
        name = response_format.__name__
        if not response.choices or response.choices[0].message is None:
            raise ValueError(f"Mistral returned no {name} message")
        parsed = response.choices[0].message.parsed
        if not isinstance(parsed, response_format):
            raise TypeError(f"Mistral returned no structured {name}")
        return parsed

    @staticmethod
    def format_messages(messages: list[BaseMessage]) -> str:
        """Format the full conversation stored in the current agent state."""
        return "\n\n".join(
            f"{message.type.upper()}:\n{message.content}"
            for message in messages
        )
