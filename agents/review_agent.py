import logging
from itertools import accumulate
from pathlib import Path
from typing import List, Tuple

import config
from models.state import ReviewIssue, ReviewResult
from prompts import load_prompt
from services.scene_renderer import RENDERER_CAPABILITIES
from services.llm import ask_claude_structured
from services.media_probe import extract_frames, probe


logger = logging.getLogger(__name__)

# Allowed deviation from the target duration range, in seconds
DURATION_TOLERANCE = 2.0
MAX_REVIEW_FRAMES = 8


def technical_checks(state) -> Tuple[str, List[ReviewIssue]]:
    """
    Deterministic checks on the rendered file.
    """

    info = probe(state.video_path)
    issues = []

    if info.duration < config.VIDEO_MIN_SECONDS - DURATION_TOLERANCE:
        issues.append(ReviewIssue(
            severity="major",
            target_agent="script",
            description=(
                f"Video is {info.duration:.1f} s, shorter than the "
                f"{config.VIDEO_MIN_SECONDS} s minimum: lengthen the script."
            ),
        ))

    if info.duration > config.VIDEO_MAX_SECONDS + DURATION_TOLERANCE:
        issues.append(ReviewIssue(
            severity="major",
            target_agent="script",
            description=(
                f"Video is {info.duration:.1f} s, longer than the "
                f"{config.VIDEO_MAX_SECONDS} s maximum: shorten the script."
            ),
        ))

    if not info.has_video or not info.has_audio:
        issues.append(ReviewIssue(
            severity="critical",
            target_agent="video",
            description="Rendered file is missing its video or audio stream.",
        ))

    if (info.width, info.height) != (config.VIDEO_WIDTH, config.VIDEO_HEIGHT):
        issues.append(ReviewIssue(
            severity="critical",
            target_agent="video",
            description=f"Resolution is {info.width}x{info.height}, expected 1080x1920.",
        ))

    report = (
        f"Duration: {info.duration:.1f} s "
        f"(target {config.VIDEO_MIN_SECONDS}-{config.VIDEO_MAX_SECONDS} s)\n"
        f"Resolution: {info.width}x{info.height}\n"
        f"Video stream: {info.has_video}, audio stream: {info.has_audio}\n"
        f"Scenes: {len(state.scene_durations)}"
    )

    return report, issues


def _frame_times(scene_durations: List[float]) -> List[float]:
    """
    The middle of each scene (when its caption and content are visible).
    """

    starts = [0.0, *accumulate(scene_durations)][:-1]
    times = [start + duration / 2 for start, duration in zip(starts, scene_durations)]

    if len(times) > MAX_REVIEW_FRAMES:
        step = len(times) / MAX_REVIEW_FRAMES
        times = [times[int(i * step)] for i in range(MAX_REVIEW_FRAMES)]

    return times


def review_agent(state):

    attempt = state.iteration + 1

    report, technical_issues = technical_checks(state)

    frames = extract_frames(
        state.video_path,
        _frame_times(state.scene_durations),
        Path(state.run_dir) / f"review_frames_v{attempt}",
    )

    prompt = load_prompt(
        "review",
        user_prompt=state.user_prompt,
        research=state.research.model_dump_json(indent=2),
        renderer_capabilities=RENDERER_CAPABILITIES,
        script=state.script.full_text,
        storyboard=state.storyboard.model_dump_json(indent=2),
        technical_report=report,
    )

    content_review = ask_claude_structured(prompt, ReviewResult, images=frames)

    issues = technical_issues + content_review.issues
    blocking = [issue for issue in issues if issue.severity in ("major", "critical")]

    review = ReviewResult(
        approved=content_review.approved and not blocking,
        score=content_review.score,
        issues=issues,
        feedback=content_review.feedback,
    )

    state.review = review
    state.review_history.append(review)
    state.review_feedback = review.feedback
    state.approved = review.approved
    state.iteration = attempt
    state.needs_human_review = (
        not review.approved and attempt >= config.VIDEO_MAX_ITERATIONS
    )

    logger.info(
        "Review v%d: %s (score %d/10, %d issues, %d blocking)",
        attempt,
        "APPROVED" if review.approved else "REJECTED",
        review.score,
        len(issues),
        len(blocking),
    )
    for issue in issues:
        logger.info("  [%s -> %s] %s", issue.severity, issue.target_agent, issue.description)

    return state
