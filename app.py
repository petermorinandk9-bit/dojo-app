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
# 2. THE DOJO GATE (LOGIN SCREEN)
# ==================================================
if 'user' not in st.session_state:
    st.set_page_config(page_title="The Dojo - Entry", layout="centered")
    st.markdown("""
        <style>
        .stApp { background-color: #ffffff; }
        .login-header { text-align: center; font-style: italic; font-weight: 800; font-size: 3.5rem; color: #1a1a1a; margin-bottom: 0px; }
        .login-sub { text-align: center; color: #666; font-size: 1.2rem; margin-bottom: 40px; }
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown('<p class="login-header">The-Dojo</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-sub">Speak from center. Step onto the mat.</p>', unsafe_allow_html=True)
    
    with st.container():
        with st.form("login_gate"):
            u_name = st.text_input("Username").lower().strip()
            u_pass = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Enter the Dojo", use_container_width=True)
            
            if submitted:
                res = supabase.table("users").select("*").eq("username", u_name).eq("password", u_pass).execute()
                if res.data:
                    st.session_state.user = res.data[0]
                    st.success(f"Welcome, {st.session_state.user['display_name']}. The mat is yours.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("The Dojo does not recognize those credentials.")
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

MASTER_PROMPT = (
    f"ROLE: Dojo Mentor. \n"
    f"CURRENT WARRIOR: {USER_NAME}. \n"
    "STYLE: Grounded, authoritative, and deeply observant. Speak like a man who respects the fire but loves the blade it produces. \n"
    "THE BALANCE: Be visceral and honest about the struggle, but use that honesty to fuel a high-stakes vision. \n"
    "RULES:\n"
    "1. THE LEDGER: Use the background context provided. Address THIS specific user's patterns and history. \n"
    "2. NO CHEAP PRAISE: Acknowledge the user's raw experience as a forge for their future.\n"
    "3. NO FLUFF: Keep the prose tight. No fillers.\n"
    "4. FORWARD MOVEMENT: End with ONE sharp, tactical question."
)

# ==================================================
# 4. ARCHWAY UI (MAIN APP)
# ==================================================
st.set_page_config(page_title="The Dojo", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e0e0e0; }
    .stChatMessage { background-color: #f8f9fa; border: 1px solid #e0e0e0; }
    .sidebar-dojo { font-size: 2.2rem !important; font-weight: 800; color: #1a1a1a; font-style: italic; line-height: 1.1; }
    .active-rank { color: #000000; font-weight: 700; font-size: 1.35em; }
    .inactive-rank { color: #666666; font-size: 1.1em; }
    .active-phase { color: #000000; font-weight: 600; padding-left: 10px; }
    .inactive-phase { color: #888888; padding-left: 10px; }
    .slogan-stack-refined { font-size: 1.65em; text-align: center; color: #666666; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# ==================================================
# 5. DATA OPERATIONS (PRIVATE LEDGERS)
# ==================================================
def save_to_ledger(role, text, rank, phase):
    data = {"user_id": USER_ID, "timestamp": time.time(), "role": role, "content": text, "rank": rank, "phase": str(phase)}
    supabase.table("records").insert(data).execute()

# Load User's Long Term Memory
try:
    w_res = supabase.table("ledger_wisdom").select("*").eq("user_id", USER_ID).order("timestamp").execute()
    long_term_memory = "\n".join([f"- {r['summary']}" for r in w_res.data])
except:
    long_term_memory = ""

# Load User's Session State
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
# 6. SIDEBAR - DOJO STATUS
# ==================================================
with st.sidebar:
    st.markdown('<p class="sidebar-dojo">The-Dojo</p>', unsafe_allow_html=True)
    st.write(f"Logged in as: **{USER_NAME}**")
    st.divider()
    
    ranks = ["Student", "Practitioner", "Sentinel", "Sovereign"]
    for r in ranks:
        st.markdown(f"<p class='{'active-rank' if r == st.session_state.rank else 'inactive-rank'}'>{'➤ ' if r == st.session_state.rank else ''}{r}</p>", unsafe_allow_html=True)
    
    st.divider()
    if st.button("Bow-Out (Save & Clear)", use_container_width=True):
        if len(st.session_state.msgs) > 2:
            with st.spinner("Archiving wisdom..."):
                chat_log = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.msgs])
                headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "system", "content": "Summarize user growth and key breakthroughs. One dense paragraph."}, {"role": "user", "content": chat_log}],
                    "temperature": 0.3
                }
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
# 7. MAIN ENGINE
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

    # AI Call
    headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
    messages = [{"role": "system", "content": MASTER_PROMPT + f"\n\nPAST WISDOM:\n{long_term_memory}"}] + st.session_state.msgs[-15:]
    payload = {"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.6}
    
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
        final_response = res.json()['choices'][0]['message']['content']
    except:
        final_response = "The transmission was severed. Stand firm and try again."
    
    with st.chat_message("assistant"): st.markdown(final_response)
    st.session_state.msgs.append({"role": "assistant", "content": final_response})
    save_to_ledger("assistant", final_response, st.session_state.rank, st.session_state.phase)
    st.rerun()
