import streamlit as st
import requests
import time
import random
from supabase import create_client, Client

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="The-Dojo", layout="wide")

# ==================================================
# CONNECTION
# ==================================================
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_supabase()

# ==================================================
# RANK SYSTEM
# ==================================================
def compute_rank(count):
    if count < 15:
        return "Student"
    if count < 40:
        return "Practitioner"
    if count < 80:
        return "Sentinel"
    return "Sovereign"

# ==================================================
# AUTH
# ==================================================
if "user" not in st.session_state:
    st.markdown("""
    <style>
    .stApp {background:#ffffff;}
    .login-header{text-align:center;font-style:italic;font-weight:800;font-size:3.5rem;}
    .login-sub{text-align:center;color:#666;margin-bottom:30px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="login-header">The-Dojo</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-sub">Forge your discipline. Step onto the mat.</p>', unsafe_allow_html=True)

    with st.form("login"):
        u = st.text_input("Username").lower().strip()
        p = st.text_input("Password", type="password")

        if st.form_submit_button("Enter the Dojo"):
            res = supabase.table("users")\
                .select("*")\
                .eq("username", u)\
                .eq("password", p)\
                .execute()

            if res.data:
                st.session_state.user = res.data[0]
                st.rerun()
            else:
                st.error("Credentials not recognized")

    st.stop()

USER_ID = st.session_state.user["id"]
USER_NAME = st.session_state.user["display_name"]

# ==================================================
# SESSION STATE
# ==================================================
if "msgs" not in st.session_state:
    st.session_state.msgs = []
    st.session_state.phase = 0

# ==================================================
# LOAD HISTORY
# ==================================================
if "history_loaded" not in st.session_state:
    r = supabase.table("records")\
        .select("*", count="exact")\
        .eq("user_id", USER_ID)\
        .order("timestamp")\
        .execute()

    if r.data:
        for row in r.data:
            st.session_state.msgs.append({
                "role": row["role"],
                "content": row["content"]
            })

    st.session_state.records_count = r.count if r.count else 0
    st.session_state.history_loaded = True

rank = compute_rank(st.session_state.records_count)

# ==================================================
# FETCH DOJO MEMORY
# ==================================================
def fetch_latest(table, field):
    try:
        r = supabase.table(table)\
            .select("*")\
            .eq("user_id", USER_ID)\
            .order("timestamp", desc=True)\
            .limit(1)\
            .execute()

        if r.data:
            return r.data[0][field]
    except:
        pass

    return None

latest_pattern = fetch_latest("dojo_patterns", "pattern")
latest_doctrine = fetch_latest("dojo_doctrine", "doctrine")
latest_milestone = fetch_latest("dojo_milestones", "milestone")

# ==================================================
# PHASES
# ==================================================
PHASE_SETS = {
    "Student":["Welcome","Warm-Up","Training","Cool Down"],
    "Practitioner":["Welcome","Warm-Up","Training","Cool Down"],
    "Sentinel":["Welcome","Warm-Up","Training","Cool Down"],
    "Sovereign":["Welcome","Warm-Up","Training","Cool Down"]
}

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:
    st.markdown("### The-Dojo")
    st.markdown(f"**{rank} · {USER_NAME}**")
    st.divider()

    for i,p in enumerate(PHASE_SETS[rank]):
        if i == st.session_state.phase:
            st.markdown(f"**{p}**")
        else:
            st.markdown(p)

    st.divider()

    if st.button("Bow Out"):
        st.session_state.phase = 0
        st.session_state.msgs = []
        st.success("You bow out from the mat. Training continues tomorrow.")
        time.sleep(1)
        st.rerun()

# ==================================================
# TABS
# ==================================================
tab_train, tab_history = st.tabs(["Training","History"])

# ==================================================
# TRAINING
# ==================================================
with tab_train:
    # ===============================
    # DOJO AWARENESS BANNER
    # ===============================
    with st.container():
        st.markdown("### Dojo Awareness")
        if latest_pattern:
            st.write(f"**Current Pattern:** {latest_pattern}")
        if latest_doctrine:
            st.write(f"**Recent Doctrine:** {latest_doctrine}")
        if latest_milestone:
            st.write(f"**Recent Milestone:** {latest_milestone}")
        st.write(f"**Current Phase:** {PHASE_SETS[rank][st.session_state.phase]}")
        st.divider()

    # ===============================
    # CHAT HISTORY
    # ===============================
    for msg in st.session_state.msgs[-10:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ===============================
    # ASSISTANT RESPONSE (when processing)
    # ===============================
    if prompt := st.chat_input("Speak from center..."):
        st.session_state.msgs.append({
            "role":"user",
            "content":prompt
        })

        session_summary = " ".join(
            [m["content"] for m in st.session_state.msgs if m["role"]=="user"][-3:]
        )

        # ===============================
        # RANK STYLE
        # ===============================
        rank_style = {
            "Student":"supportive instructor who explains ideas clearly",
            "Practitioner":"focused coach giving practical guidance",
            "Sentinel":"reflective strategist who points out patterns",
            "Sovereign":"minimalist mentor who guides through questions"
        }

        # ===============================
        # MASTER PROMPT
        # ===============================
        MASTER_PROMPT = f"""
You are a calm, grounded, perceptive human mentor speaking to {USER_NAME}.
Mentor style: {rank_style[rank]}
LONG-TERM MEMORY:
Pattern: {latest_pattern}
Doctrine: {latest_doctrine}
Milestone: {latest_milestone}
(Weave these quietly into your understanding. Never name or point to them directly.)
RECENT CONTEXT:
Session summary: {session_summary}
YOUR OBJECTIVE:
Offer a steady, outside perspective that helps the person notice what they may not yet see clearly — without praising, fixing, or directing.
STRICT COMMUNICATION RULES:
• Look past the surface story to the underlying tension, hesitation, or quiet assumption.
• Never repeat, mirror, echo, or rephrase anything the user said.
• No therapy phrasing, no "I hear," no "it sounds like," no emotional validation.
• Avoid motivational language, pep talks, slogans, corporate-speak.
• No martial arts imagery, dojo references, or teacher–student posturing.
• Speak like a thoughtful, experienced adult — plain, calm, direct, human.
• Match response length to the depth and weight of what the user shared: brief and light for casual or surface-level inputs, longer and more considered (up to 10–12 sentences) only when the reflection is deeper, more personal, or carries real emotional or existential weight. Avoid unnecessary length. Let proportion guide you.
CURRENT STATE:
Rank: {rank}
Phase: {PHASE_SETS[rank][st.session_state.phase]}
"""

        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "model":"llama-3.3-70b-versatile",
                "messages":[{"role":"system","content":MASTER_PROMPT}] + st.session_state.msgs[-10:]
            },
            headers=headers
        )
        reply = res.json()["choices"][0]["message"]["content"]

        thinking_phrases = [
            "Let me think a moment…",
            "Give me a moment to consider this…",
            "Let me reflect on that for a second…",
            "One moment while I think about that…",
            "Let me consider that carefully…"
        ]
        selected_phrase = random.choice(thinking_phrases)

        # Gradual reveal with contemplation first
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown(selected_phrase)

            # Initial contemplation delay
            time.sleep(2.0)

            # Dynamic thinking pause
            char_delay = min(len(reply) / 120, 4)
            time.sleep(char_delay)

            # Reveal response sentence by sentence
            current_text = ""
            sentences = reply.split(". ")
            for i, sentence in enumerate(sentences):
                if i > 0:
                    current_text += ". "
                current_text += sentence
                if i == len(sentences) - 1 and not sentence.endswith("."):
                    current_text += "."
                message_placeholder.markdown(current_text)
                if i < len(sentences) - 1:
                    time.sleep(0.6)

        st.session_state.msgs.append({
            "role":"assistant",
            "content":reply
        })

        if len(st.session_state.msgs) % 4 == 0 and st.session_state.phase < 3:
            st.session_state.phase += 1

        st.rerun()
