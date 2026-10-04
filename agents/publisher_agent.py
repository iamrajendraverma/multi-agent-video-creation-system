import logging

from models.state import YouTubeMetadata
from prompts import load_prompt
from services.llm import ask_claude_structured
from services.youtube import set_thumbnail, upload_video


logger = logging.getLogger(__name__)

YOUTUBE_TITLE_LIMIT = 100
YOUTUBE_DESCRIPTION_LIMIT = 5000


def generate_metadata(state) -> YouTubeMetadata:

    metadata = ask_claude_structured(
        load_prompt(
            "metadata",
            user_prompt=state.user_prompt,
            script=state.script.full_text,
            sources="\n".join(state.research.sources),
        ),
        YouTubeMetadata,
    )

    metadata.title = metadata.title[:YOUTUBE_TITLE_LIMIT]
    metadata.description = metadata.description[:YOUTUBE_DESCRIPTION_LIMIT]

    if "#shorts" not in metadata.description.lower():
        metadata.description += "\n\n#Shorts"
    if "Shorts" not in metadata.tags:
        metadata.tags.append("Shorts")

    return metadata


def _confirmed(state) -> bool:

    if state.auto_confirm:
        return True

    meta = state.youtube_metadata
    print(
        f"\nReady to publish to YouTube ({state.privacy}):\n"
        f"  Video: {state.video_path}\n"
        f"  Title: {meta.title}\n"
        f"  Tags:  {', '.join(meta.tags)}\n"
    )
    answer = input("Publish now? [y/N] ").strip().lower()

    return answer in ("y", "yes")


def publisher_agent(state):

    state.youtube_metadata = generate_metadata(state)
    logger.info("YouTube title: %s", state.youtube_metadata.title)

    if not state.publish:
        logger.info("Publishing disabled (--no-publish); video kept locally")
        return state

    # Human-in-the-loop: nothing goes public without confirmation
    if not _confirmed(state):
        logger.info("Publishing cancelled by user")
        return state

    meta = state.youtube_metadata
    video_id, url = upload_video(
        state.video_path,
        title=meta.title,
        description=meta.description,
        tags=meta.tags,
        privacy_status=state.privacy,
    )
    state.youtube_url = url
    logger.info("Uploaded: %s", url)

    if state.thumbnail_path:
        try:
            set_thumbnail(video_id, state.thumbnail_path)
        except Exception as error:
            # Custom thumbnails need a verified channel; not fatal
            logger.warning("Could not set thumbnail: %s", error)

    return state
