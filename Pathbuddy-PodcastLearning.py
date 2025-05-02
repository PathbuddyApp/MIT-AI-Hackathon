import streamlit as st
from openai import OpenAI
from io import BytesIO
import os

# Load API key
client = OpenAI(api_key="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")
# client = os.getenv("OPENAI_API_KEY") or "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"  # or hardcode for testing

st.set_page_config(page_title="AI Podcast Learning", layout="centered")
st.title("🎙️ Learn with AI Podcasts")

st.markdown("Enter up to 6 questions or topics you'd like to learn about. We'll generate a podcast-style conversation that teaches you about them.")

# --- Suggestions ---
suggestions = [
    "Quantum Computing", "What is Inflation?", "Basics of Machine Learning",
    "History of the Internet", "Climate Change", "How Blockchain Works"
]

st.markdown("💡 **Suggested Topics:**")
cols = st.columns(len(suggestions))
for i, topic in enumerate(suggestions):
    if cols[i].button(topic):
        st.session_state.setdefault("questions", []).append(topic)

# --- Input Fields ---
questions = st.session_state.get("questions", [])
new_questions = []

for i in range(6):
    default = questions[i] if i < len(questions) else ""
    q = st.text_input(f"Topic or Question {i+1}", default)
    if q.strip():
        new_questions.append(q.strip())

st.session_state["questions"] = new_questions

# --- Script Generation ---
def generate_script(questions):
    prompt = f"""
You're writing a short, friendly podcast script with two hosts (Alex and Sam). The tone should be playful, educational, and casual.

The podcast should cover these user questions or topics:
{', '.join(questions)}

Write a script (800-1000 words) where:
- Alex and Sam take turns talking
- They explain the topics in easy-to-understand language
- Use examples, analogies, jokes if helpful
- Avoid too much fluff — keep it informative but fun

Begin the script:
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )
    return response.choices[0].message.content

# --- TTS Audio Generation ---
def generate_audio(script_text, voice="nova", speed=1.0):
    audio_response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=script_text,
        speed=speed
    )
    return BytesIO(audio_response.content)

# --- Generate Button ---
if st.button("🎧 Generate Podcast"):
    if not new_questions:
        st.warning("Please enter at least one topic.")
    else:
        with st.spinner("Generating podcast script..."):
            script = generate_script(new_questions)
            st.text_area("🎙️ Podcast Script", script, height=300)

        with st.spinner("Generating podcast audio..."):
            audio = generate_audio(script)
            st.audio(audio, format="audio/mp3")
            st.success("Your podcast is ready!")
