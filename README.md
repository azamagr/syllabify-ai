# 🎙️ Syllabify AI: Educational Podcast & Accessibility Studio

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://syllabify-ai-jumfwpgniusmy7eqcrf2py.streamlit.app/)
[![Powered by Google Gemma](https://img.shields.io/badge/Model-Google%20Gemma%202B-blue.svg)](https://ai.google.dev/gemma)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)

> **Syllabify AI** is an AI-powered accessibility platform designed for **Visually Impaired & Dyslexic Students**. It transforms dense academic documents (PDFs) into dynamic, multi-voice educational podcast dialogues, interactive oral viva assessments, and step-by-step audio assignment solutions.

🚀 **[Click Here for Live Interactive Demo](https://syllabify-ai-jumfwpgniusmy7eqcrf2py.streamlit.app/)**

---

## 🎯 The Problem

Over **2.2 billion people** globally live with vision impairment or print disabilities like dyslexia. Traditional screen readers are often:
- Monotonous and robotic.
- Difficult to navigate for long textbook chapters.
- Passive, lacking interactive learning mechanisms.

## 💡 Our Solution

Syllabify AI reimagines reading materials into engaging, structured audio experiences using **Google's Gemma LLM** and **Neural Text-to-Speech (TTS)**:

1. **🎙️ Educational Podcast Studio:** Converts static PDF text into a back-and-forth educational dialogue between a **Tutor** and a **Student**.
2. **🎓 Interactive Viva Test:** Generates oral practice quiz questions with instant feedback and explanations.
3. **📝 Assignment AI Solver:** Breaks down complex assignment questions into step-by-step written solutions accompanied by audio explanations.
4. **⚡ Audio Revision Flashcards:** Provides bite-sized key concept summaries for quick exam prep with playback speed control.
5. **🌐 Localization:** Full support for both **English** and **Roman Urdu** for localized learning accessibility.

---

## 🛠️ Tech Stack & Architecture

- **Large Language Model (LLM):** Google Gemma 2B (`gemma:2b`) running via Ollama.
- **Neural Text-to-Speech Engine:** `edge-tts` (Microsoft Azure Neural Voices).
  - *Tutor Voices:* `en-US-GuyNeural` / `ur-PK-AsadNeural`
  - *Student Voices:* `en-US-AnaNeural` / `ur-PK-UzmaNeural`
- **Frontend Framework:** Streamlit (Custom Accessible CSS).
- **Document Processing:** PyPDF text extraction engine.

---

## 📁 Repository Structure

```text
├── app.py              # Main Streamlit Application Pipeline
├── requirements.txt    # Python Dependencies for Deployment
├── README.md           # Project Documentation
└── .gitignore          # Environment and Cache Ignores