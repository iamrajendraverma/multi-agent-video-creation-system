import logging
from pathlib import Path

from PIL import Image

from services.scene_renderer import render_scene
from services.video_generator import compose_video, find_background_music
from services.voice_generator import generate_voice


logger = logging.getLogger(__name__)


def video_agent(state):

    storyboard = state.storyboard
    run_dir = Path(state.run_dir)
    attempt = state.iteration + 1

    scenes_dir = run_dir / "scenes"
    audio_dir = run_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    scene_images = []
    audio_paths = []

    for scene in storyboard.scenes:
        scene_images.append(
            render_scene(
                scene,
                storyboard.color_theme,
                len(storyboard.scenes),
                scenes_dir / f"scene_{scene.index:02d}.png",
            )
        )
        audio_paths.append(
            generate_voice(scene.narration, audio_dir / f"scene_{scene.index:02d}")
        )

    music = find_background_music()
    if music:
        logger.info("Background music: %s", music.name)

    video_path = run_dir / f"video_v{attempt}.mp4"

    state.scene_durations = compose_video(
        scene_images,
        audio_paths,
        [scene.narration for scene in storyboard.scenes],
        video_path,
        music_path=music,
    )

    # Thumbnail: the first (title) scene as JPEG
    thumbnail_path = run_dir / "thumbnail.jpg"
    Image.open(scene_images[0]).convert("RGB").save(thumbnail_path, quality=90)

    state.scene_images = scene_images
    state.audio_paths = audio_paths
    state.video_path = str(video_path)
    state.thumbnail_path = str(thumbnail_path)

    return state
