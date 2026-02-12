@echo off
cd /d %~dp0
echo Starting DeepGloss...
call conda activate DeepGloss
streamlit run main.py
pause