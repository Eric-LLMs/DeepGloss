from pathlib import Path
import hashlib

import numpy as np
import soundfile as sf

import config  # Import the configuration module


class TTSManager:
    def __init__(self):
        # Use the path resolved in config.py
        self.output_dir = config.AUDIO_CACHE_DIR

        # Ensure the directory exists
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)

        # Kokoro pipeline is loaded lazily on first use (it downloads/loads
        # the ~320MB model), so constructing TTSManager stays cheap.
        self._pipeline = None

    def _get_pipeline(self):
        if self._pipeline is None:
            from kokoro import KPipeline

            # 'a' = American English (uses misaki[en] for phonemization)
            self._pipeline = KPipeline(lang_code="a")
        return self._pipeline

    def get_audio_path(self, text):
        """
        Generates TTS audio for the given text via local Kokoro-82M.
        Returns the absolute file path.
        Checks cache first to avoid redundant generation.
        """
        if not text or len(text.strip()) == 0:
            return None

        # Unique hash from text + voice, prefixed with the provider so the
        # local Kokoro WAV cache never collides with the old OpenAI MP3 cache.
        hash_input = f"kokoro_{text}_{config.TTS_VOICE}"
        text_hash = hashlib.md5(hash_input.encode("utf-8")).hexdigest()

        file_name = f"{text_hash}.wav"
        file_path = self.output_dir / file_name

        # Return the existing path if already cached
        if file_path.exists():
            return str(file_path)

        try:
            pipeline = self._get_pipeline()
            generator = pipeline(text, voice=config.TTS_VOICE)

            # Concatenate all yielded segments into a single waveform
            audio = None
            for _gs, _ps, segment in generator:
                if audio is None:
                    audio = segment
                else:
                    audio = np.concatenate([audio, segment])

            if audio is None:
                return None

            # Kokoro outputs 24kHz float32 audio
            sf.write(file_path, audio, 24000)
            return str(file_path)

        except Exception as e:
            print(f"TTS Error: {e}")
            return None
