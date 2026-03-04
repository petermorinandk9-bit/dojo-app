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
# 2. LOGIN GATE (THE BOUNCER)
# ==================================================
if 'user' not in st.session_state:
    st.set_page_config(page_title="The Dojo - Entry", layout="centered")
    st.markdown("""
        <style>
        .stApp { background-color: #ffffff; }
        .login-header { text-align: center; font-style: italic; font-weight: 800; font-size: 3rem; margin-bottom: 0px; }
        .login-sub { text-align: center; color: #666; margin-bottom: 30px; }
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown('<p class="login-header">The-Dojo</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-sub">Speak from center. Step onto the mat.</p>', unsafe_allow_html=True)
    
    with st.form("login_form"):
        u_name = st.text_input("Username").lower().strip()
        u_pass = st.text_input("Password", type="password")
        submit = st.form_submit_with_button("Enter the Dojo", use_container_width=True)
        
        if submit:
            res = supabase.table("users").select("*").eq("username", u_name).eq("password", u_pass).execute()
            if res.data:
                st.session_state.user = res.data[0]
                st.success(f"Welcome, {st.session_state.user['display_name']}.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Credentials not recognized.")
    st.stop() # LOCKS THE REST OF THE APP

# ==================================================
# 3. CORE CONFIG & PROMPTS
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
    f"CURRENT USER: {USER_NAME}. \n"
    "STYLE: Grounded, authoritative, and deeply observant. Speak like a man who respects the fire but loves the blade it produces. \n"
    "THE BALANCE: Be visceral and honest about the struggle, but use that honesty to fuel a high-stakes vision. \n"
    "RULES:\n"
    "1. THE LEDGER: Read the background context. Address THIS user's specific journey and patterns.\n"
    "2. NO CHEAP PRAISE: Acknowledge their raw experience as a forge.\n"
    "3. FORWARD MOVEMENT: End with ONE sharp, tactical question."
)

MIRROR_PROMPT = "ROLE: Dojo Mirror. Pure synthesis of the Ledger. Point out deep patterns with minimalist weight."

# ==================================================
# 4. ARCHWAY UI (MAIN APP)
# ==================================================
st.set_page_config(page_title="The Dojo", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e0e0e0; }
    .sidebar-dojo { font-size: 2.2rem !important; font-weight: 800; color: #1a1a1a; font-style: italic; margin-bottom: -10px; }
    .active-rank { color: #000000; font-weight: 700; font-size: 1.35em; }
    .inactive-rank { color: #666666; font-size: 1.1em; }
    .active-phase { color: #000000; font-weight: 600; padding-left: 10px; }
    .inactive-phase { color: #888888; padding-left: 10px; }
    .slogan-stack-refined { font-size: 1.65em; text-align: center; color: #666666; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# ==================================================
# 5. DATA OPERATIONS (FILTERED BY USER_ID)
# ==================================================
def save_to_ledger(role, text, rank, phase):
    data = {"user_id": USER_ID, "timestamp": time.time(), "role": role, "content": text, "rank": rank, "phase": str(phase)}
    supabase.table("records").insert(data).execute()

# Load Memory for this User
try:
    w_res = supabase.table("ledger_wisdom").select("*").eq("user_id", USER_ID).order("timestamp").execute()
    long_term_memory = "\n".join([f"- {r['summary']}" for r in w_res.data])
except: long_term_memory = ""

if 'msgs' not in st.session_state:
    st.session_state.msgs = []
    st.session_state.exchange_count = 0
    st.session_state.rank = "Student"
    st.session_state.phase = 0
    
    # Load Chat History for this User
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
# 6. SIDEBAR & BOW-OUT
# ==================================================
with st.sidebar:
    st.markdown(f'<p class="sidebar-dojo">The-Dojo</p>', unsafe_allow_html=True)
    st.write(f"Warrior: **{USER_NAME}**")
    st.divider()
    
    ranks = ["Student", "Practitioner", "Sentinel", "Sovereign"]
    for r in ranks:
        st.markdown(f"<p class='{'active-rank' if r == st.session_state.rank else 'inactive-rank'}'>{'➤ ' if r == st.session_state.rank else ''}{r}</p>", unsafe_allow_html=True)
    
    st.divider()
    if st.button("Bow-Out", use_container_width=True):
        if len(st.session_state.msgs) > 2:
            chat_log = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.msgs])
            headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "system", "content": "Summarize user growth. One dense paragraph."}, {"role": "user", "content": chat_log}],
                "temperature": 0.3
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
            summary = res.json()['choices'][0]['message']['content']
            supabase.table("ledger_wisdom").insert({"user_id": USER_ID, "timestamp": time.time(), "summary": summary}).execute()
        
        supabase.table("records").delete().eq("user_id", USER_ID).execute()
        st.session_state.msgs = []
        st.rerun()
        
    if st.button("Logout"):
        del st.session_state.user
        st.rerun()

# ==================================================
# 7. CHAT INTERFACE
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

    # Simple AI Call
    headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
    messages = [{"role": "system", "content": MASTER_PROMPT + f"\n\nContext: {long_term_memory}"}] + st.session_state.msgs[-10:]
    payload = {"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.6}
    
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
    final_response = res.json()['choices'][0]['message']['content']
    
    with st.chat_message("assistant"): st.markdown(final_response)
    st.session_state.msgs.append({"role": "assistant", "content": final_response})
    save_to_ledger("assistant", final_response, st.session_state.rank, st.session_state.phase)
