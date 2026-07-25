import asyncio
import json
import os
import edge_tts
import ollama
from pypdf import PdfReader
import streamlit as st

# Page Config
st.set_page_config(
    page_title="Syllabify AI - Podcast Studio", page_icon="🎙️", layout="wide"
)

st.title("🎙️ Syllabify AI: Educational Podcast Studio")
st.write(
    "Visually Impaired & Dyslexic Students ke liye AI-Powered Learning App"
)


# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text[:2500]


# Gemma Script Generator
def generate_podcast_script(text_content):
    prompt = f"""
    You are an expert educational podcast scriptwriter for visually impaired students.
    Convert the following textbook content into a 2-person dialogue script between "Tutor" and "Student".

    Rules:
    1. Keep it simple, engaging, and conversational.
    2. Tutor explains concepts using relatable real-world analogies.
    3. Student asks curious, natural follow-up questions.
    4. Output MUST strictly be a JSON array of objects with keys "speaker" and "text".
    5. Do NOT add any markdown fences, intro, or extra text outside JSON.

    Format Example:
    [
      {{"speaker": "Tutor", "text": "Welcome! Today we are learning about how gravity works."}},
      {{"speaker": "Student", "text": "Is gravity what keeps our feet on the ground?"}},
      {{"speaker": "Tutor", "text": "Exactly! It acts like an invisible pulling force..."}}
    ]

    Content:
    {text_content}
    """

    response = ollama.chat(
        model="gemma:2b",
        messages=[{"role": "user", "content": prompt}],
    )

    content = response["message"]["content"].strip()

    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:].strip()

    return json.loads(content)


# Dual Voice Generator
async def generate_audio(script, output_filename="podcast.mp3"):
    TUTOR_VOICE = "en-US-GuyNeural"
    STUDENT_VOICE = "en-US-AnaNeural"

    os.makedirs("temp_chunks", exist_ok=True)
    audio_bytes = []

    for idx, line in enumerate(script):
        speaker = line.get("speaker", "Tutor")
        text = line.get("text", "")
        voice = TUTOR_VOICE if speaker.lower() == "tutor" else STUDENT_VOICE

        chunk_path = f"temp_chunks/chunk_{idx}.mp3"
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(chunk_path)

        with open(chunk_path, "rb") as f:
            audio_bytes.append(f.read())

    with open(output_filename, "wb") as f:
        for chunk in audio_bytes:
            f.write(chunk)


# UI Layout
uploaded_pdf = st.file_uploader("PDF File Upload Karein", type=["pdf"])
text_input = st.text_area("Ya Direct Text Paste Karein:", height=150)

final_text = ""
if uploaded_pdf:
    final_text = extract_text_from_pdf(uploaded_pdf)
    st.success("PDF Read Ho Gaya!")
elif text_input:
    final_text = text_input

if st.button("🚀 Generate Podcast"):
    if not final_text.strip():
        st.warning("Pehle PDF upload karein ya text likhein!")
    else:
        with st.spinner("Gemma Script Bana Raha Hai..."):
            try:
                script = generate_podcast_script(final_text)

                st.subheader("📜 Generated Script")
                for line in script:
                    speaker = line.get("speaker", "Tutor")
                    text = line.get("text", "")
                    if speaker.lower() == "tutor":
                        st.markdown(f"👨‍🏫 **Tutor:** {text}")
                    else:
                        st.markdown(f"🧑‍🎓 **Student:** {text}")

                with st.spinner("Audio Banti Ho..."):
                    asyncio.run(generate_audio(script, "final_podcast.mp3"))

                st.success("🎉 Podcast Ready!")
                st.audio("final_podcast.mp3", format="audio/mp3")

            except Exception as e:
                st.error(f"Error Aaya: {e}")