import streamlit as st
import sqlite3
import requests
import time

# ==================================================
# 1. CORE CONFIG & WARMER PROMPTS
# ==================================================
PHASE_SETS = {
    "Student": ["Welcome Mat", "Warm-Up", "Training", "Cool Down"],
    "Practitioner": ["Step Onto the Mat", "Feel It Out", "Work the Pattern", "Close the Round"],
    "Sentinel": ["Enter the Dojo", "Center", "Engage", "Seal & Step Out"],
    "Sovereign": ["Check-In", "Look Closer", "Name It", "Next Step"]
}

MASTER_PROMPT = """ROLE: Dojo Mentor. 
You are a grounded, supportive, and empathetic listener. 
Validate the user's state warmly. Speak naturally and kindly, offering a conversational reflection. 
Avoid clinical, cold, or robotic phrasing. Be a warm human presence."""

MIRROR_PROMPT = """ROLE: Dojo Mirror.
Reflect on the user's words with warm, empathetic insight. 
Speak like a wise, caring mentor offering perspective. 
Acknowledge their journey and offer supportive conversation. Hold space for them."""

CRISIS_PROMPT = """ROLE: Sensei (Emergency).
Ground the user gently and safely in the present moment.
ALWAYS include: Call/Text 988 or Text HOME to 741741."""

# ==================================================
# 2. ARCHWAY UI - LIGHT MODE
# ==================================================
st.set_page_config(page_title="Sovereign Dojo", layout="wide")

st.markdown("""
    <style>
    .stApp { 
        background-color: #ffffff; 
        color: #1a1a1a; 
    }
    [data-testid="stSidebar"] { 
        background-color: #f8f9fa; 
        border-right: 1px solid #e0e0e0; 
    }
    .stChatMessage {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
    }
    
    /* Rank Path - active bold black with arrow, inactive light grey */
    .active-rank { 
        color: #000000; 
        font-weight: 700; 
        font-size: 1.35em; 
        margin-bottom: 4px;
    }
    .inactive-rank { 
        color: #666666; 
        font-size: 1.1em; 
        margin-bottom: 4px;
    }
    
    /* Semicolon-Infinity Watermark */
    .watermark {
        position: fixed;
        bottom: 40%;
        left: 50%;
        transform: translateX(-50%);
        font-size: 11rem;
        opacity: 0.04;
        color: #111111;
        pointer-events: none;
        z-index: -1;
        user-select: none;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================================================
# 3. DATABASE & SESSION STATE
# ==================================================
def init_db():
    conn = sqlite3.connect('sovereign.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL, content TEXT,
                  rank TEXT, phase TEXT, vector TEXT)''')
    conn.commit()
    conn.close()

init_db()

if 'phase' not in st.session_state:
    st.session_state.phase = 0
if 'rank' not in st.session_state:
    st.session_state.rank = "Student"
if 'msgs' not in st.session_state:
    st.session_state.msgs = []
if 'exchange_count' not in st.session_state:
    st.session_state.exchange_count = 0

# ==================================================
# 4. SIDEBAR: THE RANK PATH (Progress Bar Removed)
# ==================================================
with st.sidebar:
    st.markdown("## **The Dojo**")
    st.divider()
    
    ranks = ["Student", "Practitioner", "Sentinel", "Sovereign"]
    for r in ranks:
        if r == st.session_state.rank:
            st.markdown(f"<p class='active-rank'>➤ {r}</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p class='inactive-rank'>{r}</p>", unsafe_allow_html=True)
    
    st.divider()
    
    current_phases = PHASE_SETS.get(st.session_state.rank, PHASE_SETS["Student"])
    active_phase_name = current_phases[st.session_state.phase]
    
    st.markdown(f"**Current State:** {active_phase_name}")
    st.markdown(f"**Exchanges:** {st.session_state.exchange_count}/3")
    
    if st.button("Reset Session"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ==================================================
# 5. MAIN INTERFACE
# ==================================================
st.markdown('<div style="text-align:center; font-size:2.1rem; font-weight:700; margin:1.5rem 0;">Warriors Don\'t Always Win — Warriors Always Fight</div>', unsafe_allow_html=True)
st.markdown('<div class="watermark">;∞</div>', unsafe_allow_html=True)

# Display Chat History
for msg in st.session_state.msgs:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==================================================
# 6. USER INPUT, GROQ API & AUTO-ADVANCE LOGIC
# ==================================================
if prompt := st.chat_input("Enter the Dojo..."):
    st.session_state.msgs.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # Safety Check
    def is_crisis(text):
        keywords = ["cut myself", "self harm", "kill myself", "suicide", "end my life", "blade", "razor"]
        return any(kw in text.lower() for kw in keywords)

    # Dynamic System Prompt
    if is_crisis(prompt):
        sys_msg = CRISIS_PROMPT
    elif st.session_state.phase >= 2:
        sys_msg = MIRROR_PROMPT
    else:
        sys_msg = MASTER_PROMPT

    messages = [{"role": "system", "content": sys_msg}]
    for m in st.session_state.msgs:
        messages.append({"role": m["role"], "content": m["content"]})

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets.get('GROQ_API_KEY', '')}"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages
