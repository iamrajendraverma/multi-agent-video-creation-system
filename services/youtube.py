from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import config


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload"
]

CLIENT_SECRET_FILE = config.YOUTUBE_CLIENT_SECRET_FILE
TOKEN_FILE = config.YOUTUBE_TOKEN_FILE


def get_youtube_client():

    credentials = None

    # Load existing token
    if Path(TOKEN_FILE).exists():
        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    # Refresh expired token
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    # First-time authentication
    if not credentials or not credentials.valid:

        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            SCOPES
        )

        credentials = flow.run_local_server(
            port=0
        )

        # Save credentials for future runs
        with open(TOKEN_FILE, "w") as token:
            token.write(credentials.to_json())

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials
    )

    return youtube


def upload_video(
    video_path: str,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    privacy_status: str = config.YOUTUBE_PRIVACY
) -> tuple[str, str]:
    """
    Upload a video. Returns (video_id, watch URL).
    """

    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(
            f"Video not found: {video_path}"
        )

    youtube = get_youtube_client()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }

    media = MediaFileUpload(
        str(video_path),
        chunksize=-1,
        resumable=True,
        mimetype="video/mp4"
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = request.execute()

    video_id = response["id"]

    return video_id, f"https://www.youtube.com/shorts/{video_id}"


def set_thumbnail(video_id: str, image_path: str) -> None:

    youtube = get_youtube_client()

    youtube.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(image_path, mimetype="image/jpeg")
    ).execute()