```python
import streamlit as st
from elevenlabs.client import ElevenLabs

# ==================================================
# CONFIG
# ==================================================

st.set_page_config(page_title="Dojo Voice Test", layout="centered")

VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel (free tier voice)

client = ElevenLabs(
    api_key=st.secrets["ELEVEN_API_KEY"]
)

# ==================================================
# SESSION STATE
# ==================================================

if "voice_mode" not in st.session_state:
    st.session_state.voice_mode = False

# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.title("Voice Settings")

    st.session_state.voice_mode = st.checkbox(
        "Voice Mode (auto speak mentor)",
        value=st.session_state.voice_mode
    )

# ==================================================
# VOICE FUNCTION
# ==================================================

def generate_voice(text):

    audio_stream = client.text_to_speech.convert(
        text=text,
        voice_id=VOICE_ID,
        model_id="eleven_multilingual_v2"
    )

    audio_bytes = b"".join(audio_stream)

    return audio_bytes

# ==================================================
# MAIN UI
# ==================================================

st.title("Dojo Voice Test")

text = st.text_area(
    "Enter text for the mentor to speak:",
    "Welcome back to the dojo. Step onto the mat."
)

if st.button("Generate Mentor Response"):

    st.markdown("### Mentor")

    st.write(text)

    # Listen button
    if st.button("▶ Listen"):

        audio = generate_voice(text)
        st.audio(audio)

    # Auto voice mode
    if st.session_state.voice_mode:

        audio = generate_voice(text)
        st.audio(audio)
```
