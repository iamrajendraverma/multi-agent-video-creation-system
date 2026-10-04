import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent

load_dotenv(PROJECT_ROOT / ".env")


def _bool(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes")


# Claude
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "16000"))
# Server-side refusal fallbacks (Claude API only)
CLAUDE_FALLBACKS = _bool("CLAUDE_FALLBACKS", "true")

# Research
RESEARCH_WEB_SEARCH = _bool("RESEARCH_WEB_SEARCH", "true")
RESEARCH_MAX_SEARCHES = int(os.getenv("RESEARCH_MAX_SEARCHES", "5"))

# Voice: "google" (Google Cloud TTS) or "macos" (built-in `say`, for local testing)
VOICE_PROVIDER = os.getenv("VOICE_PROVIDER", "google")
GOOGLE_TTS_LANGUAGE = os.getenv("GOOGLE_TTS_LANGUAGE", "en-US")
GOOGLE_TTS_VOICE = os.getenv("GOOGLE_TTS_VOICE", "en-US-Neural2-D")
GOOGLE_TTS_SPEAKING_RATE = float(os.getenv("GOOGLE_TTS_SPEAKING_RATE", "1.05"))
MACOS_VOICE = os.getenv("MACOS_VOICE", "Samantha")

# Video
OUTPUT_ROOT = PROJECT_ROOT / os.getenv("OUTPUT_DIR", "output")
MUSIC_DIR = PROJECT_ROOT / "assets" / "music"
FONT_PATH = os.getenv("FONT_PATH", "")

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = int(os.getenv("VIDEO_FPS", "30"))
VIDEO_MIN_SECONDS = int(os.getenv("VIDEO_MIN_SECONDS", "30"))
VIDEO_MAX_SECONDS = int(os.getenv("VIDEO_MAX_SECONDS", "60"))
VIDEO_MAX_ITERATIONS = int(os.getenv("VIDEO_MAX_ITERATIONS", "3"))

# YouTube
YOUTUBE_CLIENT_SECRET_FILE = os.getenv(
    "YOUTUBE_CLIENT_SECRET_FILE", "client_secret.json"
)
YOUTUBE_TOKEN_FILE = os.getenv("YOUTUBE_TOKEN_FILE", "youtube_token.json")
YOUTUBE_PRIVACY = os.getenv("YOUTUBE_PRIVACY", "private")


def create_run_dir(user_prompt: str) -> Path:
    """
    Create a unique output folder for one pipeline run,
    e.g. output/20261004-153012-labor-market-trends-in-india
    """

    slug = re.sub(r"[^a-z0-9]+", "-", user_prompt.lower()).strip("-")[:40]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    run_dir = OUTPUT_ROOT / f"{timestamp}-{slug or 'video'}"
    run_dir.mkdir(parents=True, exist_ok=True)

    return run_dir
