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
    "Neural Networks", "String Theory", "SpaceX Rockets", "Nutrition Science",
    "Ancient Civilizations", "Economics of AI", "Electric Vehicles", "Mars Colonization"
]

# --- Session State ---
if "questions" not in st.session_state:
    st.session_state["questions"] = []

if "suggestions" not in st.session_state:
    st.session_state["suggestions"] = random.sample(default_suggestions, 6)

# --- User Interest Mapping ---
interest_tags = {
    "tech": ["AI", "Machine Learning", "Neural", "Computing", "Internet", "Blockchain"],
    "science": ["Quantum", "Physics", "Chemistry", "Biology", "Nutrition", "Climate"],
    "history": ["History", "Revolution", "War", "Ancient"],
    "space": ["Space", "NASA", "Rockets", "Astronomy", "Mars"],
    "economics": ["Inflation", "Economics", "Finance", "Money"],
}

# --- Detect Interests from Questions ---
def get_user_interests(questions):
    tags = set()
    for q in questions:
        for tag, keywords in interest_tags.items():
            if any(k.lower() in q.lower() for k in keywords):
                tags.add(tag)
    return tags

# --- Personalized Suggestion Update ---
def update_suggestions():
    tags = get_user_interests(st.session_state["questions"])
    if tags:
        related = [s for s in default_suggestions if any(t in s for tag in tags for t in interest_tags[tag])]
        st.session_state["suggestions"] = random.sample(set(related), min(6, len(related)))
    else:
        st.session_state["suggestions"] = random.sample(default_suggestions, 6)

# --- Streamlit UI Setup ---
st.set_page_config(page_title="AI Podcast Builder", layout="centered")
st.title("🎙️ AI-Powered Learning Podcasts")
st.markdown("Enter up to 6 topics you're curious about. We'll generate a short podcast per topic with two engaging hosts (Alex and Sam).")

# --- Duration Selection ---
duration_map = {
    "60 seconds": 120,
    "2 minutes": 300,
    "5 minutes": 700
}
duration_choice = st.selectbox("🕒 Select podcast length:", list(duration_map.keys()))
max_tokens = duration_map[duration_choice]

# --- Suggestion Bubbles ---
st.markdown("💡 **Topic Suggestions:**")
cols = st.columns(6)
for i, topic in enumerate(st.session_state["suggestions"]):
    if cols[i].button(topic):
        if len(st.session_state["questions"]) < 6:
            st.session_state["questions"].append(topic)
            update_suggestions()

# --- Input Fields ---
new_questions = []
for i in range(6):
    val = st.text_input(f"Topic {i+1}", st.session_state["questions"][i] if i < len(st.session_state["questions"]) else "")
    if val.strip():
        new_questions.append(val.strip())

st.session_state["questions"] = new_questions

# --- Script Generator ---
def generate_script(topic, max_tokens=300):
    prompt = f"""
You're writing a podcast between two hosts: Alex and Sam.

Topic: "{topic}"

Make it:
- Friendly and educational
- Around {max_tokens} words
- Conversational, with back-and-forth dialogue
- Use analogies, humor, and simple explanations
- No monologues

Begin the script:
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=1500
    )
    return response.choices[0].message.content

# --- Audio Generator ---
def generate_audio(script_text, voice="nova", speed=1.0):
    audio_response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=script_text,
        speed=speed
    )
    return BytesIO(audio_response.content)

# --- Cover Image Generator ---
def generate_image(topics):
    prompt = f"A square podcast cover representing the topic: {topics[0]}. Modern, colorful, education-themed, minimal design."
    image = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )
    return image.data[0].url

# --- Audio Player + Cover Image ---
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

# --- Main Button ---
if st.button("🎧 Generate Podcasts"):
    if not new_questions:
        st.warning("Please enter at least one topic.")
    else:
        update_suggestions()

        for topic in new_questions:
            st.subheader(f"🎙️ Podcast: {topic}")

            with st.spinner("Generating script..."):
                script = generate_script(topic, max_tokens=max_tokens)
                st.text_area("📜 Script", script, height=250)

            with st.spinner("Generating cover image..."):
                img_url = generate_image([topic])

            with st.spinner("Generating audio..."):
                audio = generate_audio(script)

            audio_player_basic(audio, img_url)
            st.divider()
