@echo off
echo Starting DeepGloss...
call conda activate english_app
streamlit run main.py
pause