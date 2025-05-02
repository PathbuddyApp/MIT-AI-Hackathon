import streamlit as st
from openai import OpenAI
from io import BytesIO
import os
import random
import base64

# --- OpenAI Client ---
client = OpenAI(api_key="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")


# --- Default Suggestions ---
default_suggestions = [
    "Quantum Computing", "What is Inflation?", "Basics of Machine Learning",
    "History of the Internet", "Climate Change", "How Blockchain Works",
    "Neural Networks", "String Theory", "SpaceX Rockets", "Nutrition Science"
]

# --- Session State Setup ---
if "questions" not in st.session_state:
    st.session_state["questions"] = []

if "suggestions" not in st.session_state:
    st.session_state["suggestions"] = random.sample(default_suggestions, 6)

# --- Streamlit UI ---
st.set_page_config(page_title="AI Podcast Learning", layout="centered")
st.title("🎙️ Learn with AI Podcasts")
st.markdown("Enter up to 6 questions or topics you'd like to learn about. We'll generate a podcast-style conversation with hosts Alex and Sam that teaches you.")

# --- Suggestion Buttons ---
st.markdown("💡 **Click a suggestion to add it to your list:**")
cols = st.columns(6)
for i, topic in enumerate(st.session_state["suggestions"]):
    if cols[i].button(topic):
        if len(st.session_state["questions"]) < 6:
            st.session_state["questions"].append(topic)
            # Replace this suggestion with a new random one
            remaining = list(set(default_suggestions) - set(st.session_state["suggestions"]))
            if remaining:
                new_topic = random.choice(remaining)
                st.session_state["suggestions"][i] = new_topic

# --- User Input Fields ---
new_questions = []
for i in range(6):
    q = st.text_input(f"Topic or Question {i+1}", st.session_state["questions"][i] if i < len(st.session_state["questions"]) else "")
    if q.strip():
        new_questions.append(q.strip())

st.session_state["questions"] = new_questions

# --- Generate Podcast Script ---
def generate_script(questions):
    prompt = f"""
You're writing a podcast script between two hosts (Alex and Sam). The tone is fun, friendly, and educational.

The podcast should cover these user questions or topics:
{', '.join(questions)}

Write a script (800-1000 words) where:
- Alex and Sam take turns speaking.
- They explain in easy, clear language.
- Use analogies, humor, and examples.
- Avoid long monologues — make it dynamic and engaging.

Begin the script:
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )
    return response.choices[0].message.content

# --- Generate Audio ---
def generate_audio(script_text, voice="nova", speed=1.0):
    audio_response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=script_text,
        speed=speed
    )
    return BytesIO(audio_response.content)

# --- Generate Podcast Cover Image ---
def generate_image(topics):
    prompt = f"A podcast album cover representing the topics: {', '.join(topics)}. Modern, colorful, abstract, educational-themed. Square layout."
    image = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )
    return image.data[0].url

def audio_player_basic(audio_bytes, cover_url):
    audio_base64 = base64.b64encode(audio_bytes.getvalue()).decode()

    audio_html = f"""
    <div style="display: flex; flex-direction: column; align-items: center;">
        <img src="{cover_url}" width="300" style="border-radius: 16px; margin-bottom: 16px;" />
        <audio controls style="width: 300px;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
    </div>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# --- Main Generate Button ---
if st.button("🎧 Generate Podcast"):
    if not new_questions:
        st.warning("Please enter at least one topic.")
    else:
        with st.spinner("Generating podcast script..."):
            script = generate_script(new_questions)
            st.text_area("📜 Podcast Script", script, height=300)

        with st.spinner("Creating podcast cover..."):
            img_url = generate_image(new_questions)

        with st.spinner("Synthesizing audio..."):
            audio = generate_audio(script)

        st.success("✅ Podcast is ready!")
        audio_player_basic(audio, img_url)
