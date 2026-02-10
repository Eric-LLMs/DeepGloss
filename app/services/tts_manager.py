import os
import hashlib
from openai import OpenAI
import config
import streamlit as st


class TTSManager:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            api_key = st.session_state.get("openai_api_key")

        # 👇 关键修改：传入 base_url
        if api_key:
            self.client = OpenAI(
                api_key=api_key,
                base_url=config.OPENAI_BASE_URL  # 使用转发地址
            )
        else:
            self.client = None

    def get_audio_path(self, text):
        """返回音频文件路径。如果缓存有就直接返回，没有就调API生成。"""
        if not text: return None

        # 1. 计算哈希
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        filename = f"{text_hash}.mp3"
        # 使用 config 中配置的路径
        file_path = config.AUDIO_CACHE_DIR / filename

        # 2. 检查缓存 (省钱逻辑)
        if file_path.exists():
            return str(file_path)

        # 3. 调用 API 生成
        if not self.client:
            st.warning("⚠️ 未配置 OpenAI API Key，无法生成语音。请在侧边栏或 .env 文件中配置。")
            return None

        try:
            response = self.client.audio.speech.create(
                model=config.TTS_MODEL,
                voice=config.TTS_VOICE,
                input=text
            )
            response.stream_to_file(file_path)
            return str(file_path)
        except Exception as e:
            st.error(f"TTS 生成失败: {e}")
            return None