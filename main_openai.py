import streamlit as st
import config

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

# 检查 API Key
import os
if not os.getenv("OPENAI_API_KEY"):
    st.warning("⚠️ 未检测到 .env 文件中的 API Key")
    key = st.text_input("请输入 OpenAI API Key", type="password")
    if key:
        os.environ["OPENAI_API_KEY"] = key
        st.success("API Key 已临时设置！")