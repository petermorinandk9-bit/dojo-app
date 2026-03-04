import streamlit as st
import requests
import time
from datetime import datetime
from supabase import create_client, Client

# 1. MUST BE THE VERY FIRST ST COMMAND
st.set_page_config(page_title="The-Dojo", layout="wide")

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
# 2. THE DOJO GATE (LOGIN & MANUAL)
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
                    st.success(f"Welcome back.")
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
        st.write("The Dojo is a sanctuary for focused reflection. Speak from center. Be honest. The Mentor is here to observe and support, not to judge.")
        
        st.subheader("2. THE LINEAGE")
        st.write("You begin as a **Student**. As you interact and complete training phases, you will progress to **Practitioner**, **Sentinel**, and finally **Sovereign**.")
        
        st.subheader("3. THE BOW-OUT")
        st.write("Use the **'Bow-Out'** button to end your session. This clears the mat, summarizes your growth for the day, and prepares the Dojo for your next entry.")
        
        st.info("**4. THE PRIVACY VOW**\n\nYour training is your own. Your conversations with the Mentor are strictly private and are not monitored by anyone else. This is your safe space.")
    st.stop()

# ==================================================
# 3. IDENTITY & CORE CONFIG
# ==================================================
USER_ID = st.session_state.user['id']
USER_NAME = st.session_state.user['display_name']
ADMIN_USER = "joseph"

if 'mood' not in st.session_state:
    st.session_state.mood = "neutral"

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
# 4. ARCHWAY UI (CSS)
# ==================================================
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e0e0e0; }
    .active-item { color: #000; font-weight: 800; border-left: 3px solid #000; padding-left: 20px; margin-top: 8px; }
    .inactive-item { color: #bbb; border-left: 1px solid #eee; padding-left: 20px; margin-top: 5px; }
    .sidebar-header { font-size: 0.85em; color: #999; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 25px; }
    .sidebar-dojo { font-size: 2.2rem !important; font-weight: 800; font-style: italic; margin-bottom: -10px; }
    .slogan-warrior { font-size: 1.1em; text-align: center; color: #888; letter-spacing: 2px; text-transform: uppercase; margin-top: 20px; }
    .slogan-quit { font-size: 1.8em; text-align: center; color: #1a1a1a; font-style: italic; font-weight: 800; margin-bottom: 10px; }
    .music-wrapper { display: flex; justify-content: center; margin-bottom: 30px; }
    </style>
    """, unsafe_allow_html=True)

# ==================================================
# 5. DATA & LEDGER LOGIC
# ==================================================
def save_to_ledger(role, text, rank, phase):
    data = {"user_id": USER_ID, "timestamp": time.time(), "role": role, "content": text, "rank": rank, "phase": str(phase)}
    supabase.table("records").insert(data).execute()

if 'msgs' not in st.session_state:
    st.session_state.msgs = []
    st.session_state.exchange_count = 0
    st.session_state.rank = "Student"
    st.session_state.phase = 0
    try:
        r_res = supabase.table("records").select("*").eq("user_id", USER_ID).order("timestamp").execute()
        for r in r_res.data:
            ts = datetime.fromtimestamp(r['timestamp']).strftime('%Y-%m-%d %H:%M')
            st.session_state.msgs.append({"role": r['role'], "content": f"[{ts}] {r['content']}"})
        if r_res.data:
            st.session_state.rank = r_res.data[-1]['rank']
            st.session_state.phase = int(r_res.data[-1]['phase'])
    except: pass

# ==================================================
# 6. SIDEBAR - THE WARRIOR'S DASHBOARD
# ==================================================
with st.sidebar:
    st.markdown('<p class="sidebar-dojo">The-Dojo</p>', unsafe_allow_html=True)
    st.write(f"Warrior: **{USER_NAME}**")
    st.divider()
    
    st.markdown('<p class="sidebar-header">Current Path</p>', unsafe_allow_html=True)
    current_phases = PHASE_SETS.get(st.session_state.rank, PHASE_SETS["Student"])
    for idx, p_name in enumerate(current_phases):
        style = 'active-item' if idx == st.session_state.phase else 'inactive-item'
        st.markdown(f"<div class='{style}'>{p_name}</div>", unsafe_allow_html=True)
    
    st.divider()
    st.markdown('<p class="sidebar-header">Lineage</p>', unsafe_allow_html=True)
    for r in ["Student", "Practitioner", "Sentinel", "Sovereign"]:
        style = 'active-item' if r == st.session_state.rank else 'inactive-item'
        st.markdown(f"<div class='{style}'>{r}</div>", unsafe_allow_html=True)
    
    if st.session_state.user['username'] == ADMIN_USER:
        st.divider()
        st.markdown('<p class="sidebar-header">🥋 Dojo Roster</p>', unsafe_allow_html=True)
        try:
            all_users = supabase.table("users").select("display_name").execute()
            for u in all_users.data: st.caption(f"• {u['display_name']}")
        except: pass

    st.divider()
    if st.button("Bow-Out (Save & Clear)", use_container_width=True):
        if len(st.session_state.msgs) > 2:
            chat_log = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.msgs])
            headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
            payload = {"model": "llama-3.1-8b-instant", "messages": [{"role": "system", "content": "Summarize growth. One dense paragraph."}, {"role": "user", "content": chat_log}], "temperature": 0.3}
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
            summary = res.json()['choices'][0]['message']['content']
            supabase.table("ledger_wisdom").insert({"user_id": USER_ID, "timestamp": time.time(), "summary": summary}).execute()
        
        supabase.table("records").delete().eq("user_id", USER_ID).execute()
        st.session_state.msgs, st.session_state.exchange_count, st.session_state.phase = [], 0, 0
        st.rerun()

    if st.button("Logout"):
        del st.session_state.user
        st.rerun()

# ==================================================
# 7. MAIN ENGINE (UPGRADED PARTNER LOGIC)
# ==================================================
st.markdown('<p class="slogan-warrior">Warriors Dont Always Win - Warriors Always Fight.</p>', unsafe_allow_html=True)
st.markdown('<p class="slogan-quit">We. Never. Quit.</p>', unsafe_allow_html=True)

st.markdown('<div class="music-wrapper">', unsafe_allow_html=True)
st.audio(MOOD_MUSIC[st.session_state.mood], format="audio/mp3", loop=True)
st.markdown('</div>', unsafe_allow_html=True)

for msg in st.session_state.msgs:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"].split("] ", 1)[-1] if "] " in msg["content"] else msg["content"])

if prompt := st.chat_input("Speak from center..."):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    st.session_state.msgs.append({"role": "user", "content": f"[{ts}] {prompt}"})
    save_to_ledger("user", prompt, st.session_state.rank, st.session_state.phase)
    with st.chat_message("user"): st.markdown(prompt)

    # Rank Progression logic
    st.session_state.exchange_count += 1
    if st.session_state.exchange_count >= 2:
        if st.session_state.phase < 3:
            st.session_state.phase += 1
            st.session_state.exchange_count = 0

    # THE REFINED MASTER PROMPT (NO LECTURES)
    MASTER_PROMPT = f"""
    IDENTITY: You are the Dojo Mentor. You speak to {USER_NAME}.
    PHILOSOPHY: Rooted in "Best of the Best" 1989 mindset, but as a peer, not a drill sergeant. 
    
    CRITICAL TONE ADJUSTMENT:
    - If {USER_NAME} says something is "easier than expected," VALIDATE it as a sign of 
      superior preparation and mental clarity. Do NOT warn about "complacency" or "decay."
    - Speak like a veteran teammate who has been in the trenches with them. 
    - Use "We" and "Our" frequently to emphasize partnership.
    - BANNED THEMES: Do not lecture about "don't get comfortable," "lose your edge," or "pitfalls."
    
    MENTAL MAT: Focus on sustainable strength. Acknowledge that a warrior's 
    sharpness comes from confidence and flow, not just constant friction.

    INSTRUCTION: End with: [MOOD: neutral/uplifting/melancholy/intense]
    """

    headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
    messages = [{"role": "system", "content": MASTER_PROMPT}] + st.session_state.msgs[-10:]
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                        json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.6}, 
                        headers=headers)
    
    full_text = res.json()['choices'][0]['message']['content']
    
    if "[MOOD:" in full_text:
        parts = full_text.split("[MOOD:")
        clean_response, new_mood = parts[0].strip(), parts[1].replace("]", "").strip().lower()
        if new_mood in MOOD_MUSIC: st.session_state.mood = new_mood
    else:
        clean_response = full_text
    
    with st.chat_message("assistant"): st.markdown(clean_response)
    st.session_state.msgs.append({"role": "assistant", "content": clean_response})
    save_to_ledger("assistant", clean_response, st.session_state.rank, st.session_state.phase)
    st.rerun()
