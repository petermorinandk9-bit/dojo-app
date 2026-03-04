import streamlit as st
import requests
import time
from datetime import datetime
from supabase import create_client, Client

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
    st.set_page_config(page_title="The Dojo - Entry", layout="centered")
    st.markdown("""
        <style>
        .stApp { background-color: #ffffff; }
        .login-header { text-align: center; font-style: italic; font-weight: 800; font-size: 3.5rem; color: #1a1a1a; margin-bottom: 0px; }
        .login-sub { text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 30px; }
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown('<p class="login-header">The-Dojo</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-sub">Forge your discipline. Step onto the mat.</p>', unsafe_allow_html=True)
    
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
                            st.success("Account created.")
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
# 4. ARCHWAY UI (RESTORING EXACT SIDEBAR LAYOUT)
# ==================================================
st.set_page_config(page_title="The Dojo", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e0e0e0; }
    .stChatMessage { background-color: #f8f9fa; border: 1px solid #e0e0e0; }
    .sidebar-dojo { font-size: 2.2rem !important; font-weight: 800; color: #1a1a1a; font-style: italic; margin-bottom: -10px; }
    
    /* Layout Restoration Styles */
    .active-rank { color: #000000; font-weight: 800; font-size: 1.4em; margin-top: 15px; margin-bottom: 5px; }
    .inactive-rank { color: #cccccc; font-weight: 400; font-size: 1.1em; margin-top: 10px; }
    .active-phase { color: #000000; font-weight: 600; padding-left: 20px; font-size: 1.1em; border-left: 2px solid #000; margin-bottom: 2px; }
    .inactive-phase { color: #bbbbbb; font-weight: 400; padding-left: 20px; font-size: 0.95em; border-left: 1px solid #eee; margin-bottom: 2px; }
    
    .slogan-stack-refined { font-size: 1.65em; text-align: center; color: #666666; font-style: italic; padding-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# ==================================================
# 5. DATA & SESSION
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
# 6. SIDEBAR - THE RESTORED NESTED LAYOUT
# ==================================================
with st.sidebar:
    st.markdown('<p class="sidebar-dojo">The-Dojo</p>', unsafe_allow_html=True)
    st.write(f"Warrior: **{USER_NAME}**")
    st.divider()
    
    # --- DYNAMIC RANK & PHASE LIST ---
    ranks = ["Student", "Practitioner", "Sentinel", "Sovereign"]
    for r in ranks:
        is_active_rank = (r == st.session_state.rank)
        st.markdown(f"<div class='{'active-rank' if is_active_rank else 'inactive-rank'}'>{r}</div>", unsafe_allow_html=True)
        
        # If this is the active rank, show its phases underneath
        if is_active_rank:
            current_phases = PHASE_SETS[r]
            for idx, p_name in enumerate(current_phases):
                is_active_phase = (idx == st.session_state.phase)
                st.markdown(f"<div class='{'active-phase' if is_active_phase else 'inactive-phase'}'>{p_name}</div>", unsafe_allow_html=True)
    
    st.divider()
    if st.button("Bow-Out (Save & Clear)", use_container_width=True):
        # Summary & Clear logic... (remains unchanged for integrity)
        if len(st.session_state.msgs) > 2:
            chat_log = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.msgs])
            headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
            payload = {"model": "llama-3.1-8b-instant", "messages": [{"role": "system", "content": "Summarize growth. One dense paragraph."}, {"role": "user", "content": chat_log}], "temperature": 0.3}
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
            summary = res.json()['choices'][0]['message']['content']
            supabase.table("ledger_wisdom").insert({"user_id": USER_ID, "timestamp": time.time(), "summary": summary}).execute()
        
        supabase.table("records").delete().eq("user_id", USER_ID).execute()
        st.session_state.msgs = []
        st.session_state.exchange_count = 0
        st.session_state.phase = 0
        st.rerun()

    if st.button("Logout"):
        del st.session_state.user
        st.rerun()

# ==================================================
# 7. MAIN ENGINE (LOGIC INTEGRITY)
# ==================================================
st.markdown('<div class="slogan-stack-refined">We. Never. Quit.</div>', unsafe_allow_html=True)

for msg in st.session_state.msgs:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"].split("] ", 1)[-1] if "] " in msg["content"] else msg["content"])

if prompt := st.chat_input("Speak from center..."):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    st.session_state.msgs.append({"role": "user", "content": f"[{ts}] {prompt}"})
    save_to_ledger("user", prompt, st.session_state.rank, st.session_state.phase)
    with st.chat_message("user"): st.markdown(prompt)

    # Phase Progression Logic
    st.session_state.exchange_count += 1
    if st.session_state.exchange_count >= 2:
        if st.session_state.phase < 3:
            st.session_state.phase += 1
            st.session_state.exchange_count = 0

    # AI Call
    headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
    MASTER_PROMPT = f"ROLE: Dojo Mentor. WARRIOR: {USER_NAME}. STYLE: Grounded, visceral, observant."
    messages = [{"role": "system", "content": MASTER_PROMPT}] + st.session_state.msgs[-15:]
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.6}, headers=headers)
    final_response = res.json()['choices'][0]['message']['content']
    
    with st.chat_message("assistant"): st.markdown(final_response)
    st.session_state.msgs.append({"role": "assistant", "content": final_response})
    save_to_ledger("assistant", final_response, st.session_state.rank, st.session_state.phase)
    st.rerun()
