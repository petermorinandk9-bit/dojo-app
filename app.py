import streamlit as st
import sqlite3
import requests
import time

# ==================================================
# 1. CORE CONFIG & "GROUNDED MENTOR" PROMPTS
# ==================================================
PHASE_SETS = {
    "Student": ["Welcome Mat", "Warm-Up", "Training", "Cool Down"],
    "Practitioner": ["Step Onto the Mat", "Feel It Out", "Work the Pattern", "Close the Round"],
    "Sentinel": ["Enter the Dojo", "Center", "Engage", "Seal & Step Out"],
    "Sovereign": ["Check-In", "Look Closer", "Name It", "Next Step"]
}

MASTER_PROMPT = (
    "ROLE: Dojo Mentor. \n"
    "You are a grounded, supportive mentor—not a harsh commander, but not a soft therapist either.\n"
    "CRITICAL RULES:\n"
    "1. BALANCE & LENGTH: Write 1 to 2 conversational paragraphs. Give the response room to breathe, but avoid long essays.\n"
    "2. GROUNDED EMPATHY: Acknowledge their state, but do not be overly agreeable (avoid phrases like 'I totally understand exactly how you feel'). Validate quietly, then pivot to growth.\n"
    "3. PATTERNS & SOLUTIONS: Review the 'User's Recent History'. Point out recurring themes. Offer a practical perspective, a structural observation, or a grounded solution if applicable.\n"
    "4. GROWTH QUESTION: End by asking a thoughtful question aimed at growth—such as asking 'why' a pattern exists, what the next tactical step is, or if they want to explore a specific feeling deeper."
)

MIRROR_PROMPT = (
    "ROLE: Dojo Mirror.\n"
    "Reflect the user's truth with supportive, grounded wisdom.\n"
    "CRITICAL RULES:\n"
    "1. BALANCE: Write about 3 to 5 sentences. \n"
    "2. TONE: Act as a wise mentor. Acknowledge the weight of their words without coddling.\n"
    "3. REFLECTION & INQUIRY: Review the 'User's Recent History'. Point out an underlying pattern, then ask a single, probing question to help them look deeper or take action."
)

# ==================================================
# 2. ARCHWAY UI - LIGHT MODE
# ==================================================
st.set_page_config(page_title="Sovereign Dojo", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e0e0e0; }
    .stChatMessage { background-color: #f8f9fa; border: 1px solid #e0e0e0; }
    .active-rank { color: #000000; font-weight: 700; font-size: 1.35em; margin-bottom: 4px; }
    .inactive-rank { color: #666666; font-size: 1.1em; margin-bottom: 4px; }
    .active-phase { color: #000000; font-weight: 600; font-size: 1.15em; margin-bottom: 2px; padding-left: 10px; }
    .inactive-phase { color: #888888; font-size: 1.0em; margin-bottom: 2px; padding-left: 10px; }
    .watermark { position: fixed; bottom: 40%; left: 50%; transform: translateX(-50%); font-size: 11rem; opacity: 0.04; color: #111111; pointer-events: none; z-index: -1; user-select: none; }
    .crisis-box { background-color: #ffe6e6; border-left: 5px solid #ff0000; padding: 15px; margin-top: 10px; border-radius: 5px; }
    .crisis-text { color: #cc0000; font-weight: bold; font-size: 1.1em; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# ==================================================
# 3. DATABASE: THE ROLLING LEDGER
# ==================================================
def init_db():
    conn = sqlite3.connect('sovereign.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL, role TEXT, content TEXT, rank TEXT, phase TEXT)''')
    conn.commit()
    return conn

conn = init_db()

def save_to_ledger(role, text, rank, phase):
    c = conn.cursor()
    c.execute("INSERT INTO records (timestamp, role, content, rank, phase) VALUES (?, ?, ?, ?, ?)",
              (time.time(), role, text, rank, phase))
    conn.commit()

def get_recent_history(limit=30):
    c = conn.cursor()
    c.execute("SELECT role, content FROM records ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    if not rows: return "No past patterns established yet."
    history = "\n".join([f"{row[0]}: {row[1]}" for row in reversed(rows)])
    return history

# Initialize State
if 'phase' not in st.session_state: st.session_state.phase = 0
if 'rank' not in st.session_state: st.session_state.rank = "Student"
if 'msgs' not in st.session_state: st.session_state.msgs = []
if 'exchange_count' not in st.session_state: st.session_state.exchange_count = 0

# ==================================================
# 4. SIDEBAR LOGIC
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
    st.markdown("**Current Phase:**")
    for idx, phase_name in enumerate(current_phases):
        if idx == st.session_state.phase:
            st.markdown(f"<p class='active-phase'>➤ {phase_name}</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p class='inactive-phase'>{phase_name}</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Bow-Out"):
        for key in list(st.session
