import streamlit as st
import sqlite3
import requests

# ==================================================
# 1. CORE CONFIG & "THE BALANCE" PROMPTS
# ==================================================
PHASE_SETS = {
    "Student": ["Welcome Mat", "Warm-Up", "Training", "Cool Down"],
    "Practitioner": ["Step Onto the Mat", "Feel It Out", "Work the Pattern", "Close the Round"],
    "Sentinel": ["Enter the Dojo", "Center", "Engage", "Seal & Step Out"],
    "Sovereign": ["Check-In", "Look Closer", "Name It", "Next Step"]
}

MASTER_PROMPT = """ROLE: Dojo Mentor. 
You are a supportive, conversational mentor and a caring listener.
CRITICAL RULES:
1. BALANCE: Write 1 to 2 conversational paragraphs. Let the response breathe, but do not write long essays.
2. AUTHENTIC EMPATHY: Validate their feelings naturally. Be warm and human. Do not sound like a cold machine, but avoid extreme cheerleading (no "Wow!" or "That's absolutely amazing!").
3. NO PARROTING: Do not just summarize or repeat what they said. Offer a grounded perspective or a shared thought, then ask a thoughtful, gentle question to keep the dialogue flowing naturally."""

MIRROR_PROMPT = """ROLE: Dojo Mirror.
Reflect on the user's words with conversational, genuine warmth.
CRITICAL RULES:
1. BALANCE: Write about 3 to 5 sentences. Keep it focused but human.
2. NO ECHOING: Don't just repeat their story back to them. Instead, gently point out the strength, emotion, or underlying pattern in what they are experiencing.
3. TONE: Speak like a wise, caring friend who is listening deeply. Hold space, offer quiet validation, and be present."""

CRISIS_PROMPT = """ROLE: Sensei (Emergency).
Ground the user gently and safely in the present moment. Short, factual, calming sentences.
ALWAYS include: Call/Text 988 or Text HOME to 741741."""

# ==================================================
# 2. ARCHWAY UI - LIGHT MODE & HIERARCHY
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
    
    /* Rank Path */
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

    /* Phase Path */
    .active-phase { 
        color: #000000; 
        font-weight: 600; 
        font-size: 1.15em; 
        margin-bottom: 2px;
        padding-left: 10px;
    }
    .inactive-phase { 
        color: #888888; 
        font-size: 1.0em; 
        margin-bottom: 2px;
        padding-left: 10px;
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
# 4. SIDEBAR: THE RANK & PHASE PATH
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
    
    st.markdown(f"<br><span style='color: #666; font-size: 0.9em;'>Exchanges: {st.session_state.exchange_count}/3</span>", unsafe_allow_html=True)
    
    st.divider()

    if st.button("Bow-Out"):
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
        st.markdown(msg["content"])

# ==================================================
# 6. USER INPUT, GROQ API & AUTO-ADVANCE
# ==================================================
if prompt := st.chat_input("Enter the Dojo..."):
    st.session_state.msgs.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    def is_crisis(text):
        keywords = ["cut myself", "self harm", "kill myself", "suicide", "end my life", "blade", "razor"]
        return any(kw in text.lower() for kw in keywords)

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
        "messages": messages,
        "temperature": 0.45, # Bumped up slightly to allow natural phrasing
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
        
        st.session_state.msgs.append({"role": "assistant", "content": response})
        st.session_state.exchange_count += 1
        
        # --- THE AUTO-ADVANCE WELD ---
        if st.session_state.exchange_count >= 3:
            st.session_state.exchange_count = 0
            
            if st.session_state.phase < 3:
                st.session_state.phase += 1
            else:
                st.session_state.phase = 0
                ranks = ["Student", "Practitioner", "Sentinel", "Sovereign"]
                try:
                    current_idx = ranks.index(st.session_state.rank)
                    if current_idx < len(ranks) - 1:
                        st.session_state.rank = ranks[current_idx + 1]
                except ValueError:
                    pass

    st.rerun()
