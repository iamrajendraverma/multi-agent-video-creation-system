"""
Coordinator: runs the agents as a LangGraph state machine.

    START ─► research ─► script ─► visual ─► video ─► review ─┬─► publish ─► END
                           ▲          ▲         ▲             │
                           └──────────┴─────────┴── rejected ─┘ (up to VIDEO_MAX_ITERATIONS)

Any agent error ends the run. After every step the full state is
saved to <run_dir>/state.json, so a run can be resumed with --resume.
"""

import logging
import time
from pathlib import Path
from typing import Optional

from langgraph.graph import END, START, StateGraph
from rich.logging import RichHandler

import config
from agents.publisher_agent import publisher_agent
from agents.research_agent import research_agent
from agents.review_agent import review_agent
from agents.script_agent import script_agent
from agents.video_agent import video_agent
from agents.visual_agent import visual_agent
from models.state import VideoState


logger = logging.getLogger("coordinator")

AGENTS = {
    "research": research_agent,
    "script": script_agent,
    "visual": visual_agent,
    "video": video_agent,
    "review": review_agent,
    "publish": publisher_agent,
}

NEXT_STAGE = {
    "research": "script",
    "script": "visual",
    "visual": "video",
    "video": "review",
}

# Earliest stage first: a script fix also re-runs visual and video
FIX_ORDER = ["script", "visual", "video"]

STATE_FILE = "state.json"


# ------------------------------------------------------------------
# Nodes
# ------------------------------------------------------------------


def _node(name: str):

    def run(state: VideoState) -> dict:

        logger.info("[bold cyan]▶ %s agent[/]", name, extra={"markup": True})
        started = time.monotonic()

        working = state.model_copy(deep=True)

        try:
            working = AGENTS[name](working)
        except Exception as error:
            logger.exception("%s agent failed", name)
            working.errors.append(f"{name}: {type(error).__name__}: {error}")

        logger.info("  %s agent finished in %.1f s", name, time.monotonic() - started)

        save_state(working)
        _save_artifact(name, working)

        return {field: getattr(working, field) for field in VideoState.model_fields}

    return run


def _save_artifact(name: str, state: VideoState) -> None:

    run_dir = Path(state.run_dir)

    artifacts = {
        "research": ("research.json", state.research),
        "script": ("script.json", state.script),
        "visual": ("storyboard.json", state.storyboard),
        "review": (f"review_v{state.iteration}.json", state.review),
        "publish": ("youtube.json", state.youtube_metadata),
    }

    if name in artifacts:
        filename, value = artifacts[name]
        if value is not None:
            (run_dir / filename).write_text(value.model_dump_json(indent=2), encoding="utf-8")


def save_state(state: VideoState) -> None:
    (Path(state.run_dir) / STATE_FILE).write_text(
        state.model_dump_json(indent=2), encoding="utf-8"
    )


def load_state(run_dir: Path) -> VideoState:
    return VideoState.model_validate_json((run_dir / STATE_FILE).read_text(encoding="utf-8"))


# ------------------------------------------------------------------
# Routing
# ------------------------------------------------------------------


def route_start(state: VideoState) -> str:
    """
    First stage whose output is missing (lets --resume skip finished work).
    """

    if state.research is None:
        return "research"
    if state.script is None:
        return "script"
    if state.storyboard is None:
        return "visual"
    if state.video_path is None or not Path(state.video_path).exists():
        return "video"
    if state.review is None:
        return "review"
    if state.approved:
        return END if state.youtube_url else "publish"

    return route_after_review(state)


def route_next(name: str):

    def route(state: VideoState) -> str:
        return END if state.errors else NEXT_STAGE[name]

    return route


def route_after_review(state: VideoState) -> str:

    if state.errors:
        return END
    if state.approved:
        return "publish"
    if state.iteration >= config.VIDEO_MAX_ITERATIONS:
        return END

    issues = state.review.issues if state.review else []
    blocking = [issue for issue in issues if issue.severity != "minor"]
    targets = {issue.target_agent for issue in blocking or issues}

    for stage in FIX_ORDER:
        if stage in targets:
            return stage

    return "script"


def create_video_graph():

    graph = StateGraph(VideoState)

    for name in AGENTS:
        graph.add_node(name, _node(name))

    stages = ["research", "script", "visual", "video", "review", "publish", END]

    graph.add_conditional_edges(START, route_start, stages)

    for name, next_stage in NEXT_STAGE.items():
        graph.add_conditional_edges(name, route_next(name), [next_stage, END])

    graph.add_conditional_edges(
        "review", route_after_review, ["script", "visual", "video", "publish", END]
    )
    graph.add_edge("publish", END)

    return graph.compile()


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------


def setup_logging(run_dir: Path) -> None:

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    root.addHandler(RichHandler(show_path=False, markup=False))

    file_handler = logging.FileHandler(run_dir / "run.log", encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root.addHandler(file_handler)

    # Keep third-party HTTP chatter out of the console
    for noisy in ("httpx", "httpx2", "anthropic", "googleapiclient", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def run_pipeline(
    user_prompt: Optional[str] = None,
    publish: bool = True,
    auto_confirm: bool = False,
    privacy: str = config.YOUTUBE_PRIVACY,
    resume_dir: Optional[str] = None,
) -> VideoState:

    if resume_dir:
        state = load_state(Path(resume_dir))
        # Retry whatever failed last time
        state.errors = []
        state.publish = publish
        state.auto_confirm = auto_confirm
        state.privacy = privacy
    else:
        run_dir = config.create_run_dir(user_prompt)
        state = VideoState(
            user_prompt=user_prompt,
            run_dir=str(run_dir),
            publish=publish,
            auto_confirm=auto_confirm,
            privacy=privacy,
        )

    setup_logging(Path(state.run_dir))
    logger.info("Run folder: %s", state.run_dir)
    logger.info("Request: %s", state.user_prompt)

    app = create_video_graph()

    result = app.invoke(state, config={"recursion_limit": 50})

    return VideoState.model_validate(result)
