import base64
import logging
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Type, TypeVar

from anthropic import Anthropic
from pydantic import BaseModel

import config


logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Server-tool turns (e.g. web search) may pause; resume at most this often
MAX_PAUSE_CONTINUATIONS = 3


class ClaudeRefusalError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_client() -> Anthropic:
    # The SDK retries 408/409/429/5xx and connection errors with backoff
    return Anthropic(max_retries=4)


def _request_options() -> dict:

    options = {
        "model": config.CLAUDE_MODEL,
        "max_tokens": config.CLAUDE_MAX_TOKENS,
    }

    if config.CLAUDE_FALLBACKS:
        # On a safety decline the API re-runs the request on a fallback model
        options["betas"] = ["server-side-fallback-2026-07-01"]
        options["fallbacks"] = "default"

    return options


def _user_content(prompt: str, images: Optional[List[str]]) -> list:

    content = []

    for image_path in images or []:
        data = base64.standard_b64encode(Path(image_path).read_bytes())
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": data.decode("utf-8"),
            },
        })

    content.append({"type": "text", "text": prompt})

    return content


def _check_refusal(response) -> None:

    if response.stop_reason == "refusal":
        details = getattr(response, "stop_details", None)
        raise ClaudeRefusalError(
            f"Claude declined the request: {details}"
        )

    if response.stop_reason == "max_tokens":
        logger.warning("Claude response was cut off at max_tokens")


def ask_claude(
    prompt: str,
    system: Optional[str] = None,
    tools: Optional[list] = None,
    images: Optional[List[str]] = None,
) -> str:
    """
    Send a prompt and return the text of Claude's answer.
    Supports server-side tools such as web search.
    """

    messages = [{"role": "user", "content": _user_content(prompt, images)}]

    kwargs = _request_options()
    if system:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = tools

    for _ in range(MAX_PAUSE_CONTINUATIONS + 1):

        response = get_client().beta.messages.create(
            messages=messages, **kwargs
        )

        _check_refusal(response)

        if response.stop_reason != "pause_turn":
            break

        # A long server-tool turn paused; send it back to let Claude continue
        messages.append({"role": "assistant", "content": response.content})

    # The response may contain non-text blocks (thinking, tool use, ...),
    # so keep only the text parts.
    return "".join(
        block.text
        for block in response.content
        if block.type == "text"
    )


def ask_claude_structured(
    prompt: str,
    schema: Type[T],
    system: Optional[str] = None,
    images: Optional[List[str]] = None,
) -> T:
    """
    Send a prompt and return Claude's answer validated as `schema`
    (a Pydantic model), using structured outputs.
    """

    kwargs = _request_options()
    if system:
        kwargs["system"] = system

    response = get_client().beta.messages.parse(
        messages=[{"role": "user", "content": _user_content(prompt, images)}],
        output_format=schema,
        **kwargs,
    )

    _check_refusal(response)

    if response.parsed_output is None:
        raise ValueError(f"Claude returned no valid {schema.__name__}")

    return response.parsed_output
