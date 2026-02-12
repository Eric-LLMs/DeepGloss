from pathlib import Path
from openai import OpenAI
import hashlib
import config  # Import the configuration module


class TTSManager:
    def __init__(self):
        # Initialize OpenAI client using unified settings from config.py
        # Uses LLM_BASE_URL and LLM_API_KEY to allow provider swapping
        self.client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY
        )

        # Use the path resolved in config.py
        self.output_dir = config.AUDIO_CACHE_DIR

        # Double check existence
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_audio_path(self, text):
        """
        Generates TTS audio for the given text.
        Returns the absolute file path.
        Checks cache first to avoid API costs.
        """
        if not text or len(text.strip()) == 0:
            return None

        # Create a hash of the text to serve as the filename
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        file_name = f"{text_hash}.mp3"
        file_path = self.output_dir / file_name

        # Return existing path if cached
        if file_path.exists():
            return str(file_path)

        # Generate new audio if not in cache
        try:
            response = self.client.audio.speech.create(
                model=config.TTS_MODEL,
                voice=config.TTS_VOICE,
                input=text
            )
            # Save to the configured directory
            response.stream_to_file(file_path)
            return str(file_path)

        except Exception as e:
            print(f"TTS Error: {e}")
            return None