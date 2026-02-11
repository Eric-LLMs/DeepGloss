import streamlit as st
import os
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

st.set_page_config(
    page_title="DeepGloss",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 DeepGloss Learning Assistant")

st.markdown("""
### Welcome to DeepGloss
A domain-specific English learning tool tailored for your specific needs.

Please select a function from the sidebar:
- **import_data**: Import your vocabulary and sentences
- **study_mode**: Start studying
""")

# Check API Key
api_key = os.getenv("LLM_API_KEY")

if not api_key:
    st.warning("⚠️ LLM_API_KEY not found in the .env file.")
    st.info("Please create a .env file in the project root and configure LLM_API_KEY, LLM_BASE_URL, and LLM_MODEL.")
else:
    st.success("✅ API Environment is properly configured and ready.")