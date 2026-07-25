import asyncio
import json
import os
import re
import edge_tts
import ollama
from pypdf import PdfReader
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Syllabify AI - Educational Podcast Studio",
    page_icon="🎙️",
    layout="wide",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stButton>button { width: 100%; font-weight: bold; border-radius: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# Helper function to clean LLM JSON response safely
def clean_json_response(content):
    content = content.strip()
    if "```" in content:
        content = re.sub(r"```json\s*", "", content)
        content = re.sub(r"```\s*", "", content)
    return json.loads(content.strip())


# 1. Text Extractor Function
def extract_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text[:3000]


# 2. Gemma AI Engine: Extended Podcast Dialogue & Summary
def generate_podcast_and_summary(text_content, language="English"):
    lang_rule = (
        "Write in Roman Urdu (e.g. 'Aaj hum yeh parhenge...')"
        if language == "Roman Urdu"
        else "Write in English"
    )

    prompt = f"""
    You are an AI Educational Studio engine for visually impaired students.
    Process the provided text and output a JSON object with:
    1. "summary": A 2-sentence key takeaway of the text.
    2. "script": A detailed back-and-forth educational dialogue between Tutor and Student.

    CRITICAL RULES FOR "script":
    - Generate AT LEAST 5 to 8 back-and-forth dialogue exchanges (Q&A turns).
    - Tutor asks multiple different questions covering the main topics of the text step-by-step.
    - Student provides clear, detailed answers and asks follow-up questions.
    - {lang_rule}
    - Output MUST strictly be valid JSON with no markdown formatting or extra text.

    JSON Structure:
    {{
      "summary": "...",
      "script": [
        {{"speaker": "Tutor", "text": "Welcome! Today we will learn about... First, what is...?"}},
        {{"speaker": "Student", "text": "An operating system is..."}},
        {{"speaker": "Tutor", "text": "Great! Now how does it handle process scheduling?"}},
        {{"speaker": "Student", "text": "Process scheduling is handled by..."}}
      ]
    }}

    Text:
    {text_content}
    """

    response = ollama.chat(
        model="gemma:2b", messages=[{"role": "user", "content": prompt}]
    )

    return clean_json_response(response["message"]["content"])


# 3. Gemma AI Engine: Viva Quiz
def generate_viva_quiz(text_content, language="English"):
    lang_rule = (
        "Write questions and options in Roman Urdu"
        if language == "Roman Urdu"
        else "Write in English"
    )

    prompt = f"""
    Generate 3 interactive viva quiz questions based on the provided text.

    Rule: {lang_rule}
    Output MUST strictly be valid JSON with no markdown formatting.

    JSON Structure:
    {{
      "viva": [
        {{
          "question": "...",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "answer": "Exact matching option text",
          "explanation": "Why this option is correct..."
        }}
      ]
    }}

    Text:
    {text_content}
    """

    response = ollama.chat(
        model="gemma:2b", messages=[{"role": "user", "content": prompt}]
    )

    return clean_json_response(response["message"]["content"])


# 4. Gemma AI Engine: Assignment Solver
def solve_assignment(assignment_text, language="English"):
    lang_rule = (
        "Explain step-by-step in Roman Urdu"
        if language == "Roman Urdu"
        else "Explain step-by-step in clear English"
    )

    prompt = f"""
    You are a supportive AI Tutor helping a blind or dyslexic student.
    Solve the assignment question provided and explain step-by-step.

    Rule: {lang_rule}

    Format Output as JSON:
    {{
      "solution_text": "Detailed step-by-step solution...",
      "audio_script": "Tutor audio response explaining how to solve this step-by-step..."
    }}

    Assignment Question:
    {assignment_text}
    """

    response = ollama.chat(
        model="gemma:2b", messages=[{"role": "user", "content": prompt}]
    )

    return clean_json_response(response["message"]["content"])


# 5. Audio Generator Engine
async def generate_audio(
    script,
    language="English",
    output_filename="podcast.mp3",
    single_voice=False,
    speed="+0%",
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
        comm = edge_tts.Communicate(script, tutor_v, rate=speed)
        await comm.save(output_filename)
        return

    for idx, line in enumerate(script):
        speaker = line.get("speaker", "Tutor")
        text = line.get("text", "")
        voice = tutor_v if speaker.lower() == "tutor" else student_v

        chunk_path = f"temp_chunks/chunk_{idx}.mp3"
        comm = edge_tts.Communicate(text, voice, rate=speed)
        await comm.save(chunk_path)

        with open(chunk_path, "rb") as f:
            audio_bytes.append(f.read())

    with open(output_filename, "wb") as f:
        for chunk in audio_bytes:
            f.write(chunk)


# ---------------- SIDEBAR CONTROLS ----------------
st.sidebar.title("⚙️ Studio Settings")

MODE_PODCAST = "🎙️ Educational Podcast Studio"
MODE_VIVA = "🎓 Interactive Viva Test"
MODE_ASSIGNMENT = "📝 Assignment AI Solver"

app_mode = st.sidebar.radio(
    "Select Feature Mode:",
    [MODE_PODCAST, MODE_VIVA, MODE_ASSIGNMENT],
)

language = st.sidebar.selectbox("Preferred Language:", ["English", "Roman Urdu"])

speed_option = st.sidebar.select_slider(
    "🔊 Audio Playback Speed:",
    options=["Slow (-20%)", "Normal (0%)", "Fast (+20%)", "Very Fast (+40%)"],
    value="Normal (0%)",
)

speed_map = {
    "Slow (-20%)": "-20%",
    "Normal (0%)": "+0%",
    "Fast (+20%)": "+20%",
    "Very Fast (+40%)": "+40%",
}
selected_speed = speed_map[speed_option]


# ---------------- MODE 1: PODCAST STUDIO ----------------
if app_mode == MODE_PODCAST:
    st.title("🎙️ Syllabify AI: Educational Podcast Studio")
    st.caption(
        "Visually Impaired & Dyslexic Students ke liye AI-Powered Learning App"
    )

    st.markdown("### PDF File Upload Karein")
    uploaded_pdf = st.file_uploader(
        "Upload PDF file", type=["pdf"], label_visibility="collapsed"
    )

    st.markdown("### Or Paste The Text Directly:")
    text_input = st.text_area(
        "Paste text here", height=150, label_visibility="collapsed"
    )

    final_text = ""
    if uploaded_pdf:
        final_text = extract_text(uploaded_pdf)
        st.success("✅ PDF Text Extracted Successfully!")
    elif text_input:
        final_text = text_input

    if st.button("🚀 Generate Podcast", type="primary"):
        if not final_text.strip():
            st.warning("Pehle PDF upload karein ya direct text paste karein!")
        else:
            with st.spinner("Gemma is generating podcast dialogue audio..."):
                try:
                    data = generate_podcast_and_summary(final_text, language)
                    st.session_state["podcast_data"] = data

                    asyncio.run(
                        generate_audio(
                            data["script"],
                            language,
                            "podcast_audio.mp3",
                            speed=selected_speed,
                        )
                    )
                    st.success("🎉 Podcast Generated Successfully!")
                except Exception as e:
                    st.error(f"Error: {e}")

    if "podcast_data" in st.session_state:
        pdata = st.session_state["podcast_data"]

        st.markdown("---")
        st.subheader("🎧 Audio Output")
        st.info(f"📌 **Key Summary:** {pdata.get('summary', '')}")
        st.audio("podcast_audio.mp3")

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            with open("podcast_audio.mp3", "rb") as f:
                st.download_button(
                    "📥 Download MP3 Audio",
                    f,
                    file_name="syllabify_podcast.mp3",
                    mime="audio/mp3",
                )
        with col_d2:
            script_text = "\n".join(
                [
                    f"{x.get('speaker')}: {x.get('text')}"
                    for x in pdata.get("script", [])
                ]
            )
            st.download_button(
                "📜 Download Script (.txt)",
                script_text,
                file_name="script.txt",
                mime="text/plain",
            )

        st.subheader("📜 Dialogue Transcript")
        for line in pdata.get("script", []):
            spk = line.get("speaker", "Tutor")
            txt = line.get("text", "")
            st.markdown(
                f"**{'👨‍🏫 Tutor' if spk.lower() == 'tutor' else '🧑‍🎓 Student'}:** {txt}"
            )


# ---------------- MODE 2: INTERACTIVE VIVA TEST ----------------
elif app_mode == MODE_VIVA:
    st.title("🎓 Syllabify AI: Interactive Viva Test")
    st.caption("Audio-Based Interactive Questions & Self-Assessment Studio")

    st.markdown("### Upload Chapter PDF for Viva Quiz")
    viva_pdf = st.file_uploader("Upload PDF", type=["pdf"])
    viva_text = st.text_area("Or Paste Notes/Text for Viva:")

    v_input = ""
    if viva_pdf:
        v_input = extract_text(viva_pdf)
    elif viva_text:
        v_input = viva_text

    if st.button("🎯 Generate Viva Test Questions", type="primary"):
        if not v_input.strip():
            st.warning("Please upload a PDF or enter text!")
        else:
            with st.spinner("Gemma is extracting viva quiz questions..."):
                try:
                    v_data = generate_viva_quiz(v_input, language)
                    st.session_state["viva_data"] = v_data
                    st.success("✅ Viva Test Ready!")
                except Exception as e:
                    st.error(f"Error: {e}")

    if "viva_data" in st.session_state:
        vdata = st.session_state["viva_data"]
        st.markdown("---")
        st.subheader("🎓 Live Interactive Viva Test")

        for i, q in enumerate(vdata.get("viva", [])):
            st.markdown(f"**Q{i+1}: {q.get('question')}**")
            user_ans = st.radio(
                f"Select Answer Q{i+1}:",
                q.get("options", []),
                key=f"viva_opt_{i}",
            )

            if st.button(f"Submit Answer Q{i+1}"):
                if user_ans == q.get("answer"):
                    st.success("Correct! 🎉 " + q.get("explanation", ""))
                else:
                    st.error(
                        f"Incorrect! Correct Answer: {q.get('answer')}. {q.get('explanation', '')}"
                    )


# ---------------- MODE 3: ASSIGNMENT SOLVER ----------------
elif app_mode == MODE_ASSIGNMENT:
    st.title("📝 Syllabify AI: Assignment AI Solver")
    st.caption("Step-by-Step AI Solutions & Audio Explanations for Students")

    st.markdown("### Upload Assignment PDF")
    assign_pdf = st.file_uploader("Upload Assignment PDF File", type=["pdf"])
    assign_text = st.text_area("Or Paste Assignment Question Directly:")

    a_input = ""
    if assign_pdf:
        a_input = extract_text(assign_pdf)
    elif assign_text:
        a_input = assign_text

    if st.button("💡 Solve & Generate Audio Explanation", type="primary"):
        if not a_input.strip():
            st.warning("Please upload or enter assignment text!")
        else:
            with st.spinner("Gemma is solving assignment..."):
                try:
                    res = solve_assignment(a_input, language)
                    st.session_state["assign_res"] = res

                    asyncio.run(
                        generate_audio(
                            res.get("audio_script", ""),
                            language,
                            "assignment_audio.mp3",
                            single_voice=True,
                            speed=selected_speed,
                        )
                    )
                    st.success("✅ Solution & Audio Generated!")
                except Exception as e:
                    st.error(f"Error: {e}")

    if "assign_res" in st.session_state:
        ares = st.session_state["assign_res"]

        st.markdown("---")
        st.subheader("🔊 Step-by-Step Audio Explanation")
        st.audio("assignment_audio.mp3")

        st.subheader("📖 Written Solution")
        st.write(ares.get("solution_text", ""))