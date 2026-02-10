import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ... (路径配置保持不变) ...

# 5. 模型与网络配置
LLM_MODEL = "gpt-4o-mini"
TTS_MODEL = "tts-1"
TTS_VOICE = "alloy"

# 👇 新增：读取 Base URL，如果没有配置则默认用官方的
OPENAI_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")