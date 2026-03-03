import streamlit as st
import sqlite3
import requests
import time

# ==================================================
# 1. CORE CONFIG & SOVEREIGN PROMPTS
# ==================================================
PHASE_SETS = {
    "Student": ["Welcome Mat", "Warm-Up", "Training", "Cool Down"],
    "Practitioner": ["Step Onto the Mat", "Feel It Out", "Work the Pattern", "Close the Round"],
    "Sentinel": ["Enter the Dojo", "Center", "Engage", "Seal & Step Out"],
    "Sovereign": ["Check-In", "Look Closer", "Name It", "Next Step"]
}

MASTER_PROMPT = """ROLE: Disciplined Warrior / Dojo Lead.
Observe the state without judgment. Name the immediate fact.
Minimalist. Strength in reserve. No 'inhale/exhale' fluff. Max 3 lines."""

MIRROR_PROMPT = """ROLE: Dojo Mirror (Semantic).
Reflect patterns/echoes with surgical precision. Hold the line.
No coaching. Just the truth. Identify the 'Shield' if present."""

CRISIS_PROMPT = """ROLE: Sensei (Emergency).
Ground the user in immediate physical facts.
ALWAYS include: Call/Text 988 or Text HOME to 741741."""

# ==================================================
# 2. ARCHWAY UI - LIGHT MODE (full CSS strip of dark theme)
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
   
    /* Semicolon-Infinity Watermark - adjusted for light background */
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
if '_advance_ready' not in st.session_state:
    st.session_state._advance_ready = False

# ==================================================
# 4. SIDEBAR: THE RANK PATH (exact logic retained, CSS updated)
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
    st.progress((st.session_state.phase + 1) / 4)
    st.markdown(f"**Exchanges:** {st.session_state.exchange_count}/3")
   
    if st.button("Reset Session"):
        for key in list(st.session_state.keys()):
            if key not in ["client"]:  # preserve any hidden client if present
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
# 6. USER INPUT + GROQ API (payload fixed - llama-3.3-70b-versatile + explicit clean messages array)
# ==================================================
if prompt := st.chat_input("Enter the Dojo..."):
    st.session_state.msgs.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # Safety Check (full keywords from blueprint)
    def is_crisis(text):
        keywords = ["cut myself", "self harm", "kill myself", "suicide", "end my life", "blade", "razor"]
        return any(kw in text.lower() for kw in keywords)

    # Dynamic System Prompt per phase
    if is_crisis(prompt):
        sys_msg = CRISIS_PROMPT
    elif st.session_state.phase >= 2:
        sys_msg = MIRROR_PROMPT
    else:
        sys_msg = MASTER_PROMPT

    # Clean messages array - system first, then full history (exact Groq/OpenAI format)
    messages = [{"role": "system", "content": sys_msg}]
    for m in st.session_state.msgs:
        messages.append({"role": m["role"], "content": m["content"]})

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets.get('GROQ_API_KEY', '')}"
    }
   
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.35,
        "max_tokens": 512
    }
   
    with st.chat_message("assistant"):
        try:
            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions", 
                headers=headers, 
                json=payload,
                timeout=25
            )
            res.raise_for_status()
            response = res.json()['choices'][0]['message']['content']
        except Exception as e:
            response = f"**System Alert:** Transmission issue. Groq returned: {str(e)[:120]}"

        st.markdown(response)
        
        # Log response
        st.session_state.msgs.append({"role": "assistant", "content": response})
        st.session_state.exchange_count += 1
       
        if st.session_state.exchange_count >= 3:
            st.session_state._advance_ready = True

    st.rerun()

# ==================================================
# 7. PHASE / RANK ADVANCEMENT (completion of truncated logic)
# ==================================================
if st.session_state.get('_advance_ready', False):
    st.divider()
    current_phases = PHASE_SETS.get(st.session_state.rank, PHASE_SETS["Student"])
    
    if st.session_state.phase < 3:
        next_label = current_phases[st.session_state.phase + 1]
        if st.button(f"Advance to {next_label}", type="primary"):
            st.session_state.phase += 1
            st.session_state.exchange_count = 0
            st.session_state._advance_ready = False
            st.rerun()
    else:
        # Advance Rank or close Sovereign
        ranks = ["Student", "Practitioner", "Sentinel", "Sovereign"]
        try:
            current_idx = ranks.index(st.session_state.rank)
            if current_idx < len(ranks) - 1:
                next_rank = ranks[current_idx + 1]
                if st.button(f"Advance to {next_rank} Rank", type="primary"):
                    st.session_state.rank = next_rank
                    st.session_state.phase = 0
                    st.session_state.exchange_count = 0
                    st.session_state._advance_ready = False
                    st.rerun()
            else:
                st.success("You have reached Sovereign. Session complete.")
                if st.button("Close & Reset"):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
        except:
            pass
