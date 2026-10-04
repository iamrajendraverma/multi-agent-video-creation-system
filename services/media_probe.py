from dataclasses import dataclass
from pathlib import Path
from typing import List

from PIL import Image


@dataclass
class MediaInfo:
    duration: float
    has_video: bool
    has_audio: bool
    width: int
    height: int


def probe(path: str) -> MediaInfo:
    """
    Read duration, streams and resolution of a media file
    (uses the ffmpeg binary bundled with moviepy).
    """

    from moviepy.video.io.ffmpeg_reader import ffmpeg_parse_infos

    infos = ffmpeg_parse_infos(str(path), decode_file=True)
    width, height = infos.get("video_size") or (0, 0)

    return MediaInfo(
        duration=float(infos.get("duration") or 0.0),
        has_video=bool(infos.get("video_found")),
        has_audio=bool(infos.get("audio_found")),
        width=int(width),
        height=int(height),
    )


def audio_duration(path: str) -> float:

    from moviepy import AudioFileClip

    with AudioFileClip(str(path)) as clip:
        return float(clip.duration)


def extract_frames(video_path: str, times: List[float], output_dir: Path) -> List[str]:
    """
    Save the frames at the given timestamps (seconds) as PNG files.
    """

    from moviepy import VideoFileClip

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    with VideoFileClip(str(video_path), audio=False) as clip:
        for number, time in enumerate(times, start=1):
            frame = clip.get_frame(min(time, clip.duration - 0.05))
            path = output_dir / f"frame_{number:02d}.png"
            # Half size is plenty for review and keeps requests small
            image = Image.fromarray(frame)
            image.thumbnail((540, 960))
            image.save(path)
            paths.append(str(path))

    return paths
