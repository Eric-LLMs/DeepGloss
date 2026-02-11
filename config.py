import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ================= 路径配置（保持通用，不依赖具体平台） =================
# 项目根目录：config.py 所在目录的上一级
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR

# 数据目录：用于存放数据库、音频缓存等
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 音频缓存目录：TTS 生成的 mp3 会缓存在这里，避免重复调用 API
AUDIO_CACHE_DIR = DATA_DIR / "audio_cache"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ================= 模型与网络配置 =================
# 默认使用 OpenAI 官方模型
LLM_MODEL = "o3-mini"          # 用于文本翻译 / 解释
TTS_MODEL = "tts-1-hd"         # 用于 TTS 读音与音频生成
TTS_VOICE = "alloy"

# 👇 优先读取 OPENAI_BASE_URL，其次兼容通用 LLM_BASE_URL / 旧的 DEEPSEEK_BASE_URL，最后回落到官方地址
OPENAI_BASE_URL = (
    os.getenv("OPENAI_BASE_URL")
    or os.getenv("LLM_BASE_URL")
    or os.getenv("DEEPSEEK_BASE_URL")
    or "https://api.openai.com/v1"
)