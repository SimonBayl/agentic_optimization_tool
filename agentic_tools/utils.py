"""Provide the functions shared by every agentic tool."""

import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps

import httpx2
from mistralai.client.errors import MistralError
from pydantic import ValidationError

from parameters import RetryPolicy, load_settings

RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


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
