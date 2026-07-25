import asyncio
import json
import os
import edge_tts
import ollama
from pypdf import PdfReader
import streamlit as st

# Streamlit Page Setup
st.set_page_config(
    page_title="Syllabify AI - Podcast & Tutor Studio",
    page_icon="🎙️",
    layout="wide",
)

st.title("🎙️ Syllabify AI: Accessible Educational Studio PRO")
st.caption(
    "Visually Impaired & Dyslexic Students ke liye AI Podcast, Viva Test, aur Assignment Tutor"
)


# 1. PDF Text Extractor
def extract_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text[:3000]


# 2. Gemma Engine: Podcast + Viva Quiz Generator
def generate_podcast_and_viva(text_content, language="English"):
    lang_rule = (
        "Write in Roman Urdu (e.g. 'Aaj hum yeh parhenge...')"
        if language == "Roman Urdu"
        else "Write in English"
    )

    prompt = f"""
    You are an AI Educational Studio engine for visually impaired students.
    Process the provided text and output a JSON object with:
    1. "summary": A 2-sentence key takeaway of the text.
    2. "script": A 2-person educational dialogue (Tutor & Student).
    3. "viva": 3 interactive viva quiz questions with options, correct answer, and a short explanation.

    Rule: {lang_rule}
    Output MUST strictly be valid JSON with no markdown formatting.

    JSON Structure:
    {{
      "summary": "...",
      "script": [
        {{"speaker": "Tutor", "text": "..."}},
        {{"speaker": "Student", "text": "..."}}
      ],
      "viva": [
        {{
          "question": "...",
          "options": ["A", "B", "C", "D"],
          "answer": "Exact matching option text",
          "explanation": "Why this is correct..."
        }}
      ]
    }}

    Text:
    {text_content}
    """

    response = ollama.chat(
        model="gemma:2b", messages=[{"role": "user", "content": prompt}]
    )

    content = response["message"]["content"].strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:].strip()

    return json.loads(content)


# 3. Gemma Engine: Assignment Solver & Tutor Explanation
def solve_assignment(assignment_text, language="English"):
    lang_rule = (
        "Explain step-by-step in Roman Urdu"
        if language == "Roman Urdu"
        else "Explain step-by-step in clear English"
    )

    prompt = f"""
    You are a supportive AI Tutor helping a blind or dyslexic student with their assignment.
    Solve the assignment question provided, break down the step-by-step solution, and provide a clear explanation that can be converted to speech.

    Rule: {lang_rule}

    Format Output as JSON:
    {{
      "solution_text": "Detailed step-by-step solution and answer...",
      "audio_script": "Tutor audio response explaining how to solve this step-by-step..."
    }}

    Assignment Question/Text:
    {assignment_text}
    """

    response = ollama.chat(
        model="gemma:2b", messages=[{"role": "user", "content": prompt}]
    )

    content = response["message"]["content"].strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:].strip()

    return json.loads(content)


# 4. Audio Generator (Supports Dual Voice & Single Tutor Voice)
async def generate_audio(
    script,
    language="English",
    output_filename="podcast.mp3",
    single_voice=False,
):
    tutor_v = (
        "ur-PK-AsadNeural" if language == "Roman Urdu" else "en-US-GuyNeural"
    )
    student_v = (
        "ur-PK-UzmaNeural" if language == "Roman Urdu" else "en-US-AnaNeural"
    )

    os.makedirs("temp_chunks", exist_ok=True)
    audio_bytes = []

    if single_voice:
        # For Assignment Explanation
        comm = edge_tts.Communicate(script, tutor_v)
        await comm.save(output_filename)
        return

    for idx, line in enumerate(script):
        speaker = line.get("speaker", "Tutor")
        text = line.get("text", "")
        voice = tutor_v if speaker.lower() == "tutor" else student_v

        chunk_path = f"temp_chunks/chunk_{idx}.mp3"
        comm = edge_tts.Communicate(text, voice)
        await comm.save(chunk_path)

        with open(chunk_path, "rb") as f:
            audio_bytes.append(f.read())

    with open(output_filename, "wb") as f:
        for chunk in audio_bytes:
            f.write(chunk)


# ---------------- APP LAYOUT ----------------

app_mode = st.sidebar.radio(
    "Select Mode / Feature:",
    ["🎙️ Syllabus-to-Podcast & Viva", "📝 Assignment AI Solver"],
)
language = st.sidebar.selectbox("Language:", ["English", "Roman Urdu"])

# MODE 1: PODCAST & VIVA TEST
if app_mode == "🎙️ Syllabus-to-Podcast & Viva":
    st.header("🎙️ Chapter Podcast & Live Viva Test")

    uploaded_pdf = st.file_uploader("Upload Chapter PDF", type=["pdf"])
    raw_text = st.text_area("Or Paste Text Here:", height=150)

    input_data = ""
    if uploaded_pdf:
        input_data = extract_text(uploaded_pdf)
    elif raw_text:
        input_data = raw_text

    if st.button("🚀 Process Podcast & Viva Package", type="primary"):
        if not input_data.strip():
            st.warning("Please upload a PDF or paste text first!")
        else:
            with st.spinner("Gemma is generating podcast script & viva..."):
                try:
                    data = generate_podcast_and_viva(input_data, language)
                    st.session_state["studio_data"] = data

                    asyncio.run(
                        generate_audio(
                            data["script"], language, "podcast_audio.mp3"
                        )
                    )
                    st.success("✅ Package Ready!")
                except Exception as e:
                    st.error(f"Error: {e}")

    if "studio_data" in st.session_state:
        data = st.session_state["studio_data"]

        st.info(f"📌 **Audio Summary:** {data.get('summary', '')}")
        st.audio("podcast_audio.mp3")

        tab1, tab2 = st.tabs(["📜 Dialogue Script", "🎓 Interactive Viva Test"])

        with tab1:
            for line in data.get("script", []):
                spk = line.get("speaker", "Tutor")
                txt = line.get("text", "")
                st.markdown(
                    f"**{'👨‍🏫 Tutor' if spk.lower() == 'tutor' else '🧑‍🎓 Student'}:** {txt}"
                )

        with tab2:
            st.write("### 🎓 Test Your Knowledge (Viva Mode):")
            for i, q in enumerate(data.get("viva", [])):
                st.markdown(f"**Question {i+1}: {q.get('question')}**")
                ans = st.radio(
                    f"Select Answer Q{i+1}:",
                    q.get("options", []),
                    key=f"viva_{i}",
                )
                if st.button(f"Submit Answer Q{i+1}"):
                    if ans == q.get("answer"):
                        st.success("Correct! 🎉 " + q.get("explanation", ""))
                    else:
                        st.error(
                            f"Incorrect! Correct answer is: {q.get('answer')}. {q.get('explanation', '')}"
                        )

# MODE 2: ASSIGNMENT SOLVER
else:
    st.header("📝 Assignment Step-by-Step Solver & Audio Explanation")

    assign_pdf = st.file_uploader("Upload Assignment PDF", type=["pdf"])
    assign_text = st.text_area("Or Paste Question/Assignment Text:", height=150)

    a_input = ""
    if assign_pdf:
        a_input = extract_text(assign_pdf)
    elif assign_text:
        a_input = assign_text

    if st.button("💡 Solve & Generate Audio Explanation", type="primary"):
        if not a_input.strip():
            st.warning("Please enter your assignment question!")
        else:
            with st.spinner(
                "Gemma is solving the assignment and generating audio..."
            ):
                try:
                    result = solve_assignment(a_input, language)
                    st.session_state["assign_result"] = result

                    asyncio.run(
                        generate_audio(
                            result.get("audio_script", ""),
                            language,
                            "assignment_audio.mp3",
                            single_voice=True,
                        )
                    )
                    st.success("✅ Assignment Solved!")
                except Exception as e:
                    st.error(f"Error: {e}")

    if "assign_result" in st.session_state:
        res = st.session_state["assign_result"]

        st.subheader("🔊 Audio Explanation for Visually Impaired Students:")
        st.audio("assignment_audio.mp3")

        st.subheader("📖 Detailed Written Solution:")
        st.write(res.get("solution_text", ""))