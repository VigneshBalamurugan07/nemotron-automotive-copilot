"""
Audio & Text-to-Speech Engine for NemoDrive-AI In-Cabin Voice Synthesis.
Supports gTTS audio generation and browser Web Speech Audio player integration.
"""

import io
import base64
import logging
from typing import Optional

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

from src.config import config

logger = logging.getLogger(__name__)


class TTSEngine:
    """
    Synthesizes spoken automotive voice guidance into audio bytes / HTML audio elements.
    """

    def __init__(self, lang: str = "en"):
        self.lang = lang or config.voice_language
        self.enabled = config.enable_voice_tts

    def synthesize_to_bytes(self, text: str) -> Optional[bytes]:
        """Convert text into MP3 audio bytes using gTTS."""
        if not self.enabled or not text.strip() or gTTS is None:
            return None
        try:
            # Clean text for clean speech
            clean_text = text.replace("🚨", "").replace("🔴", "").replace("❄️", "").replace("🔥", "").replace("*", "")
            tts = gTTS(text=clean_text, lang=self.lang, slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except Exception as e:
            logger.warning(f"Error generating audio with gTTS: {e}")
            return None

    def get_audio_html_tag(self, text: str, auto_play: bool = True) -> str:
        """Returns an auto-playing HTML5 audio element encoded in base64."""
        audio_bytes = self.synthesize_to_bytes(text)
        if not audio_bytes:
            return ""

        b64 = base64.b64encode(audio_bytes).decode()
        autoplay_attr = "autoplay" if auto_play else ""
        return f"""
        <div style="margin-top: 8px; margin-bottom: 12px;">
            <audio controls {autoplay_attr} style="width: 100%; height: 36px; border-radius: 8px;">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                Your browser does not support audio playback.
            </audio>
        </div>
        """
