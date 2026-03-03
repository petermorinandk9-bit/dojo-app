import streamlit as st
from openai import OpenAI
import sqlite3
import time

# === PROMPTS (exact from blueprints) ===
MASTER_PROMPT = "ROLE: Disciplined Warrior / Dojo Lead. Observe the state without judgment. Name the immediate fact. Minimalist. Strength in reserve. No mindfulness fluff. Max 3 lines."
MIRROR_PROMPT = "ROLE: Dojo Mirror (Semantic). Identify Shield. Compare with semantically relevant past truths. Name recurring patterns/echoes. No coaching. Just the truth."
CRISIS_PROMPT = "ROLE: Sensei (Emergency). Ground the user in immediate physical facts. ALWAYS include: Call/Text 988 or Text HOME to 741741."
SENTINEL_PROMPT = "ROLE: Sentinel. Validate the next tactical step with absolute clarity."
CLOSURE_PROMPT = "ROLE: Dojo Closure. Confirm the session's structural gains. Ask exactly: \"Is there anything else we can work on today?\""

def contains_self_harm(text):
    t = text.lower()
    keywords = ["cut myself", "self harm", "kill myself", "suicide", "end my life", "blade", "razor"]
    return any(kw in t for kw in keywords)

# === DB ===
def init_db():
    conn = sqlite3.connect('records.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp REAL,
        content TEXT,
        rank TEXT,
        phase TEXT,
        vector TEXT
    )''')
    conn.commit()
    conn.close()

def log_record(content, rank, phase, vector="[]"):
    conn = sqlite3.connect('records.db')
    conn.execute("INSERT INTO records (timestamp, content, rank, phase, vector) VALUES (?, ?, ?, ?, ?)",
                 (time.time(), content, rank, str(phase), vector))
    conn.commit()
    conn.close()

init_db()

# === UI ===
st.set_page_config(page_title="Grounded Kenpo", page_icon="⚔️", layout="centered")
st.markdown("""
<style>
.stApp {background-color: #080808; color: #ffffff;}
.stChatMessage {background-color: #1a1a1a; border: 1px solid #444;}
.header {text-align: center; font-size: 2.1rem; font-weight: 700; margin: 1rem 0;}
.footer {text-align: center; color: #666; padding: 1rem; font-size: 0.95rem;}
.watermark {position: fixed; bottom: 35%; left: 50%; transform: translateX(-50%); font-size: 9rem; opacity: 0.05; color: #fff; pointer-events: none; z-index: -1; user-select: none;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header">Warriors Don\'t Always Win — Warriors Always Fight</div>', unsafe_allow_html=True)
st.markdown('<div class="watermark">;∞</div>', unsafe_allow_html=True)

# === SESSION STATE ===
if 'phase' not in st.session_state:
    st.session_state.update({
        'phase': 0,
        'msgs': [],
        'exchange_count': 0,
        'crisis_active': False,
        '_advance_next': False,
        'client': None
    })

# === SIDEBAR CONTROLS ===
with st.sidebar:
    st.metric("Phase", st.session_state.phase)
    st.metric("Exchanges", st.session_state.exchange_count)
    
    api_key = st.text_input("xAI Grok API Key", type="password", key="xai_key")
    if api_key and (st.session_state.client is None or not st.session_state.client):
        st.session_state.client = OpenAI(base_url="https://api.x.ai/v1", api_key=api_key)
        st.success("Grok link established")
    
    if st.button("Advance Phase", disabled=st.session_state.exchange_count < 3):
        st.session_state._advance_next = True
        st.rerun()
    
    if st.session_state.phase == 3 and st.session_state.exchange_count >= 3:
        if st.button("**Close Session**"):
            st.session_state.phase = 0
            st.session_state.exchange_count = 0
            st.session_state.msgs = []
            st.session_state.crisis_active = False
            st.session_state._advance_next = False
            st.rerun()
    
    if st.button("Full Reset"):
        for k in list(st.session_state.keys()):
            if k != "client":
                del st.session_state[k]
        st.rerun()

# === CHAT RENDER ===
for msg in st.session_state.msgs:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# === INPUT & LOGIC ===
if prompt := st.chat_input("State the immediate fact..."):
    log_record(prompt, "user", st.session_state.phase)
    st.session_state.msgs.append({"role": "user", "content": prompt})
    st.session_state.exchange_count += 1

    # Crisis gate
    if contains_self_harm(prompt):
        st.session_state.crisis_active = True

    # Generate response
    if st.session_state.crisis_active:
        response = "Feet on ground. You are here. Name one physical object in the room. Call/Text 988 or Text HOME to 741741. I stand ready."
        st.session_state.crisis_active = False  # single-response ground
    else:
        phase_prompts = [MASTER_PROMPT, MIRROR_PROMPT, SENTINEL_PROMPT, CLOSURE_PROMPT]
        sys_prompt = phase_prompts[st.session_state.phase]
        
        client = st.session_state.get('client')
        if client:
            try:
                messages = [{"role": "system", "content": sys_prompt}] + \
                           [{"role": m["role"], "content": m["content"]} for m in st.session_state.msgs[-6:]]
                completion = client.chat.completions.create(
                    model="grok-beta",
                    messages=messages,
                    max_tokens=220,
                    temperature=0.35
                )
                response = completion.choices[0].message.content.strip()
            except Exception as e:
                response = f"Link stable. Fact: API transmission error - {str(e)[:60]}"
        else:
            response = f"Phase {st.session_state.phase} fact: Line acknowledged. {sys_prompt.split('.')[0]}."

    log_record(response, "assistant", st.session_state.phase)
    st.session_state.msgs.append({"role": "assistant", "content": response})

    # Phase gate
    if st.session_state.exchange_count >= 3:
        st.session_state._advance_next = True
    if st.session_state._advance_next and st.session_state.phase < 3:
        st.session_state.phase += 1
        st.session_state.exchange_count = 0
        st.session_state._advance_next = False

    st.rerun()

st.markdown('<div class="footer">We Never Quit</div>', unsafe_allow_html=True)
