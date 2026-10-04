import logging

import config
from agents.feedback import feedback_section
from models.state import Script
from prompts import load_prompt
from services.llm import ask_claude_structured


logger = logging.getLogger(__name__)

# Typical voice-over pace
WORDS_PER_SECOND = 2.5


def script_agent(state):

    prompt = load_prompt(
        "script",
        user_prompt=state.user_prompt,
        research=state.research.model_dump_json(indent=2),
        min_words=int(config.VIDEO_MIN_SECONDS * WORDS_PER_SECOND),
        max_words=int(config.VIDEO_MAX_SECONDS * WORDS_PER_SECOND * 0.9),
        min_seconds=config.VIDEO_MIN_SECONDS,
        max_seconds=config.VIDEO_MAX_SECONDS,
        feedback=feedback_section(state, "script"),
    )

    state.script = ask_claude_structured(prompt, Script)

    logger.info(
        "Script '%s': %d words (~%.0f s)",
        state.script.title,
        state.script.word_count,
        state.script.word_count / WORDS_PER_SECOND,
    )

    return state
