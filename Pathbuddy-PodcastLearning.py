import streamlit as st
import openai
from io import BytesIO
import os
import random
import base64

from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# --- OpenAI ---
openai_key = st.secrets["OPENAI_API_KEY"]
openai.api_key = st.secrets["OPENAI_API_KEY"]
response = openai.ChatCompletion.create(...)  # or other relevant function
llm = ChatOpenAI(temperature=0.7, openai_api_key=openai_key)  # For LangChain

# --- LangChain: Dynamic Topic Suggestion Chain ---
suggest_prompt = PromptTemplate(
    input_variables=["topics"],
    template="""
You are an education-focused AI. Given the following list of topics the user is interested in:

{topics}

Suggest 6 additional unique and diverse but *related* educational podcast topics. Avoid repeating any of the original ones. Make them engaging and specific.
Only return a list of topic titles, no explanations.
"""
)
suggest_chain = LLMChain(llm=llm, prompt=suggest_prompt)

# --- Default Suggestions Fallback ---
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

# --- Suggestion Update Using LangChain ---
def update_suggestions():
    current = st.session_state["questions"]
    if current:
        input_str = ", ".join(current)
        raw_output = suggest_chain.run({"topics": input_str})
        suggestions = [s.strip("-• ").strip() for s in raw_output.split("\n") if s.strip()]
        suggestions = [s for s in suggestions if s not in current]
        st.session_state["suggestions"] = suggestions[:6] if suggestions else random.sample(default_suggestions, 6)
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
        if len(st.session_state["questions"]) < 6 and topic not in st.session_state["questions"]:
            st.session_state["questions"].append(topic)
            update_suggestions()

# --- Input Fields ---
new_questions = []
for i in range(6):
    val = st.text_input(f"Topic {i+1}", st.session_state["questions"][i] if i < len(st.session_state["questions"]) else "")
    if val.strip():
        new_questions.append(val.strip())

st.session_state["questions"] = new_questions

# --- Podcast Script Generator ---
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
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=1500
    )
    return response.choices[0].message.content

# --- Audio Generator ---
def generate_audio(script_text, voice="nova", speed=1.0):
    audio_response = openai.Audio.speech.create(
        model="tts-1",
        voice=voice,
        input=script_text,
        speed=speed
    )
    return BytesIO(audio_response.content)

# --- Cover Image Generator ---
def generate_image(topics):
    prompt = f"A square podcast cover representing the topic: {topics[0]}. Modern, colorful, education-themed, minimal design."
    image = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1024x1024",
         response_format="url",
            )
    return image["data"][0]["url"]

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
