import numpy as np
from PIL import Image

import config
from agents.review_agent import _frame_times
from services.media_probe import extract_frames, probe
from services.scene_renderer import LAYOUTS, _effective_layout, render_caption, render_scene
from services.video_generator import compose_video

from tests.conftest import make_scene


def test_every_layout_renders_full_size(storyboard, tmp_path):

    rendered = {scene.layout for scene in storyboard.scenes}
    assert rendered == set(LAYOUTS)

    for scene in storyboard.scenes:
        path = render_scene(scene, storyboard.color_theme, len(storyboard.scenes), tmp_path / f"{scene.index}.png")

        with Image.open(path) as image:
            assert image.size == (config.VIDEO_WIDTH, config.VIDEO_HEIGHT)


def test_layout_falls_back_when_data_is_missing():

    assert _effective_layout(make_scene(1, "stat")) == "title"
    assert _effective_layout(make_scene(1, "bar_chart", chart_labels=["A", "B"], chart_values=[1.0])) == "title"
    assert _effective_layout(make_scene(1, "bar_chart", bullets=["x"])) == "bullets"


def test_long_text_still_renders(tmp_path):

    scene = make_scene(1, "title", headline="word " * 80)
    render_scene(scene, "teal", 1, tmp_path / "long.png")

    caption = render_caption("a very long caption " * 10)
    assert caption.mode == "RGBA"
    assert caption.width == config.VIDEO_WIDTH


def _write_tone(path, seconds):

    from moviepy.audio.AudioClip import AudioArrayClip

    rate = 44100
    t = np.linspace(0, seconds, int(rate * seconds), endpoint=False)
    tone = 0.2 * np.sin(2 * np.pi * 440 * t)
    AudioArrayClip(np.column_stack([tone, tone]), fps=rate).write_audiofile(str(path), logger=None)


def test_compose_and_probe_video(storyboard, tmp_path):

    scenes = storyboard.scenes[:2]
    images, audio = [], []

    for scene in scenes:
        images.append(render_scene(scene, "navy", 2, tmp_path / f"s{scene.index}.png"))
        audio_path = tmp_path / f"s{scene.index}.wav"
        _write_tone(audio_path, 1.0)
        audio.append(str(audio_path))

    output = tmp_path / "video.mp4"
    durations = compose_video(images, audio, [s.narration for s in scenes], output)

    info = probe(str(output))

    assert info.has_video and info.has_audio
    assert (info.width, info.height) == (config.VIDEO_WIDTH, config.VIDEO_HEIGHT)
    assert abs(info.duration - sum(durations)) < 0.3

    frames = extract_frames(str(output), _frame_times(durations), tmp_path / "frames")
    assert len(frames) == 2


def test_frame_times_are_scene_midpoints():

    assert _frame_times([2.0, 4.0]) == [1.0, 4.0]
    assert len(_frame_times([1.0] * 20)) == 8


def test_caption_chunks_follow_phrases():

    from services.video_generator import MAX_WORDS_PER_CAPTION, caption_chunks

    narration = (
        "Unemployment was 3.1 percent in 2025, using usual status. "
        "That looks low. But the monthly survey, which looks at the last seven days, says 5.1 percent."
    )
    chunks = caption_chunks(narration)

    assert " ".join(chunks) == narration
    assert all(len(chunk.split()) <= MAX_WORDS_PER_CAPTION for chunk in chunks)
    assert "Unemployment was 3.1 percent in 2025," in chunks


def test_number_formatting():

    from services.scene_renderer import _format_number

    assert _format_number(43, 1, "%") == "43.0%"
    assert _format_number(47, 0, "crore") == "47 crore"
    assert _format_number(1500, 0, "") == "1,500"
