from pathlib import Path
from openai import OpenAI
import hashlib
import config  # Import the configuration module


class TTSManager:
    def __init__(self):
        # Initialize OpenAI client using dedicated TTS settings from config.py
        # This allows using different providers/tokens for TTS and LLM
        self.client = OpenAI(
            base_url=config.TTS_BASE_URL,
            api_key=config.TTS_API_KEY
        )

        # Use the path resolved in config.py
        self.output_dir = config.AUDIO_CACHE_DIR

        # Ensure the directory exists
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_audio_path(self, text):
        """
        Generates TTS audio for the given text.
        Returns the absolute file path.
        Checks cache first to avoid redundant API costs.
        """
        if not text or len(text.strip()) == 0:
            return None

        # Create a unique hash by combining text, model, and voice settings.
        # This prevents new generations from overwriting old files physically
        # until the user explicitly clicks "Save" to update the database.
        hash_input = f"{text}_{config.TTS_MODEL}_{config.TTS_VOICE}"
        text_hash = hashlib.md5(hash_input.encode('utf-8')).hexdigest()

        file_name = f"{text_hash}.mp3"
        file_path = self.output_dir / file_name

        # Return the existing path if this specific version is already cached
        if file_path.exists():
            return str(file_path)

        # Generate new audio if it does not exist in the cache
        try:
            response = self.client.audio.speech.create(
                model=config.TTS_MODEL,
                voice=config.TTS_VOICE,
                input=text
            )
            # Save the new audio file to the configured directory
            response.stream_to_file(file_path)
            return str(file_path)

        except Exception as e:
            print(f"TTS Error: {e}")
            return None