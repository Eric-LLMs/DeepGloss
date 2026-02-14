import streamlit as st
import os
from dotenv import load_dotenv
from app.ui.sidebar import render_sidebar

# Load Environment Variables
load_dotenv()

st.set_page_config(
    page_title="DeepGloss",
    page_icon="🧠",
    layout="wide"
)

# Render the custom beautiful sidebar
render_sidebar()

st.title("🧠 DeepGloss Learning Assistant")

st.markdown("""
### Welcome to DeepGloss
A domain-specific English learning tool tailored for your specific needs.

**Please select a function from the sidebar:**
- 📥 **Import Data**: Import your vocabulary, sentences, and build VectorDB index.
- 📖 **Study Mode**: Start your immersive and interactive learning session with AI explanations and TTS.
- 🛠️ **Manage Vocabulary**: Edit definitions, levels, and enable/disable specific words.
""")

# Check API Key
api_key = os.getenv("LLM_API_KEY")

if not api_key:
    st.warning("⚠️ LLM_API_KEY not found in the .env file.")
    st.info("Please create a .env file in the project root and configure LLM_API_KEY, LLM_BASE_URL, and LLM_MODEL.")
else:
    st.success("✅ API Environment is properly configured and ready.")