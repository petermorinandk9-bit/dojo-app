import streamlit as st
import requests
import time
from datetime import datetime
from supabase import create_client, Client

# 1. MUST BE THE VERY FIRST ST COMMAND
st.set_page_config(page_title="The Dojo", layout="wide")

# ==================================================
# 1. CLOUD DATABASE CONNECTION
# ==================================================
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_supabase()

# ==================================================
# 2. THE DOJO GATE (LOGIN & SIGN-UP)
# ==================================================
if 'user' not in st.session_state:
    st.markdown("""
        <style>
        .stApp { background-color: #ffffff; }
        .login-header { text-align: center; font-style: italic; font-weight: 800; font-size: 3.5rem; color: #1a1a1a; margin-bottom: 0px; }
        .login-sub { text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 20px; }
        .audio-container-gate { text-align: center; margin: 0 auto 30px auto; padding: 15px; background: #fdfdfd; border: 1px solid #eeeeee; border-radius: 12px; max-width: 400px; }
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown('<p class="login-header">The-Dojo</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-sub">Forge your discipline. Step onto the mat.</p>', unsafe_allow_html=True)

    st.markdown('<div class="audio-container-gate">', unsafe_allow_html=True)
    st.caption("🔊 Entrance Ritual")
    # Reliable Entry Flute
    st.audio("https://res.cloudinary.com/dxfq3iotg/video/upload/v1557233294/info.mp3", format="audio/mp3", loop=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    tab_login, tab_signup = st.tabs(["Login", "Create Account"])

    with tab_login:
        with st.form("login_form"):
            u_name = st.text_input("Username").lower().strip()
            u_pass = st.text_input("Password", type="password")
            if st.form_submit_button("Enter the Dojo", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u_name).eq("password", u_pass).execute()
                if res.data:
                    st.session_state.user = res.data[0]
                    st.success(f"Welcome, {st.session_state.user['display_name']}.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Credentials not recognized.")

    with tab_signup:
        with st.form("signup_form"):
            new_name = st.text_input("Choose Username").lower().strip()
            display_n = st.text_input("Your Name (Display Name)")
            new_pass = st.text_input("Choose Password", type="password")
            invite_c = st.text_input("Dojo Invite Code", type="password")
            if st.form_submit_button("Join the Dojo", use_container_width=True):
                if invite_c == "dojoentry" and new_name and new_pass:
                    user_data = {"username": new_name, "password": new_pass, "display_name": display_n}
                    new_user = supabase.table("users").insert(user_data).execute()
                    if new_user.data:
                        st.session_state.user = new_user.data[0]
                        st.rerun()
    st.stop()

# ==================================================
# 3. IDENTITY & MOOD CONFIG
# ==================================================
USER_ID = st.session_state.user['id']
USER_NAME = st.session_state.user['display_name']
ADMIN_USER = "joseph"

if 'mood' not in st.session_state:
    st.session_state.mood = "neutral"

# Standardizing on reliable SoundHelix tracks that worked before
MOOD_MUSIC = {
    "neutral": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
    "uplifting": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "melancholy": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
    "intense": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3"
}

PHASE_SETS = {
    "Student": ["Welcome Mat", "Warm Up", "Training", "Reflection/Cool Down"],
    "Practitioner": ["Step Onto the Mat", "Warm Up", "Work the Pattern", "Wisdom/Cool Down"],
    "Sentinel": ["Enter the Dojo", "Center", "Engage", "Seal/Reflection"],
    "Sovereign": ["Check-In", "Look Closer", "Name It", "The Wisdom Step"]
}

# ==================================================
# 4. ARCHWAY UI
# ==================================================
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e0e0e0; }
    .active-item { color: #000; font-weight: 800; border-left: 3px solid #000; padding-left: 20px; margin-top: 8px; }
    .inactive-item { color: #bbb; border-left: 1px solid #eee; padding-left: 20px; margin-top: 5px; }
    .sidebar-header { font-size: 0.85em; color: #999; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 25px; }
    .sidebar-dojo { font-size: 2.2rem !important; font-weight: 800; font-style: italic; margin-bottom: -10px; }
    .slogan-stack-refined { font-size: 1.65em; text-align: center; color: #666; font-style: italic; padding-top: 20px; margin-bottom: 0px;}
    .music-wrapper { display: flex; justify-content: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# ==================================================
# 6. SIDEBAR
# ==================================================
with st.sidebar:
    st.markdown('<p class="sidebar-dojo">The-Dojo</p>', unsafe_allow_html=True)
    st.write(f"Warrior: **{USER_NAME}**")
    st.divider()
    
    st.markdown('<p class="sidebar-header">Current Path</p>', unsafe_allow_html=True)
    current_phases = PHASE_SETS.get(st.session_state.get('rank', 'Student'), PHASE_SETS["Student"])
    for idx, p_name in enumerate(current_phases):
        style = 'active-item' if idx == st.session_state.get('phase', 0) else 'inactive-item'
        st.markdown(f"<div class='{style}'>{p_name}</div>", unsafe_allow_html=True)
    
    if st.session_state.user['username'] == ADMIN_USER:
        st.divider()
        st.markdown('<p class="sidebar-header">🥋 Dojo Roster</p>', unsafe_allow_html=True)
        try:
            all_users = supabase.table("users").select("display_name").execute()
            for u in all_users.data: st.caption(f"• {u['display_name']}")
        except: pass

    st.divider()
    if st.button("Logout"):
        del st.session_state.user
        st.rerun()

# ==================================================
# 7. MAIN ENGINE (Music Under Slogan)
# ==================================================
st.markdown('<div class="slogan-stack-refined">We. Never. Quit.</div>', unsafe_allow_html=True)

# THE ATMOSPHERE PLAYER
st.markdown('<div class="music-wrapper">', unsafe_allow_html=True)
st.audio(MOOD_MUSIC[st.session_state.mood], format="audio/mp3", loop=True)
st.markdown('</div>', unsafe_allow_html=True)

if 'msgs' not in st.session_state:
    st.session_state.msgs = []

for msg in st.session_state.msgs:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Speak from center..."):
    st.session_state.msgs.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
    MOOD_PROMPT = "ROLE: Dojo Mentor. At the end of your response, add: [MOOD: neutral/uplifting/melancholy/intense]"
    
    messages = [{"role": "system", "content": MOOD_PROMPT}] + st.session_state.msgs[-10:]
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                        json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.6}, 
                        headers=headers)
    
    full_text = res.json()['choices'][0]['message']['content']
    
    if "[MOOD:" in full_text:
        parts = full_text.split("[MOOD:")
        clean_response = parts[0].strip()
        new_mood = parts[1].replace("]", "").strip().lower()
        if new_mood in MOOD_MUSIC:
            st.session_state.mood = new_mood
    else:
        clean_response = full_text

    with st.chat_message("assistant"): st.markdown(clean_response)
    st.session_state.msgs.append({"role": "assistant", "content": clean_response})
    st.rerun()
