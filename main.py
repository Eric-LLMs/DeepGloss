import streamlit as st
import os
from dotenv import load_dotenv

# 加载环境配置
load_dotenv()

st.set_page_config(
    page_title="DeepGloss",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 DeepGloss 学习助手")

st.markdown("""
### 欢迎使用 DeepGloss
这是一个垂直领域的英语学习工具。

请从左侧侧边栏选择功能：
- **import_data**: 导入词汇和文章
- **study_mode**: 开始学习
""")

# 检查环境变量
api_key = os.getenv("LLM_API_KEY")

if not api_key:
    st.warning("⚠️ 未检测到 .env 文件中的 LLM_API_KEY")
    st.info("请在项目根目录创建 .env 文件，并配置 LLM_API_KEY, LLM_BASE_URL, LLM_MODEL")
else:
    st.success("✅ API 环境已就绪")