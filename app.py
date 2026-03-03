import streamlit as st
import sqlite3
import time
import requests

# ==================================================
# 1. CORE CONFIG & SOVEREIGN PROMPTS
# ==================================================
PHASE_SETS = {
    "Student": ["Welcome Mat", "Warm-Up", "Training", "Cool Down"],
    "Practitioner": ["Step Onto the Mat", "Feel It Out", "Work the Pattern", "Close the Round"],
    "Sentinel": ["Enter the Dojo", "Center", "Engage", "Seal & Step Out"],
    "Sovereign": ["Check-In", "Look Closer", "Name It", "Next Step"]
}

# --- THE SOUL RESTORATION ---
MASTER_PROMPT = """ROLE: Disciplined Warrior / Dojo Lead.
Observe the state without judgment. Name the immediate fact. 
Minimalist. Strength in reserve. No 'inhale/exhale' fluff. Max 3 lines."""

MIRROR_PROMPT = """ROLE: Dojo Mirror (Semantic).
Reflect patterns/echoes with surgical precision. Hold the line. 
No coaching. Just the truth. Identify the 'Shield' if present."""

CRISIS_PROMPT = """ROLE: Sensei (Emergency). 
Ground the user in immediate physical facts. 
ALWAYS include: Call/Text 988 or Text HOME to 741741."""

SENTINEL_PROMPT = "ROLE: Sentinel. Validate the next tactical step with absolute clarity."

# ==================================================
# 2. ARCHWAY UI (CSS CUSTOMIZATION)
# ==================================================
st.set_page_config(page_title="Sovereign Dojo", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #080808; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #121212; border-right: 1px solid #333333; }
    
    /* Rank Path Colors */
    .active-rank { color: #FFFFFF; font-weight: 700; font-size: 1.3em; }
    .inactive-rank { color: #444444; font-size: 1.1em; }
    
    /* Semicolon-Infinity Watermark (5% Opacity) */
    .stApp::before {
        content: ""; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        width: 300px; height: 300px; opacity: 0.05; z-index: -1;
        background-image: url('https://raw.githubusercontent.com/your-repo/assets/main/semicolon_infinity.svg');
        background-repeat: no-repeat; background-size: contain;
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
    return conn

if 'phase' not in st.session_state: st.session_state.phase = 0
if 'rank' not in st.session_state: st.session_state.rank = "Student"
if 'msgs' not in st.session_state: st.session_state.msgs = []
if 'exchange_count' not in st.session_state: st.session_state.exchange_count = 0
if '_advance_next' not in st.session_state: st.session_state._advance_next = False

# ==================================================
# 4. SIDEBAR: THE RANK PATH
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
    
    # Dynamic Phase Name
    current_phases = PHASE_SETS.get(st.session_state.rank)
    active_phase_name = current_phases[st.session_state.phase]
    
    st.markdown(f"**Current State:** {active_phase_name}")
    st.progress((st.session_state.phase + 1) / 4)
    st.markdown(f"**Exchanges:** {st.session_state.exchange_count}/3")
    
    if st.button("Reset Session"):
        st.session_state.clear()
        st.rerun()

# ==================================================
# 5. MAIN INTERFACE & LOGIC
# ==================================================
st.title("Warriors Don't Always Win — Warriors Always Fight")

# Display Chat History
for msg in st.session_state.msgs:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("Enter the Dojo..."):
    st.session_state.msgs.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- SENSY/SAFETY CHECK ---
    def is_crisis(text):
        keywords = ["cut myself", "self harm", "suicide", "end my life", "blade", "razor"]
        return any(kw in text.lower() for kw in keywords)

    # --- AI RESPONSE (Grok Logic) ---
    with st.chat_message("assistant"):
        # System Instruction Construction
        sys_msg = MASTER_PROMPT if st.session_state.phase < 2 else MIRROR_PROMPT
        if is_crisis(prompt): sys_msg = CRISIS_PROMPT
        
        # Placeholder for API Call (Using st.secrets["XAI_API_KEY"])
        # response = call_grok_api(sys_msg, st.session_state.msgs)
        response = "The Architect is verifying the logic. (Weld successful)." 
        
        st.markdown(response)
        st.session_state.msgs.append({"role": "assistant", "content": response})
        st.session_state.exchange_count += 1

    # --- DELAYED ADVANCE LOGIC ---
    if st.session_state.exchange_count >= 3:
        if st.button(f"Advance to {current_phases[st.session_state.phase + 1] if st.session_state.phase < 3 else 'Next Rank'}"):
            if st.session_state.phase < 3:
                st.session_state.phase += 1
            else:
                st.session_state.phase = 0
                # Logic to shift Rank could go here
            st.session_state.exchange_count = 0
            st.rerun()

st.divider()
st.caption("We Never Quit | Sovereign v10.8")
