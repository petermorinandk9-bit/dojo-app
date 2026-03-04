import streamlit as st
import requests
import time
from datetime import datetime
from supabase import create_client, Client

# MUST BE THE FIRST ST COMMAND
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
# 2. THE DOJO GATE (LOGIN & SIGN-UP) - WITH SOUND
# ==================================================
if 'user' not in st.session_state:
    # Removed set_page_config from here
    st.markdown("""
        <style>
        .stApp { background-color: #ffffff; }
        .login-header { text-align: center; font-style: italic; font-weight: 800; font-size: 3.5rem; color: #1a1a1a; margin-bottom: 0px; }
        .login-sub { text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 20px; }
        .audio-container { 
            text-align: center; 
            margin: 0 auto 30px auto; 
            padding: 15px; 
            background: #fdfdfd; 
            border: 1px solid #eeeeee;
            border-radius: 12px;
            max-width: 400px;
        }
        .audio-label { font-size: 0.85em; color: #888; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; }
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown('<p class="login-header">The-Dojo</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-sub">Forge your discipline. Step onto the mat.</p>', unsafe_allow_html=True)

    st.markdown('<div class="audio-container">', unsafe_allow_html=True)
    st.markdown('<p class="audio-label">🔊 Establish Presence</p>', unsafe_allow_html=True)
    audio_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"
    st.audio(audio_url, format="audio/mp3", loop=True)
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
                if invite_c != "dojoentry":
                    st.error("Invalid Invite Code.")
                elif not new_name or not new_pass or not display_n:
                    st.warning("All fields required.")
                else:
                    check = supabase.table("users").select("id").eq("username", new_name).execute()
                    if check.data:
                        st.error("Username taken.")
                    else:
                        user_data = {"username": new_name, "password": new_pass, "display_name": display_n}
                        new_user = supabase.table("users").insert(user_data).execute()
                        if new_user.data:
                            st.session_state.user = new_user.data[0]
                            st.success("Account created. Welcome to the lineage.")
                            time.sleep(1)
                            st.rerun()
    st.stop()

# ==================================================
# 3. IDENTITY & CORE CONFIG
# ==================================================
USER_ID = st.session_state.user['id']
USER_NAME = st.session_state.user['display_name']

PHASE_SETS = {
    "Student": ["Welcome Mat", "Warm Up", "Training", "Reflection/Cool Down"],
    "Practitioner": ["Step Onto the Mat", "Warm Up", "Work the Pattern", "Wisdom/Cool Down"],
    "Sentinel": ["Enter the Dojo", "Center", "Engage", "Seal/Reflection"],
    "Sovereign": ["Check-In", "Look Closer", "Name It", "The Wisdom Step"]
}

# ==================================================
# 4. ARCHWAY UI (INTEGRATED LINEAGE STYLE)
# ==================================================
# REMOVED SECOND st.set_page_config FROM HERE
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e0e0e0; }
    
    .active-item { 
        color: #000000; font-weight: 800; font-size: 1.15em; 
        border-left: 3px solid #000; padding-left: 20px; margin-top: 8px; 
    }
    .inactive-item { 
        color: #bbbbbb; font-weight: 400; font-size: 0.95em; 
        border-left: 1px solid #eeeeee; padding-left: 20px; margin-top: 5px; 
    }
    .sidebar-header { font-size: 0.85em; color: #999; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 25px; margin-bottom: 10px; }
    .sidebar-dojo { font-size: 2.2rem !important; font-weight: 800; color: #1a1a1a; font-style: italic; margin-bottom: -10px; }
    .slogan-stack-refined { font-size: 1.65em; text-align: center; color: #666666; font-style: italic; padding-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# ... (Rest of sections 5, 6, and 7 remain exactly as you had them)
