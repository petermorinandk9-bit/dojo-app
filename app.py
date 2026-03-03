import streamlit as st
import sqlite3
import requests
import time

# ==================================================
# 1. CORE CONFIG & PROMPTS
# ==================================================
PHASE_SETS = {
    "Student": ["Welcome Mat", "Warm-Up", "Training", "Cool Down"],
    "Practitioner": ["Step Onto the Mat", "Feel It Out", "Work the Pattern", "Close the Round"],
    "Sentinel": ["Enter the Dojo", "Center", "Engage", "Seal & Step Out"],
    "Sovereign": ["Check-In", "Look Closer", "Name It", "Next Step"]
}

MASTER_PROMPT = (
    "ROLE: Dojo Mentor. \n"
    "You are a grounded, supportive guide. You are a mentor—not a soft therapist, and NOT a harsh sensei.\n"
    "CRITICAL RULES:\n"
    "1. CONVERSATIONAL LENGTH: 1 to 2 paragraphs.\n"
    "2. GROUNDED EMPATHY: Acknowledge reality without clinical fluff.\n"
    "3. PATTERNS: Offer practical observations based on 'User Recent History'.\n"
    "4. FORWARD MOVEMENT: End with a thoughtful question to prompt growth."
)

MIRROR_PROMPT = (
    "ROLE: Dojo Mirror. Reflect truth with supportive, grounded wisdom. "
    "Concise paragraph. No therapy fluff. One probing question."
)

# ==================================================
# 2. ARCHWAY UI - SOVEREIGN LIGHT MODE
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
# 3. DATABASE & PERSISTENT MEMORY
# ==================================================
@st.cache_resource
def get_db_connection():
    return sqlite3.connect('sovereign.db', check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL, role TEXT, content TEXT, rank TEXT, phase TEXT)''')
    conn.commit()

init_db()

def save_to_ledger(role, text, rank, phase):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO records (timestamp, role, content, rank, phase) VALUES (?, ?, ?, ?, ?)",
              (time.time(), role, text, rank, phase))
    conn.commit()

# --- STATE RECOVERY ---
if 'msgs' not in st.session_state:
    st.session_state.msgs = []
    st.session_state.exchange_count = 0
    st.session_state.rank = "Student"
    st.session_state.phase = 0
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT role, content, rank, phase FROM records ORDER BY timestamp ASC")
    rows = c.fetchall()
    for r in rows:
        st.session_state.msgs.append({"role": r[0], "content": r[1]})
    
    if rows:
        st.session_state.rank = rows[-1][2]
        try:
            st.session_state.phase = int(rows[-1][3])
        except:
            st.session_state.phase = 0

# ==================================================
# 4. SIDEBAR LOGIC (Cleaned Up)
# ==================================================
with st.sidebar:
    st.markdown("## **Sovereign UI**")
    st.divider()
    
    ranks = ["Student", "Practitioner", "Sentinel", "Sovereign"]
    for r in ranks:
        if r == st.session_state.rank:
            st.markdown(f"<p class='active-rank'>➤ {r}</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p class='inactive-rank'>{r}</p>", unsafe_allow_html=True)
    
    st.divider()
    
    # "Current Phase" Label Removed per instruction
    current_phases = PHASE_SETS.get(st.session_state.rank, PHASE_SETS["Student"])
    for idx, phase_name in enumerate(current_phases):
        if idx == st.session_state.phase:
            st.markdown(f"<p class='active-phase'>➤ {phase_name}</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p class='inactive-phase'>{phase_name}</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Bow-Out", use_container_width=True):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM records")
        conn.commit()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ==================================================
# 5. MAIN INTERFACE
# ==================================================
st.markdown('<div style="text-align:center; font-size:2.1rem; font-weight:700; margin:1.5rem 0;">Warriors Don\'t Always Win — Warriors Always Fight</div>', unsafe_allow_html=True)
st.markdown('<div class="watermark">;∞</div>', unsafe_allow_html=True)

for msg in st.session_state.msgs:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# ==================================================
# 6. ENGINE ROUTING
# ==================================================
if prompt := st.chat_input("Speak from center..."):
    st.session_state.msgs.append({"role": "user", "content": prompt})
    save_to_ledger("user", prompt, st.session_state.rank, str(st.session_state.phase))
    st.session_state.exchange_count += 1
    
    with st.chat_message("user"):
        st.markdown(prompt)

    crisis_keywords = ["kill myself", "suicide", "hurt myself", "end my life"]
    is_crisis = any(k in prompt.lower() for k in crisis_keywords)

    def check_readiness(user_text):
        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "system", "content": "Analyze if user shows forward growth. Reply ONLY YES or NO."}, {"role": "user", "content": user_text}],
            "temperature": 0.0, "max_tokens": 5
        }
        try:
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=5)
            return "YES" in res.json()['choices'][0]['message']['content'].upper()
        except: return False

    with st.chat_message("assistant"):
        if is_crisis:
            safety_box = (
                "I am here with you, but I cannot provide guidance or assistance related to self-harm.\n\n"
                "<div class='crisis-box'><p class='crisis-text'>Support is available: <strong>988</strong> or text <strong>741741</strong></p></div>"
            )
            st.markdown(safety_box, unsafe_allow_html=True)
            st.session_state.msgs.append({"role": "assistant", "content": safety_box})
            save_to_ledger("assistant", safety_box, st.session_state.rank, str(st.session_state.phase))
        else:
            sys_msg = MIRROR_PROMPT if st.session_state.phase >= 2 else MASTER_PROMPT
            messages = [{"role": "system", "content": sys_msg}] + st.session_state.msgs[-30:]
            headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
            payload = {"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.45, "max_tokens": 512}
            
            try:
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=25)
                final_response = res.json()['choices'][0]['message']['content']
            except:
                final_response = "**System Alert:** Transmission issue."

            st.markdown(final_response)
            st.session_state.msgs.append({"role": "assistant", "content": final_response})
            save_to_ledger("assistant", final_response, st.session_state.rank, str(st.session_state.phase))
            
            if st.session_state.exchange_count >= 2:
                if check_readiness(prompt) or st.session_state.exchange_count >= 6:
                    st.session_state.exchange_count = 0
                    if st.session_state.phase < 3:
                        st.session_state.phase += 1
                    else:
                        st.session_state.phase = 0
                        ranks = ["Student", "Practitioner", "Sentinel", "Sovereign"]
                        try:
                            st.session_state.rank = ranks[ranks.index(st.session_state.rank) + 1]
                        except: pass
    st.rerun()
