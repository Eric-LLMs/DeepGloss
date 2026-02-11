# 🧠 DeepGloss

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**DeepGloss** is a smart, domain-specific English learning assistant built with Streamlit and powered by Large Language Models (LLMs). 

Unlike generic dictionary apps, DeepGloss focuses on **contextual learning** within specific domains (e.g., "Stanford CS336 Lectures", "Legal English", "Medical Terms"). It allows users to import customized vocabulary and corpus, automatically fetches definitions, generates Text-to-Speech (TTS) audio, provides context-aware AI translations, and offers interactive voice recording for pronunciation comparison.

---

## 📸 Screenshots

**1. Clean & Modern Vocabulary List**
Seamlessly sort, search, and view inline definitions via hover popovers without leaving the page.
![Vocabulary List](screenshots/listpage_demo.png)

**2. Immersive Study Dialog**
Practice pronunciation with the built-in HTML5 mic widget, compare with native TTS, and get AI-powered contextual explanations for sentences.
![Practice Dialog](screenshots/practice_demo.png)

**3. Smart Data Import Center**
Manage domains and easily import customized vocabulary and corpus with intelligent deduplication.
![Data Import](screenshots/data_upload_demo.png)
## ✨ Key Features

### 📥 Smart Data Ingestion
* **Domain Management**: Organize your learning materials into isolated domains.
* **Flexible Import**: Import vocabulary (with frequencies) and contextual sentences via CSV/Excel uploads or manual text pasting.
* **Intelligent Deduplication**: Automatically skips existing terms during import (case-insensitive) to maintain a clean database.

### 📖 Minimalist & Powerful Study Mode
* **Client-side Pagination & Sorting**: Lightning-fast UI with in-memory pagination. Sort vocabulary by Word (A-Z), Frequency, or Importance Level (Stars).
* **Advanced Filtering**: Filter your study list by specific domains or star levels.
* **Real-time Search**: Instantly find terms in your current list with a responsive search bar.
* **Hover Definitions**: Clean UI using popovers to view definitions without leaving the list.

### 🤖 AI-Powered Interactive Study Dialog
* **Context-Aware Explanations**: Uses LLMs to translate sentences and explain *exactly* what a term means within that specific context.
* **Auto-Fetch Definitions**: If a term lacks a definition, the system automatically calls the LLM in the background to fetch a precise English definition and Chinese translation.
* **Audio & Pronunciation**: 
  * Generate high-quality TTS audio for words and full sentences on the fly.
  * **Built-in Mic Widget**: Record your own voice directly in the browser and compare it with the generated TTS audio for pronunciation practice.
* **Importance Rating**: Rate terms from 1 to 5 stars (⭐⭐⭐⭐⭐) to prioritize your learning.

---

## 🛠️ Technology Stack

* **Frontend & Framework**: [Streamlit](https://streamlit.io/) (with custom CSS injection and HTML components for mic recording)
* **Backend**: Python 3.10+
* **Database**: SQLite3 (Local, lightweight, with auto-schema migration)
* **AI Integration**: [OpenAI SDK](https://github.com/openai/openai-python) (Compatible with OpenAI, DeepSeek, Moonshot, etc.)
* **Data Processing**: Pandas, Regex

---

## 📂 Project Architecture

DeepGloss follows a clean, modular, and maintainable architecture separating UI, services, and database logic:

```text
DeepGloss/
├── app/
│   ├── database/        # Database connection, schemas, and queries
│   │   ├── db_manager.py
│   │   └── schema.sql
│   ├── services/        # Third-party integrations & core logic
│   │   ├── ingestion.py # Text processing & parsing
│   │   ├── llm_client.py# Universal LLM client (OpenAI/DeepSeek compatible)
│   │   └── tts_manager.py
│   ├── ui/              # Modular UI components
│   │   ├── mic_widget.py    # Custom HTML5 audio recording component
│   │   └── study_dialog.py  # Modal dialog logic for studying
│   └── utils/           # Helper scripts
├── data/
│   ├── audio_cache/     # Local storage for generated TTS audio
│   └── deepgloss.db     # SQLite database file
├── pages/               # Streamlit multi-page routing
│   ├── import_data.py   # Page 1: Data ingestion
│   └── study_mode.py    # Page 2: Study interface
├── .env                 # Environment variables (API Keys - Git ignored)
├── .gitignore           # Git ignore rules
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
└── start.bat            # Windows quick-start script

```

---

## 🚀 Getting Started

### 1. Prerequisites

Ensure you have Python 3.8+ (Recommended: 3.10+) installed on your system.

### 2. Clone the Repository

Clone the repository to your local machine:

```bash
git clone https://github.com/Eric-LLMs/DeepGloss.git
cd DeepGloss

```

### 3. Install Dependencies

It is highly recommended to use a virtual environment:

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt

```

### 4. Configuration (.env)

Create a `.env` file in the root directory. DeepGloss uses a universal LLM client, allowing you to use OpenAI, DeepSeek, or other compatible APIs.

Add the following to your `.env` file:

```env
# Required: Your LLM API Key
LLM_API_KEY=your_api_key_here

# Optional: Base URL (Defaults to OpenAI if omitted. Change this for DeepSeek/Moonshot etc.)
LLM_BASE_URL=[https://api.openai.com/v1](https://api.openai.com/v1)

# Optional: Model Name (Defaults to o3-mini)
LLM_MODEL=o3-mini

```

### 5. Run the Application

Start the Streamlit development server:

```bash
streamlit run main.py

```

*(Alternatively, simply double-click the `start.bat` file if you are on Windows).*

---

## 💡 How to Use

1. **Import Data**: Navigate to the `import_data` page from the sidebar. Create a new "Domain" (e.g., "AI Research Papers"). Upload your vocabulary CSV or paste text directly.
2. **Add Corpus**: Switch to the "Import Sentences" tab and upload the source text or sentences where these words appear.
3. **Start Studying**: Navigate to `study_mode`. Filter your list, sort by frequency or stars, and click **⚡ Practice** on any word to open the immersive study dialog.
4. **Interact**: Generate audio, record your voice, read context-aware AI explanations, and rate the word's difficulty. Click **💾 Save** to sync your progress to the local database.

---

## 📝 License

This project is licensed under the MIT License. See the LICENSE file for details.
