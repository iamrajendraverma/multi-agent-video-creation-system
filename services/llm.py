import asyncio
import base64
import logging
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Type, TypeVar

from pydantic import BaseModel

import config


logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Server-tool turns (e.g. web search) may pause; resume at most this often
MAX_PAUSE_CONTINUATIONS = 3

# Agent turns allowed for a request (each tool call uses one turn)
DEFAULT_MAX_TURNS = 3

DEFAULT_SYSTEM = "You are a helpful assistant inside a video production pipeline."

LOGIN_HINT = (
    "Claude login not found. Run 'claude login' once "
    "(or set CLAUDE_CODE_OAUTH_TOKEN from 'claude setup-token')."
)


class ClaudeRefusalError(RuntimeError):
    pass


class ClaudeAuthError(RuntimeError):
    pass


def _image_block(image_path: str) -> dict:

    data = base64.standard_b64encode(Path(image_path).read_bytes())

    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": data.decode("utf-8"),
        },
    }


def _user_content(prompt: str, images: Optional[List[str]]) -> list:

    content = [_image_block(path) for path in images or []]
    content.append({"type": "text", "text": prompt})

    return content


# ---------------------------------------------------------------------------
# Claude login (Claude Agent SDK) - default
# ---------------------------------------------------------------------------

def _agent_options(system, tools, output_format, max_turns):

    from claude_agent_sdk import ClaudeAgentOptions

    return ClaudeAgentOptions(
        model=config.CLAUDE_MODEL,
        system_prompt=system or DEFAULT_SYSTEM,
        # Only the tools this request asks for; no Bash / file editing
        tools=list(tools or []),
        allowed_tools=list(tools or []),
        permission_mode="dontAsk",
        # Don't pick up CLAUDE.md or settings from this repo or ~/.claude
        setting_sources=[],
        max_turns=max_turns,
        output_format=output_format,
        cwd=tempfile.gettempdir(),
    )


async def _agent_query(prompt, images, options):

    from claude_agent_sdk import (
        AssistantMessage,
        ResultMessage,
        TextBlock,
        query,
    )

    if images:
        # Read the images here so a bad path raises instead of ending the stream
        content = _user_content(prompt, images)

        async def stream():
            yield {
                "type": "user",
                "message": {"role": "user", "content": content},
                "parent_tool_use_id": None,
            }
        prompt_input = stream()
    else:
        prompt_input = prompt

    texts = []
    result = None
    auth_failed = False

    async for message in query(prompt=prompt_input, options=options):

        if isinstance(message, AssistantMessage):
            # Let the stream finish; raising mid-iteration leaves the CLI running
            auth_failed = auth_failed or message.error == "authentication_failed"
            texts.extend(
                block.text for block in message.content
                if isinstance(block, TextBlock)
            )

        elif isinstance(message, ResultMessage):
            result = message

    if auth_failed:
        raise ClaudeAuthError(LOGIN_HINT)

    return texts, result


def _run_agent(prompt, system, tools, images, output_format=None,
               max_turns=DEFAULT_MAX_TURNS):

    from claude_agent_sdk import ClaudeSDKError, CLINotFoundError

    options = _agent_options(system, tools, output_format, max_turns)

    try:
        texts, result = asyncio.run(_agent_query(prompt, images, options))
    except CLINotFoundError as error:
        raise ClaudeAuthError(
            "Claude Code CLI not found; install it, then run 'claude login'."
        ) from error
    except ClaudeSDKError as error:
        if "auth" in str(error).lower() or "login" in str(error).lower():
            raise ClaudeAuthError(LOGIN_HINT) from error
        raise

    if result is None:
        raise RuntimeError("Claude returned no result")

    if result.stop_reason == "refusal":
        raise ClaudeRefusalError(f"Claude declined the request: {result.result}")

    if result.is_error and result.subtype == "success":
        raise RuntimeError(
            f"Claude request failed (HTTP {result.api_error_status}): {result.result}"
        )

    return texts, result


# ---------------------------------------------------------------------------
# API key (Anthropic SDK) - CLAUDE_AUTH=api_key
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_client():

    from anthropic import Anthropic

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


def _check_refusal(response) -> None:

    if response.stop_reason == "refusal":
        details = getattr(response, "stop_details", None)
        raise ClaudeRefusalError(
            f"Claude declined the request: {details}"
        )

    if response.stop_reason == "max_tokens":
        logger.warning("Claude response was cut off at max_tokens")


# Agent SDK tool name -> Claude API server tool
def _api_tools(tools: Optional[list]) -> Optional[list]:

    if not tools:
        return None

    api_tools = []
    for name in tools:
        if name == "WebSearch":
            api_tools.append({
                "type": "web_search_20260209",
                "name": "web_search",
                "max_uses": config.RESEARCH_MAX_SEARCHES,
            })
        else:
            raise ValueError(f"Tool {name!r} is not supported with CLAUDE_AUTH=api_key")

    return api_tools


def _api_ask(prompt, system, tools, images) -> str:

    messages = [{"role": "user", "content": _user_content(prompt, images)}]

    kwargs = _request_options()
    if system:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = _api_tools(tools)

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


def _api_ask_structured(prompt, schema, system, images):

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


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def ask_claude(
    prompt: str,
    system: Optional[str] = None,
    tools: Optional[List[str]] = None,
    images: Optional[List[str]] = None,
    max_turns: int = DEFAULT_MAX_TURNS,
) -> str:
    """
    Send a prompt and return the text of Claude's answer.
    `tools` are Claude Code tool names, e.g. ["WebSearch"].
    """

    if config.CLAUDE_AUTH == "api_key":
        return _api_ask(prompt, system, tools, images)

    texts, result = _run_agent(prompt, system, tools, images, max_turns=max_turns)

    if result.subtype != "success":
        logger.warning("Claude stopped early (%s)", result.subtype)

    return result.result or "\n\n".join(texts)


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

    if config.CLAUDE_AUTH == "api_key":
        return _api_ask_structured(prompt, schema, system, images)

    _, result = _run_agent(
        prompt,
        system,
        tools=None,
        images=images,
        output_format={
            "type": "json_schema",
            "schema": schema.model_json_schema(),
        },
    )

    if result.subtype != "success" or result.structured_output is None:
        raise ValueError(
            f"Claude returned no valid {schema.__name__} ({result.subtype})"
        )

    return schema.model_validate(result.structured_output)


def check_auth() -> None:
    """
    Make one tiny request so a missing login fails fast, before the pipeline.
    """

    ask_claude("Reply with the single word: ok", max_turns=1)
