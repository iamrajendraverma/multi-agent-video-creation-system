import pytest

from agents.feedback import feedback_section
from models.state import ReviewIssue, ReviewResult, VideoState
from prompts import load_prompt


def test_state_round_trips_through_json(storyboard, research, script):

    state = VideoState(
        user_prompt="test",
        research=research,
        script=script,
        storyboard=storyboard,
    )

    restored = VideoState.model_validate_json(state.model_dump_json())

    assert restored == state
    assert restored.storyboard.scenes[3].chart_values == [46.1, 29.7, 24.2]


def test_script_full_text_and_word_count(script):

    assert script.full_text.startswith("India's unemployment")
    assert script.word_count == len(script.full_text.split())


def test_load_prompt_fills_placeholders():

    text = load_prompt("metadata", user_prompt="AI jobs", script="Script text", sources="PLFS")

    assert "AI jobs" in text
    assert "$" not in text


def test_load_prompt_requires_all_placeholders():

    with pytest.raises(KeyError):
        load_prompt("metadata", user_prompt="AI jobs")


def test_feedback_section_only_lists_issues_for_target():

    state = VideoState(user_prompt="x")
    assert feedback_section(state, "script") == ""

    state.review = ReviewResult(
        approved=False,
        score=5,
        feedback="Too long",
        issues=[
            ReviewIssue(severity="major", target_agent="script", description="Shorten the script"),
            ReviewIssue(severity="minor", target_agent="visual", description="Bigger chart"),
        ],
    )

    section = feedback_section(state, "script")

    assert "Shorten the script" in section
    assert "Bigger chart" not in section
