import streamlit as st
import sqlite3
import requests
import time

# ==================================================
# 1. CORE CONFIG & "SUPPORTIVE MENTOR" PROMPTS
# ==================================================
PHASE_SETS = {
    "Student": [
        "Welcome Mat", "Warm-Up", "Training", "Cool Down"
    ],
    "Practitioner": [
        "Step Onto the Mat", "Feel It Out", "Work the Pattern", "Close the Round"
    ],
    "Sentinel": [
        "Enter the Dojo", "Center", "Engage", "Seal & Step Out"
    ],
    "Sovereign": [
        "Check-In", "Look Closer", "Name It", "Next Step"
    ]
}

MASTER_PROMPT = (
    "ROLE: Dojo Mentor. \n"
    "You are a grounded, supportive guide. You are a mentor—not a soft therapist, and NOT a harsh sensei barking orders.\n"
    "CRITICAL RULES:\n"
    "1. CONVERSATIONAL LENGTH: Write 1 to 2 paragraphs. Adapt naturally to the depth of the user's input.\n"
    "2. GROUNDED TONE: Be supportive but not overly agreeable. Acknowledge their reality without using clinical therapy fluff (avoid 'I totally understand', 'process your emotions', 'valid').\n"
    "3. PATTERNS & SOLUTIONS: Base your responses on the flow of the conversation. Offer practical, grounded solutions or observations to their statements.\n"
    "4. FORWARD MOVEMENT: End by asking a thoughtful question to prompt growth—such as asking 'why', asking if they want to talk about it, or offering a tactical step."
)

MIRROR_PROMPT = (
    "ROLE: Dojo Mirror.\n"
    "Reflect the user's truth with supportive, grounded wisdom.\n"
    "CRITICAL RULES:\n"
    "1. CONCISE BUT HUMAN: Write about 1 short paragraph.\n"
    "2. TONE: Act as a wise mentor. Acknowledge the weight of their words without therapy fluff.\n"
    "3. INQUIRY: Point out an underlying pattern, then ask ONE probing question to help them look deeper or decide on an action."
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
# 3. DATABASE & PERSISTENT MEMORY
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

# --- STATE RECOVERY LOGIC ---
if 'msgs' not in st.session_state:
    st.session_state.msgs = []
    st.session_state.exchange_count = 0
    st.session_state.rank = "Student"
    st.session_state.phase = 0
    
    # Restore chat and exact rank/phase if the browser refreshes
    c = conn.cursor()
    c.execute("SELECT role, content, rank, phase FROM records ORDER BY timestamp ASC")
    rows = c.fetchall()
    for r in rows:
        st.session_state.msgs.append({"role": r[0], "content": r[1]})
    
    if rows:
        last_rank = rows[-1][2]
        last_phase = rows[-1][3]
        st.session_state.rank = last_rank
        try:
            st.session_state.phase = int(last_phase)
        except:
            st.session_state.phase = 0

# ==================================================
# 4. SIDEBAR LOGIC (True Session Reset)
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
        # Wipes the DB for a truly clean slate on reset
        c = conn.cursor()
        c.execute("DELETE FROM records")
        conn.commit()
        for key in list(st.session_state.keys()): del st.session_state[key]
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
# 6. ENGINE ROUTING & QUALITATIVE ADVANCEMENT
# ==================================================
if prompt := st.chat_input("Enter the Dojo..."):
    st.session_state.msgs.append({"role": "user", "content": prompt})
    save_to_ledger("user", prompt, st.session_state.rank, str(st.session_state.phase))
    st.session_state.exchange_count += 1
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- THE CRISIS GATEKEEPER ---
    def contains_self_harm(text):
        t = text.lower()
        keywords = ["cut myself", "self harm", "hurt myself", "kill myself", "suicide", "end my life", "blade", "razor"]
        return any(kw in t for kw in keywords)

    is_crisis = contains_self_harm(prompt)

    # --- THE QUALITATIVE GATEKEEPER (Fast 8B Model) ---
    def check_readiness(user_text):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {st.secrets.get('GROQ_API_KEY', '')}"
        }
        eval_prompt = (
            "Analyze this message. Is the user showing signs of forward growth, "
            "realization, closure, or readiness to move on? If they are still asking "
            "for guidance, venting, or stuck, reply NO. If they show a shift in "
            "perspective or readiness, reply YES. Reply ONLY with YES or NO."
        )
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": eval_prompt}, 
                {"role": "user", "content": user_text}
            ],
            "temperature": 0.0,
            "max_tokens": 5
        }
        try:
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=5)
            return "YES" in res.json()['choices'][0]['message']['content'].upper()
        except:
            return False

    with st.chat_message("assistant"):
        if is_crisis:
            safety_box = (
                "I am here with you, but I cannot provide guidance or assistance related to self-harm."
                "<div class='crisis-box'>"
                "<p class='crisis-text'>Immediate support is available right now. You are not alone.</p>"
                "<ul>"
                "<li>Call or text <strong>988</strong> (Suicide & Crisis Lifeline, 24/7, free & confidential)</li>"
                "<li>Text <strong>HOME</strong> to <strong>741741</strong> (Crisis Text Line, 24/7)</li>"
                "</ul>"
                "</div>"
            )
            st.markdown(safety_box, unsafe_allow_html=True)
            st.session_state.msgs.append({"role": "assistant", "content": safety_box})
            save_to_ledger("assistant", safety_box, st.session_state.rank, str(st.session_state.phase))

        else:
            # --- DOJO RESPONSE GENERATION ---
            sys_msg = MIRROR_PROMPT if st.session_state.phase >= 2 else MASTER_PROMPT

            # Load system prompt, then append only the last 30 messages to keep the AI focused
            messages = [{"role": "system", "content": sys_msg}]
            for m in st.session_state.msgs[-30:]:
                messages.append({"role": m["role"], "content": m["content"]})

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {st.secrets.get('GROQ_API_KEY', '')}"
            }
            
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.45,
                "max_tokens": 512
            }
            
            try:
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=25)
                res.raise_for_status()
                final_response = res.json()['choices'][0]['message']['content']
            except Exception as e:
                final_response = f"**System Alert:** Transmission issue. Groq returned: {str(e)[:120]}"

            st.markdown(final_response)
            st.session_state.msgs.append({"role": "assistant", "content": final_response})
            save_to_ledger("assistant", final_response, st.session_state.rank, str(st.session_state.phase))
            
            # --- ADVANCEMENT EVALUATION ---
            if st.session_state.exchange_count >= 2:
                is_ready = check_readiness(prompt)
                if is_ready or st.session_state.exchange_count >= 6:
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
