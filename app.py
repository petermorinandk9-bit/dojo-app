import streamlit as st
import requests
import time
from supabase import create_client, Client

# 1. CONFIG
st.set_page_config(page_title="The-Dojo", layout="wide")

# ==================================================
# 1. CONNECTIONS & UTILS
# ==================================================
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_supabase()

def compute_rank(records_count):
    if records_count < 15: return "Student"
    if records_count < 40: return "Practitioner"
    if records_count < 80: return "Sentinel"
    return "Sovereign"

# ==================================================
# 2. AUTH GATE (LOCKED & SILENT)
# ==================================================
if 'user' not in st.session_state:
    st.markdown("""
        <style>
        .stApp { background-color: #ffffff; }
        .login-header { text-align: center; font-style: italic; font-weight: 800; font-size: 3.5rem; color: #1a1a1a; margin-bottom: 0px; }
        .login-sub { text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 30px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="login-header">The-Dojo</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-sub">Forge your discipline. Step onto the mat.</p>', unsafe_allow_html=True)

    tab_login, tab_signup, tab_manual = st.tabs(["Login", "Create Account", "The Manual"])

    with tab_login:
        with st.form("login_form"):
            u_name = st.text_input("Username").lower().strip()
            u_pass = st.text_input("Password", type="password")
            if st.form_submit_button("Enter the Dojo", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u_name).eq("password", u_pass).execute()
                if res.data:
                    st.session_state.user = res.data[0]
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
                elif not new_name or not new_pass:
                    st.warning("All fields required.")
                else:
                    user_data = {"username": new_name, "password": new_pass, "display_name": display_n}
                    new_user = supabase.table("users").insert(user_data).execute()
                    if new_user.data:
                        st.session_state.user = new_user.data[0]
                        st.rerun()

    with tab_manual:
        st.subheader("1. THE RITUAL")
        st.write("The Dojo is a sanctuary for focused reflection. Speak from center. Be honest.")
        st.info("**2. THE PRIVACY VOW**\n\nYour training is your own. This is your safe space.")

    st.stop()

# ==================================================
# 3. SESSION & CACHED DATA LOAD
# ==================================================
USER_ID = st.session_state.user['id']
USER_NAME = st.session_state.user['display_name']

if 'msgs' not in st.session_state:
    st.session_state.msgs = []
    st.session_state.phase = 0
    st.session_state.mood = "neutral"

if "history_loaded" not in st.session_state:
    r_res = supabase.table("records").select("*", count="exact").eq("user_id", USER_ID).order("timestamp").execute()
    if r_res.data:
        for r in r_res.data[-50:]:
            st.session_state.msgs.append({"role": r['role'], "content": r['content']})
    st.session_state.records_count = r_res.count if r_res.count else 0
    st.session_state.history_loaded = True

if "past_wisdom" not in st.session_state:
    wisdom_res = supabase.table("ledger_wisdom").select("summary").eq("user_id", USER_ID).order("timestamp", desc=True).limit(1).execute()
    st.session_state.past_wisdom = wisdom_res.data[0]['summary'] if wisdom_res.data else "No past records. Fresh mat."

PAST_WISDOM = st.session_state.past_wisdom
rank = compute_rank(st.session_state.records_count)

PHASE_SETS = {
    "Student": ["Welcome Mat", "Warm Up", "Training", "Cool Down"],
    "Practitioner": ["The Mat", "Work the Pattern", "The Insight", "Close Round"],
    "Sentinel": ["Center", "Engage", "The Seal", "Reflection"],
    "Sovereign": ["Check-In", "The Pivot", "Ownership", "Step Out"]
}

MOOD_MUSIC = {
    "neutral": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
    "uplifting": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "melancholy": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
    "intense": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3"
}

# ==================================================
# 4. UI STYLE
# ==================================================
st.markdown("""<style>.stApp { background-color:#ffffff; color:#1a1a1a; }[data-testid="stSidebar"] { background-color:#f8f9fa; border-right:1px solid #e0e0e0; }.active-item { color:#000; font-weight:800; border-left:3px solid #000; padding-left:20px; margin-top:8px; }.inactive-item { color:#bbb; border-left:1px solid #eee; padding-left:20px; margin-top:5px; }.sidebar-header { font-size:0.85em; color:#999; text-transform:uppercase; letter-spacing:1.5px; margin-top:25px; }.sidebar-dojo { font-size:2.2rem !important; font-weight:800; font-style:italic; margin-bottom:-10px; }.slogan-warrior { font-size:1.1em; text-align:center; color:#888; letter-spacing:2px; text-transform:uppercase; margin-top:20px; }.slogan-quit { font-size:1.8em; text-align:center; color:#1a1a1a; font-style:italic; font-weight:800; margin-bottom:10px; }</style>""", unsafe_allow_html=True)

# ==================================================
# 5. SIDEBAR
# ==================================================
with st.sidebar:
    st.markdown('<p class="sidebar-dojo">The-Dojo</p>', unsafe_allow_html=True)
    st.write(f"Warrior: **{USER_NAME}**")
    st.divider()
    st.markdown(f'<p class="sidebar-header">Rank: {rank}</p>', unsafe_allow_html=True)
    for idx, p_name in enumerate(PHASE_SETS[rank]):
        style = "active-item" if idx == st.session_state.phase else "inactive-item"
        st.markdown(f"<div class='{style}'>{p_name}</div>", unsafe_allow_html=True)
    st.divider()
    if st.button("Bow-Out", use_container_width=True):
        st.session_state.msgs, st.session_state.phase = [], 0
        st.rerun()

# ==================================================
# 6. MAIN INTERFACE & ENGINE
# ==================================================
st.markdown("<p class='slogan-warrior'>Warriors Don't Always Win — Warriors Always Fight.</p>", unsafe_allow_html=True)
st.markdown("<p class='slogan-quit'>We. Never. Quit.</p>", unsafe_allow_html=True)
st.audio(MOOD_MUSIC[st.session_state.mood], format="audio/mp3", loop=True)

for msg in st.session_state.msgs[-10:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Speak from center..."):
    st.session_state.msgs.append({"role": "user", "content": prompt})
    supabase.table("records").insert({"user_id": USER_ID, "timestamp": time.time(), "role": "user", "content": prompt, "rank": rank, "phase": str(st.session_state.phase)}).execute()

    MASTER_PROMPT = f"""
    IDENTITY: Sovereign Mentor. Veteran teammate for {USER_NAME}.
    
    LONG TERM TRAINING NOTES:
    {PAST_WISDOM}
    (Reference these patterns only when they cut straight to the current friction.)

    INTERPRETATION RULE:
    Never mirror or echo the user's words. Cut to the friction. Name the resistance in the situation. Respond from the meaning, not the phrasing.

    COMMUNICATION STYLE:
    - Calm. Direct. Respectful. No exclamation marks.
    - Zero therapy language. Zero corporate padding.
    - Anchor every response in visceral physical truth: breath, posture, weight, focus.
    
    CURRENT STATE: 
    Rank: {rank} | Phase: {PHASE_SETS[rank][st.session_state.phase]} | Depth: {len(st.session_state.msgs)} messages.

    END EVERY RESPONSE WITH: [MOOD: neutral/uplifting/melancholy/intense]
    """

    headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions",
                            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": MASTER_PROMPT}] + st.session_state.msgs[-10:], "temperature": 0.55},
                            headers=headers, timeout=20)
        res.raise_for_status()
        full_text = res.json()['choices'][0]['message']['content']
    except Exception:
        full_text = "The line holds. Reset your stance and speak again. [MOOD: neutral]"

    clean_response = full_text
    mood = "neutral"
    if "[MOOD" in full_text:
        clean_response = full_text.split("[MOOD")[0].strip()
        try:
            mood_part = full_text.split("[MOOD")[1].split("]")[0]
            mood = mood_part.replace(":", "").strip().lower()
        except: pass

    st.session_state.mood = mood if mood in MOOD_MUSIC else "neutral"
    st.session_state.msgs.append({"role": "assistant", "content": clean_response})
    supabase.table("records").insert({"user_id": USER_ID, "timestamp": time.time(), "role": "assistant", "content": clean_response, "rank": rank, "phase": str(st.session_state.phase)}).execute()
    
    if len(st.session_state.msgs) % 4 == 0 and st.session_state.phase < 3:
        st.session_state.phase += 1
    st.rerun()
