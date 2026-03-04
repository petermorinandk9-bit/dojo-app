import streamlit as st
import requests
import time
from supabase import create_client, Client

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="The-Dojo", layout="wide")

# ==================================================
# CONNECTIONS
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
def compute_rank(records_count):
    if records_count < 15: return "Student"
    if records_count < 40: return "Practitioner"
    if records_count < 80: return "Sentinel"
    return "Sovereign"

# ==================================================
# RANK ADAPTIVE MENTOR STYLE
# ==================================================
def mentor_style(rank):

    styles = {
        "Student": "Supportive, guiding, and clarifying.",
        "Practitioner": "Balanced between guidance and challenge.",
        "Sentinel": "More analytical and pattern-aware.",
        "Sovereign": "Direct, reflective, and ownership-focused."
    }

    return styles.get(rank, "Balanced and observant.")

# ==================================================
# AUTH GATE
# ==================================================
if 'user' not in st.session_state:

    st.markdown("""
        <style>
        .stApp { background-color: #ffffff; }
        .login-header { text-align: center; font-style: italic; font-weight: 800; font-size: 3.5rem; color: #1a1a1a; margin-bottom: 0px; }
        .login-sub { text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 30px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="login-header">The-Dojo</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-sub">Forge your discipline. Step onto the mat.</p>', unsafe_allow_html=True)

    tab_login, tab_signup, tab_manual = st.tabs(["Login", "Create Account", "The Manual"])

    with tab_login:
        with st.form("login_form"):

            u_name = st.text_input("Username").lower().strip()
            u_pass = st.text_input("Password", type="password")

            if st.form_submit_button("Enter the Dojo", use_container_width=True):

                res = supabase.table("users").select("*")\
                    .eq("username", u_name)\
                    .eq("password", u_pass)\
                    .execute()

                if res.data:
                    st.session_state.user = res.data[0]
                    st.rerun()
                else:
                    st.error("Credentials not recognized.")

    with tab_signup:
        with st.form("signup_form"):

            new_name = st.text_input("Choose Username").lower().strip()
            display_n = st.text_input("Your Name (Display Name)")
            new_pass = st.text_input("Choose Password", type="password")
            invite_c = st.text_input("Dojo Invite Code", type="password")

            if st.form_submit_button("Join the Dojo", use_container_width=True):

                if invite_c != "dojoentry":
                    st.error("Invalid Invite Code.")

                elif not new_name or not new_pass:
                    st.warning("All fields required.")

                else:
                    user_data = {
                        "username": new_name,
                        "password": new_pass,
                        "display_name": display_n
                    }

                    new_user = supabase.table("users").insert(user_data).execute()

                    if new_user.data:
                        st.session_state.user = new_user.data[0]
                        st.rerun()

    with tab_manual:

        st.subheader("1. THE RITUAL")
        st.write("The Dojo is a sanctuary for focused reflection. Speak from center. Be honest.")
        st.info("**2. THE PRIVACY VOW**\n\nYour training is your own. This is your safe space.")

    st.stop()

# ==================================================
# SESSION
# ==================================================
USER_ID = st.session_state.user['id']
USER_NAME = st.session_state.user['display_name']

if 'msgs' not in st.session_state:
    st.session_state.msgs = []
    st.session_state.phase = 0
    st.session_state.mood = "neutral"

# ==================================================
# LOAD HISTORY
# ==================================================
if "history_loaded" not in st.session_state:

    r_res = supabase.table("records")\
        .select("*", count="exact")\
        .eq("user_id", USER_ID)\
        .order("timestamp")\
        .execute()

    if r_res.data:
        for r in r_res.data[-50:]:
            st.session_state.msgs.append({
                "role": r['role'],
                "content": r['content']
            })

    st.session_state.records_count = r_res.count if r_res.count else 0
    st.session_state.history_loaded = True

rank = compute_rank(st.session_state.records_count)

# ==================================================
# PATTERN ENGINE (multiple wisdom entries)
# ==================================================
wisdom_res = supabase.table("ledger_wisdom")\
    .select("summary")\
    .eq("user_id", USER_ID)\
    .order("timestamp", desc=True)\
    .limit(5)\
    .execute()

WISDOM_BLOCK = ""

if wisdom_res.data:
    for w in wisdom_res.data:
        WISDOM_BLOCK += f"- {w['summary']}\n"

else:
    WISDOM_BLOCK = "No patterns recorded yet."

# ==================================================
# PHASES
# ==================================================
PHASE_SETS = {
    "Student": ["Welcome Mat", "Warm Up", "Training", "Cool Down"],
    "Practitioner": ["The Mat", "Work the Pattern", "The Insight", "Close Round"],
    "Sentinel": ["Center", "Engage", "The Seal", "Reflection"],
    "Sovereign": ["Check-In", "The Pivot", "Ownership", "Step Out"]
}

MOOD_MUSIC = {
    "neutral": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
    "uplifting": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "melancholy": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
    "intense": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3"
}

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:

    st.markdown("### The-Dojo")
    st.write(f"Participant: **{USER_NAME}**")

    st.divider()

    st.markdown(f"**Rank:** {rank}")

    for idx, p_name in enumerate(PHASE_SETS[rank]):
        marker = "▶" if idx == st.session_state.phase else "•"
        st.write(f"{marker} {p_name}")

    st.divider()

    # ==================================================
    # REFLECTION ENGINE
    # ==================================================
    if st.button("Bow-Out", use_container_width=True):

        session_text = "\n".join([m["content"] for m in st.session_state.msgs[-10:]])

        reflection_prompt = f"""
Summarize the key insight from this reflection session in one concise sentence.

Conversation:
{session_text}
"""

        try:

            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": reflection_prompt}],
                    "temperature": 0.3
                },
                headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
            )

            insight = res.json()['choices'][0]['message']['content']

            supabase.table("ledger_wisdom").insert({
                "user_id": USER_ID,
                "timestamp": time.time(),
                "summary": insight
            }).execute()

        except Exception:
            pass

        st.session_state.msgs = []
        st.session_state.phase = 0
        st.rerun()

# ==================================================
# MAIN UI
# ==================================================
st.markdown("### Warriors Don't Always Win — Warriors Always Fight")
st.markdown("## We. Never. Quit.")

st.audio(MOOD_MUSIC[st.session_state.mood], format="audio/mp3", loop=True)

for msg in st.session_state.msgs[-10:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==================================================
# USER INPUT
# ==================================================
if prompt := st.chat_input("Speak from center..."):

    st.session_state.msgs.append({"role": "user", "content": prompt})

    supabase.table("records").insert({
        "user_id": USER_ID,
        "timestamp": time.time(),
        "role": "user",
        "content": prompt,
        "rank": rank,
        "phase": str(st.session_state.phase)
    }).execute()

    MASTER_PROMPT = f"""
IDENTITY
Sovereign Mentor. A seasoned training partner for {USER_NAME}.

MENTOR STYLE
{mentor_style(rank)}

PATTERN MEMORY
Recent long-term patterns observed:
{WISDOM_BLOCK}

INTERPRETATION RULE
Do not mirror the user's wording.
Interpret the underlying situation and respond to that instead.

COMMUNICATION STYLE
Calm, direct, respectful. No therapy language. No corporate tone.

GROUNDING STYLE
Use grounding metaphors related to breath, focus, balance, and presence.

CURRENT STATE
Rank: {rank}
Phase: {PHASE_SETS[rank][st.session_state.phase]}
Depth: {len(st.session_state.msgs)} messages

END EVERY RESPONSE WITH:
[MOOD: neutral/uplifting/melancholy/intense]
"""

    try:

        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": MASTER_PROMPT}] + st.session_state.msgs[-10:],
                "temperature": 0.55
            },
            headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"},
            timeout=20
        )

        full_text = res.json()['choices'][0]['message']['content']

    except Exception:

        full_text = "Take a breath and try again. [MOOD: neutral]"

    clean_response = full_text
    mood = "neutral"

    if "[MOOD" in full_text:

        clean_response = full_text.split("[MOOD")[0].strip()

        try:
            mood_part = full_text.split("[MOOD")[1].split("]")[0]
            mood = mood_part.replace(":", "").strip().lower()
        except Exception:
            pass

    st.session_state.mood = mood if mood in MOOD_MUSIC else "neutral"

    st.session_state.msgs.append({"role": "assistant", "content": clean_response})

    supabase.table("records").insert({
        "user_id": USER_ID,
        "timestamp": time.time(),
        "role": "assistant",
        "content": clean_response,
        "rank": rank,
        "phase": str(st.session_state.phase)
    }).execute()

    if len(st.session_state.msgs) % 4 == 0 and st.session_state.phase < 3:
        st.session_state.phase += 1

    st.rerun()
