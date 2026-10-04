from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Agent outputs. These are also used as Claude structured-output
# schemas, so fields have no defaults: the model must fill every one.
# ------------------------------------------------------------------


class Statistic(BaseModel):
    label: str
    value: str
    source: str


class ResearchResult(BaseModel):
    summary: str
    facts: List[str]
    statistics: List[Statistic]
    caveats: List[str]
    sources: List[str]


class Script(BaseModel):
    title: str
    hook: str
    body: List[str]
    ending: str

    @property
    def full_text(self) -> str:
        return " ".join([self.hook, *self.body, self.ending])

    @property
    def word_count(self) -> int:
        return len(self.full_text.split())


Layout = Literal["title", "stat", "bullets", "bar_chart", "quote", "outro"]

ColorTheme = Literal["navy", "teal", "purple", "sunset", "forest"]


class Scene(BaseModel):
    index: int
    layout: Layout
    narration: str
    headline: str
    # Layout-specific content; empty when the layout doesn't use it
    stat_value: str
    bullets: List[str]
    chart_labels: List[str]
    chart_values: List[float]
    chart_unit: str
    # Short source credit shown on screen, e.g. "PLFS 2025"
    source: str


class Storyboard(BaseModel):
    color_theme: ColorTheme
    scenes: List[Scene]


ReviewTarget = Literal["script", "visual", "video"]


class ReviewIssue(BaseModel):
    severity: Literal["minor", "major", "critical"]
    target_agent: ReviewTarget
    description: str


class ReviewResult(BaseModel):
    approved: bool
    score: int
    issues: List[ReviewIssue]
    feedback: str


class YouTubeMetadata(BaseModel):
    title: str
    description: str
    tags: List[str]


# ------------------------------------------------------------------
# Pipeline state shared by all agents
# ------------------------------------------------------------------


class VideoState(BaseModel):
    user_prompt: str

    run_dir: Optional[str] = None

    # Run options (from the CLI)
    publish: bool = True
    auto_confirm: bool = False
    privacy: str = "private"

    research: Optional[ResearchResult] = None
    script: Optional[Script] = None
    storyboard: Optional[Storyboard] = None

    scene_images: List[str] = Field(default_factory=list)
    audio_paths: List[str] = Field(default_factory=list)
    scene_durations: List[float] = Field(default_factory=list)
    video_path: Optional[str] = None
    thumbnail_path: Optional[str] = None

    review: Optional[ReviewResult] = None
    review_history: List[ReviewResult] = Field(default_factory=list)
    review_feedback: Optional[str] = None
    approved: bool = False
    needs_human_review: bool = False
    iteration: int = 0

    youtube_metadata: Optional[YouTubeMetadata] = None
    youtube_url: Optional[str] = None

    errors: List[str] = Field(default_factory=list)
