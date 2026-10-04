import logging
import re
import subprocess
from pathlib import Path
from typing import List

import config


logger = logging.getLogger(__name__)

# Google Cloud TTS rejects requests above 5000 bytes of input
GOOGLE_TTS_MAX_BYTES = 4500


def generate_voice(text: str, output_path: Path) -> str:
    """
    Convert text to speech and save it to output_path
    (the extension is chosen by the provider).

    Returns:
        Path to the generated audio file.
    """

    if config.VOICE_PROVIDER == "macos":
        return _generate_macos(text, output_path.with_suffix(".aiff"))

    return _generate_google(text, output_path.with_suffix(".mp3"))


def _generate_google(text: str, output_path: Path) -> str:

    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()

    voice = texttospeech.VoiceSelectionParams(
        language_code=config.GOOGLE_TTS_LANGUAGE,
        name=config.GOOGLE_TTS_VOICE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=config.GOOGLE_TTS_SPEAKING_RATE,
    )

    # MP3 streams can be concatenated byte-wise
    with open(output_path, "wb") as audio_file:
        for chunk in _split_text(text, GOOGLE_TTS_MAX_BYTES):
            response = client.synthesize_speech(
                input=texttospeech.SynthesisInput(text=chunk),
                voice=voice,
                audio_config=audio_config,
            )
            audio_file.write(response.audio_content)

    logger.info("Voice generated: %s", output_path)

    return str(output_path)


def _generate_macos(text: str, output_path: Path) -> str:

    subprocess.run(
        ["say", "-v", config.MACOS_VOICE, "-o", str(output_path), text],
        check=True,
    )

    logger.info("Voice generated (macOS say): %s", output_path)

    return str(output_path)


def _split_text(text: str, max_bytes: int) -> List[str]:
    """
    Split text at sentence boundaries into chunks of at most max_bytes.
    """

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks = [""]

    for sentence in sentences:
        candidate = f"{chunks[-1]} {sentence}".strip()

        if len(candidate.encode("utf-8")) <= max_bytes:
            chunks[-1] = candidate
        else:
            chunks.append(sentence)

    return [chunk for chunk in chunks if chunk]
