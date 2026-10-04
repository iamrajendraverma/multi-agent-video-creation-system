import logging

import config
from models.state import ResearchResult
from prompts import load_prompt
from services.llm import ask_claude, ask_claude_structured


logger = logging.getLogger(__name__)


def research_agent(state):

    tools = None
    search_instructions = (
        "Use your own knowledge. Mark any statistic you are not sure about "
        "as approximate in its source."
    )

    if config.RESEARCH_WEB_SEARCH:
        tools = ["WebSearch"]
        search_instructions = (
            "Search the web for current, authoritative data before answering. "
            f"Use at most {config.RESEARCH_MAX_SEARCHES} searches."
        )

    notes = ask_claude(
        load_prompt(
            "research",
            user_prompt=state.user_prompt,
            search_instructions=search_instructions,
        ),
        tools=tools,
        # One turn per search, plus the final answer
        max_turns=config.RESEARCH_MAX_SEARCHES + 2,
    )

    # Web-search answers come back as cited free text; convert to structure
    state.research = ask_claude_structured(
        load_prompt("research_extract", notes=notes),
        ResearchResult,
    )

    logger.info(
        "Research: %d facts, %d statistics, %d sources",
        len(state.research.facts),
        len(state.research.statistics),
        len(state.research.sources),
    )

    return state
