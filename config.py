import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ================= Path Configuration =================

# Project Root: Parent directory of this config file
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR

# Path to the YAML configuration file
CONFIG_YAML_PATH = PROJECT_ROOT / "config.yaml"

# Default fallback path for audio and image
DEFAULT_AUDIO_PATH = "data/audio_cache"
DEFAULT_IMAGE_PATH = "data/image_cache"

# Load YAML configuration
config_data = {}
if CONFIG_YAML_PATH.exists():
    try:
        with open(CONFIG_YAML_PATH, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Failed to load config.yaml: {e}")

# --- 1. Audio Cache Directory Setup ---
storage_conf = config_data.get("storage", {})
raw_audio_path = storage_conf.get("audio_cache_path", DEFAULT_AUDIO_PATH)

if os.path.isabs(raw_audio_path):
    AUDIO_CACHE_DIR = Path(raw_audio_path)
else:
    AUDIO_CACHE_DIR = PROJECT_ROOT / raw_audio_path

try:
    AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Error creating audio directory at {AUDIO_CACHE_DIR}: {e}")
    AUDIO_CACHE_DIR = PROJECT_ROOT / "data" / "audio_cache"
    AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# --- 1.1 Image Cache Directory Setup ---
raw_image_path = storage_conf.get("image_cache_path", DEFAULT_IMAGE_PATH)

if os.path.isabs(raw_image_path):
    IMAGE_CACHE_DIR = Path(raw_image_path)
else:
    IMAGE_CACHE_DIR = PROJECT_ROOT / raw_image_path

try:
    IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Error creating image directory at {IMAGE_CACHE_DIR}: {e}")
    IMAGE_CACHE_DIR = PROJECT_ROOT / "data" / "image_cache"
    IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)


# --- 2. General Data Directory ---
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ================= Model & Network Configuration =================

model_conf = config_data.get("models", {})

# Models from YAML (or defaults)
LLM_MODEL = model_conf.get("llm", "o3-mini")
TTS_MODEL = model_conf.get("tts", "tts-1-hd")
TTS_VOICE = model_conf.get("tts_voice", "alloy")

# --- Unified API Configuration ---

# 1. API Key: Priority -> LLM_API_KEY > OPENAI_API_KEY
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")

# 2. Base URL: Priority -> LLM_BASE_URL > OPENAI_BASE_URL > DEEPSEEK_BASE_URL > Default
LLM_BASE_URL = (
    os.getenv("LLM_BASE_URL")
    or os.getenv("OPENAI_BASE_URL")
    or os.getenv("DEEPSEEK_BASE_URL")
    or "https://api.openai.com/v1"
)