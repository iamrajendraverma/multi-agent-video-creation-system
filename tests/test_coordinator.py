from langgraph.graph import END

import config
from coordinator import coordinator
from models.state import ReviewIssue, ReviewResult, VideoState


def _review(approved, *targets, severity="major"):

    return ReviewResult(
        approved=approved,
        score=8 if approved else 4,
        feedback="",
        issues=[
            ReviewIssue(severity=severity, target_agent=target, description=target)
            for target in targets
        ],
    )


def test_route_after_review():

    state = VideoState(user_prompt="x", iteration=1)

    state.approved = True
    assert coordinator.route_after_review(state) == "publish"

    state.approved = False
    state.review = _review(False, "video", "visual")
    assert coordinator.route_after_review(state) == "visual"

    state.review = _review(False, "script", severity="minor")
    assert coordinator.route_after_review(state) == "script"

    state.iteration = config.VIDEO_MAX_ITERATIONS
    assert coordinator.route_after_review(state) == END

    state.iteration = 1
    state.errors = ["boom"]
    assert coordinator.route_after_review(state) == END


def test_route_start_skips_finished_stages(research, script, storyboard, tmp_path):

    state = VideoState(user_prompt="x")
    assert coordinator.route_start(state) == "research"

    state.research, state.script = research, script
    assert coordinator.route_start(state) == "visual"

    state.storyboard = storyboard
    video = tmp_path / "v.mp4"
    video.write_bytes(b"")
    state.video_path = str(video)
    assert coordinator.route_start(state) == "review"


def _fake_agents(monkeypatch, research, script, storyboard, reviews, calls):

    def research_agent(state):
        calls.append("research")
        state.research = research
        return state

    def script_agent(state):
        calls.append("script")
        state.script = script
        return state

    def visual_agent(state):
        calls.append("visual")
        state.storyboard = storyboard
        return state

    def video_agent(state):
        calls.append("video")
        state.video_path = "video.mp4"
        return state

    def review_agent(state):
        calls.append("review")
        review = reviews.pop(0)
        state.review = review
        state.approved = review.approved
        state.iteration += 1
        return state

    def publish_agent(state):
        calls.append("publish")
        state.youtube_url = "https://youtube.com/shorts/test"
        return state

    monkeypatch.setattr(coordinator, "AGENTS", {
        "research": research_agent,
        "script": script_agent,
        "visual": visual_agent,
        "video": video_agent,
        "review": review_agent,
        "publish": publish_agent,
    })


def test_graph_fix_loop_then_publish(monkeypatch, tmp_path, research, script, storyboard):

    calls = []
    reviews = [_review(False, "visual"), _review(True)]
    _fake_agents(monkeypatch, research, script, storyboard, reviews, calls)

    state = VideoState(user_prompt="x", run_dir=str(tmp_path))
    result = VideoState.model_validate(coordinator.create_video_graph().invoke(state))

    assert calls == [
        "research", "script", "visual", "video", "review",
        "visual", "video", "review", "publish",
    ]
    assert result.youtube_url
    assert (tmp_path / "state.json").exists()
    assert (tmp_path / "review_v2.json").exists()


def test_graph_stops_on_agent_error(monkeypatch, tmp_path, research, script, storyboard):

    calls = []
    _fake_agents(monkeypatch, research, script, storyboard, [], calls)

    def broken_visual(state):
        raise RuntimeError("no storyboard")

    monkeypatch.setitem(coordinator.AGENTS, "visual", broken_visual)

    state = VideoState(user_prompt="x", run_dir=str(tmp_path))
    result = VideoState.model_validate(coordinator.create_video_graph().invoke(state))

    assert calls == ["research", "script"]
    assert result.errors and "no storyboard" in result.errors[0]
