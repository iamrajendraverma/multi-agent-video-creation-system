import logging

from agents.feedback import feedback_section
from models.state import Storyboard
from prompts import load_prompt
from services.scene_renderer import RENDERER_CAPABILITIES
from services.llm import ask_claude_structured


logger = logging.getLogger(__name__)


def visual_agent(state):

    prompt = load_prompt(
        "visual",
        script=state.script.full_text,
        research=state.research.model_dump_json(indent=2),
        renderer_capabilities=RENDERER_CAPABILITIES,
        feedback=feedback_section(state, "visual"),
    )

    storyboard = ask_claude_structured(prompt, Storyboard)

    if not storyboard.scenes:
        raise ValueError("Storyboard has no scenes")

    # Renumber in case the model skipped or repeated an index
    for number, scene in enumerate(storyboard.scenes, start=1):
        scene.index = number

    state.storyboard = storyboard

    logger.info(
        "Storyboard: %d scenes, theme %s, layouts %s",
        len(storyboard.scenes),
        storyboard.color_theme,
        [scene.layout for scene in storyboard.scenes],
    )

    return state
