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
        st.markdown(f"<div class='{'active
