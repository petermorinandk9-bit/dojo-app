import streamlit as st
import sqlite3
import requests
import time
from datetime import datetime

# ==================================================
# 1. CORE CONFIG - THE DYNAMIC SENSEI
# ==================================================
PHASE_SETS = {
    "Student": ["Welcome Mat", "Warm Up", "Training", "Reflection/Cool Down"],
    "Practitioner": ["Step Onto the Mat", "Warm Up", "Work the Pattern", "Wisdom/Cool Down"],
    "Sentinel": ["Enter the Dojo", "Center", "Engage", "Seal/Reflection"],
    "Sovereign": ["Check-In", "Look Closer", "Name It", "The Wisdom Step"]
}

MASTER_PROMPT = (
    "ROLE: Dojo Mentor. \n"
    "STYLE: Grounded, authoritative, observant. \n"
    "DYNAMIC DEPTH: Match the 'gravity' of the user's input. \n"
    "1. LIGHT INPUT: 1-2 punchy, strategic sentences. \n"
    "2. HEAVY INPUT: AUTHORIZED for multi-paragraph structural analysis (up to 4 paragraphs). \n"
    "TEMPORAL SOUL: Use [YYYY-MM-DD] to see patterns. Never read the clock aloud. \n"
    "RULES:\n"
    "1. THE LEDGER: Synthesize history and connect today's effort to the larger arc.\n"
    "2. SUBSTANCE: Every response must contain a 'Structural Anchor'.\n"
    "3. NO FLUFF: Every sentence must serve the mission.\n"
    "4. FORWARD MOVEMENT: End with ONE sharp, tactical question."
)

MIRROR_PROMPT = (
    "ROLE: Dojo Mirror. \n"
    "GOAL: Pure synthesis of the Ledger. Observe the rhythm of the timestamps and point out deep patterns."
)

# ==================================================
# 2. ARCHWAY UI
# ==================================================
st.set_page_config(page_title="The Dojo", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e0e0e0; }
    .stChatMessage { background-color: #f8f9fa; border: 1px solid #e0e0e0; }
    .sidebar-dojo { font-size: 2.2rem !important; font-weight: 800; color: #1a1a1a; font-style: italic; margin-bottom: -10px; line-height: 1.1; }
    .active-rank { color: #000000; font-weight: 700; font-size: 1.35em; margin-bottom: 4px; }
    .inactive-rank { color: #666666; font-size: 1.1em; margin-bottom: 4px; }
    .active-phase { color: #000000; font-weight: 600; font-size: 1.15em; margin-bottom: 2px; padding-left: 10px; }
    .inactive-phase { color: #888888; font-size: 1.0em; margin-bottom: 2px; padding-left: 10px; }
    .watermark { position: fixed; bottom: 40%; left: 50%; transform: translateX(-50%); font-size: 11rem; opacity: 0.04; color: #111111; pointer-events: none; z-index: -1; user-select: none; }
    .slogan-stack-refined { font-size: 1.65em; text-align: center; color: #666666; font-style: italic; margin-top: 5px; line-height: 1.3; }
    .spacer { margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# ==================================================
# 3. DATABASE
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

if 'msgs' not in st.session_state:
    st.session_state.msgs = []
    st.session_state.exchange_count = 0
    st.session_state.rank = "Student"
    st.session_state.phase = 0
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT timestamp, role, content, rank, phase FROM records ORDER BY timestamp ASC")
    rows = c.fetchall()
    for r in rows:
        timestamp_str = datetime.fromtimestamp(r[0]).strftime('%Y-%m-%d %H:%M')
        st.session_state.msgs.append({"role": r[1], "content": f"[{timestamp_str}] {r[2]}"})
    if rows:
        st.session_state.rank = rows[-1][3]
        try: st.session_state.phase = int(rows[-1][4])
        except: st.session_state.phase = 0

# ==================================================
# 4. SIDEBAR
# ==================================================
with st.sidebar:
    st.markdown('<p class="sidebar-dojo">The-Dojo</p>', unsafe_allow_html=True)
    st.divider()
    ranks = ["Student", "Practitioner", "Sentinel", "Sovereign"]
    for r in ranks:
        st.markdown(f"<p class='{'active-rank' if r == st.session_state.rank else 'inactive-rank'}'>{'➤ ' if r == st.session_state.rank else ''}{r}</p>", unsafe_allow_html=True)
    st.divider()
    current_phases = PHASE_SETS.get(st.session_state.rank, PHASE_SETS["Student"])
    for idx, phase_name in enumerate(current_phases):
        st.markdown(f"<p class='{'active-phase' if idx == st.session_state.phase else 'inactive-phase'}'>{'➤ ' if idx == st.session_state.phase else ''}{phase_name}</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Bow-Out", use_container_width=True):
        st.session_state.phase = 0
        st.session_state.exchange_count = 0
        st.toast("Mat Cleared.", icon="🥋")
        st.rerun()

# ==================================================
# 5. MAIN INTERFACE
# ==================================================
st.markdown('<div class="slogan-stack-refined">Warriors Don\'t Always Win — Warriors Always Fight</div>', unsafe_allow_html=True)
st.markdown('<div class="slogan-stack-refined">We. Never. Quit.</div>', unsafe_allow_html=True)
st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
st.markdown('<div class="watermark">;∞</div>', unsafe_allow_html=True)

for msg in st.session_state.msgs:
    with st.chat_message(msg["role"]):
        display_text = msg["content"].split("] ", 1)[-1] if "] " in msg["content"] else msg["content"]
        st.markdown(display_text, unsafe_allow_html=True)

# ==================================================
# 6. ENGINE ROUTING
# ==================================================
if prompt := st.chat_input("Speak from center..."):
    current_ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    st.session_state.msgs.append({"role": "user", "content": f"[{current_ts}] {prompt}"})
    save_to_ledger("user", prompt, st.session_state.rank, str(st.session_state.phase))
    st.session_state.exchange_count += 1
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🧘‍♂️ Let me think about this a moment...", expanded=False) as status:
            # Get response first
            sys_msg = MIRROR_PROMPT if st.session_state.phase == 3 else MASTER_PROMPT
            messages = [{"role": "system", "content": sys_msg}] + st.session_state.msgs[-30:]
            headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
            payload = {"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.55, "max_tokens": 1024}
            
            try:
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=25)
                final_response = res.json()['choices'][0]['message']['content']
                
                # Dynamic Delay logic with a 5-second CAP
                ai_word_count = len(final_response.split())
                dynamic_delay = 1.0 + (ai_word_count * 0.05) 
                time.sleep(min(dynamic_delay, 5.0)) # REFINED: Capped at 5 seconds
                
                status.update(label="🙏 Wisdom Found.", state="complete", expanded=False)
            except: 
                final_response = "**System Alert:** Transmission issue."
                status.update(label="⚠️ Connection Severed.", state="error")
        
        st.markdown(final_response)
        st.session_state.msgs.append({"role": "assistant", "content": final_response})
        save_to_ledger("assistant", final_response, st.session_state.rank, str(st.session_state.phase))
        
        # Advancement logic
        if st.session_state.exchange_count >= 2:
            check_payload = {"model": "llama-3.1-8b-instant", "messages": [{"role": "system", "content": "Analyze growth. Reply ONLY YES or NO."}, {"role": "user", "content": prompt}], "temperature": 0.0}
            try:
                readiness = requests.post("https://api.groq.com/openai/v1/chat/completions", json=check_payload, headers=headers, timeout=5)
                is_ready = "YES" in readiness.json()['choices'][0]['message']['content'].upper()
            except: is_ready = False

            if is_ready or st.session_state.exchange_count >= 6:
                st.session_state.exchange_count = 0
                if st.session_state.phase < 3: st.session_state.phase += 1
                else:
                    st.session_state.phase = 0
                    ranks = ["Student", "Practitioner", "Sentinel", "Sovereign"]
                    try: st.session_state.rank = ranks[ranks.index(st.session_state.rank) + 1]
                    except: pass
    st.rerun()
