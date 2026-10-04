import logging
import re
from pathlib import Path
from typing import List, Optional

import numpy as np
from PIL import Image

import config
from services.scene_renderer import render_caption


logger = logging.getLogger(__name__)

# Silence added after each scene's narration
SCENE_PADDING = 0.5
FADE_SECONDS = 0.25
# How far the background pans during a scene (Ken Burns effect)
PAN_SCALE = 1.06
CAPTION_TOP = 1320
MAX_WORDS_PER_CAPTION = 7
MIN_WORDS_PER_CAPTION = 3
MUSIC_VOLUME = 0.12


def _panning_clip(image_path: str, duration: float, direction: int):
    """
    A clip that slowly pans across a slightly enlarged scene image.
    Cropping a moving window is much faster than per-frame resizing.
    """

    from moviepy import VideoClip

    width, height = config.VIDEO_WIDTH, config.VIDEO_HEIGHT

    image = Image.open(image_path).convert("RGB")
    big = np.array(image.resize((int(width * PAN_SCALE), int(height * PAN_SCALE))))

    max_x = big.shape[1] - width
    max_y = big.shape[0] - height

    def frame(t):
        progress = t / duration if duration else 0
        if direction < 0:
            progress = 1 - progress
        x = int(max_x * progress)
        y = int(max_y * 0.5)
        return big[y:y + height, x:x + width]

    return VideoClip(frame_function=frame, duration=duration)


def _caption_clips(narration: str, start: float, speech_duration: float):
    """
    Captions of a few words each, timed by word count across the narration.
    """

    from moviepy import ImageClip

    words = narration.split()
    if not words:
        return []

    chunks = caption_chunks(narration)

    clips = []
    time = start

    for chunk in chunks:
        duration = speech_duration * len(chunk.split()) / len(words)
        caption = ImageClip(np.array(render_caption(chunk)))
        clips.append(
            caption
            .with_start(time)
            .with_duration(duration)
            .with_position(("center", CAPTION_TOP))
        )
        time += duration

    return clips


def caption_chunks(narration: str) -> List[str]:
    """
    Split narration into short captions, breaking at punctuation where
    possible so captions follow natural phrases.
    """

    phrases = [p for p in re.split(r"(?<=[,.;:!?])\s+", narration.strip()) if p]
    chunks: List[str] = []

    for phrase in phrases:
        words = phrase.split()
        # Split long phrases into near-equal parts
        parts = -(-len(words) // MAX_WORDS_PER_CAPTION)
        size = -(-len(words) // parts)
        pieces = [" ".join(words[i:i + size]) for i in range(0, len(words), size)]

        for piece in pieces:
            if chunks and len(piece.split()) < MIN_WORDS_PER_CAPTION and \
                    len(chunks[-1].split()) + len(piece.split()) <= MAX_WORDS_PER_CAPTION:
                chunks[-1] = f"{chunks[-1]} {piece}"
            else:
                chunks.append(piece)

    return chunks


def compose_video(
    scene_images: List[str],
    audio_paths: List[str],
    narrations: List[str],
    output_path: Path,
    music_path: Optional[Path] = None,
) -> List[float]:
    """
    Build the final video: one panning scene per image with its
    voice-over and burned-in captions, faded together, plus optional
    background music.

    Returns:
        The duration of each scene in seconds.
    """

    from moviepy import (
        AudioFileClip,
        CompositeAudioClip,
        CompositeVideoClip,
        afx,
        concatenate_videoclips,
        vfx,
    )

    size = (config.VIDEO_WIDTH, config.VIDEO_HEIGHT)
    scene_clips = []
    durations = []
    opened = []

    for number, (image_path, audio_path, narration) in enumerate(
        zip(scene_images, audio_paths, narrations)
    ):
        audio = AudioFileClip(audio_path)
        opened.append(audio)

        duration = audio.duration + SCENE_PADDING
        durations.append(duration)

        background = _panning_clip(image_path, duration, 1 if number % 2 == 0 else -1)
        captions = _caption_clips(narration, 0, audio.duration)

        scene = (
            CompositeVideoClip([background, *captions], size=size)
            .with_duration(duration)
            .with_audio(audio)
            .with_effects([vfx.FadeIn(FADE_SECONDS), vfx.FadeOut(FADE_SECONDS)])
        )
        scene_clips.append(scene)

    final = concatenate_videoclips(scene_clips, method="chain")

    if music_path:
        music = AudioFileClip(str(music_path))
        opened.append(music)
        music = music.with_effects([
            afx.AudioLoop(duration=final.duration),
            afx.MultiplyVolume(MUSIC_VOLUME),
            afx.AudioFadeOut(1.5),
        ])
        final = final.with_audio(CompositeAudioClip([final.audio, music]))

    output_path.parent.mkdir(parents=True, exist_ok=True)

    final.write_videofile(
        str(output_path),
        fps=config.VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        pixel_format="yuv420p",
        ffmpeg_params=["-movflags", "+faststart"],
        threads=4,
        logger=None,
    )

    final.close()
    for clip in opened:
        clip.close()

    logger.info("Video written: %s (%.1f s)", output_path, sum(durations))

    return durations


def find_background_music() -> Optional[Path]:

    if not config.MUSIC_DIR.exists():
        return None

    for pattern in ("*.mp3", "*.wav", "*.m4a"):
        tracks = sorted(config.MUSIC_DIR.glob(pattern))
        if tracks:
            return tracks[0]

    return None
