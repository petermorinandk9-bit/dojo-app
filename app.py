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
# AUTH GATE
# ==================================================
if 'user' not in st.session_state:

    st.markdown("""
    <style>
    .stApp { background:#ffffff; }
    .login-header {
        text-align:center;
        font-style:italic;
        font-weight:800;
        font-size:3.5rem;
        color:#1a1a1a;
        margin-bottom:0px;
    }
    .login-sub {
        text-align:center;
        color:#666;
        font-size:1.1rem;
        margin-bottom:30px;
    }
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

                res = supabase.table("users")\
                    .select("*")\
                    .eq("username", u_name)\
                    .eq("password", u_pass)\
                    .execute()

                if res.data:
                    st.session_state.user = res.data[0]
                    st.rerun()
                else:
                    st.error("Credentials not recognized.")

    with tab_manual:
        st.subheader("1. THE RITUAL")
        st.write("The Dojo is a sanctuary for focused reflection. Speak from center. Be honest.")
        st.info("**2. THE PRIVACY VOW**\n\nYour training is your own. This is your safe space.")

    st.stop()

# ==================================================
# SESSION INIT
# ==================================================
USER_ID = st.session_state.user["id"]
USER_NAME = st.session_state.user["display_name"]

if "msgs" not in st.session_state:
    st.session_state.msgs = []
    st.session_state.phase = 0
    st.session_state.mood = "neutral"

# ==================================================
# LOAD HISTORY ONCE
# ==================================================
if "history_loaded" not in st.session_state:

    r_res = supabase.table("records")\
        .select("*", count="exact")\
        .eq("user_id", USER_ID)\
        .order("timestamp")\
        .execute()

    if r_res.data:
        for r in r_res.data:
            st.session_state.msgs.append({
                "role": r["role"],
                "content": r["content"]
            })

    st.session_state.records_count = r_res.count if r_res.count else 0
    st.session_state.history_loaded = True

# ==================================================
# LOAD LONG TERM WISDOM
# ==================================================
if "past_wisdom" not in st.session_state:

    wisdom_res = supabase.table("ledger_wisdom")\
        .select("summary")\
        .eq("user_id", USER_ID)\
        .order("timestamp", desc=True)\
        .limit(1)\
        .execute()

    st.session_state.past_wisdom = wisdom_res.data[0]["summary"] if wisdom_res.data else "No past records yet."

PAST_WISDOM = st.session_state.past_wisdom
rank = compute_rank(st.session_state.records_count)

# ==================================================
# PHASES
# ==================================================
PHASE_SETS = {
    "Student": ["Welcome Mat","Warm Up","Training","Cool Down"],
    "Practitioner": ["The Mat","Work the Pattern","The Insight","Close Round"],
    "Sentinel": ["Center","Engage","The Seal","Reflection"],
    "Sovereign": ["Check-In","The Pivot","Ownership","Step Out"]
}

# ==================================================
# MUSIC
# ==================================================
MOOD_MUSIC = {
    "neutral":"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
    "uplifting":"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "melancholy":"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
    "intense":"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3"
}

# ==================================================
# STYLE
# ==================================================
st.markdown("""
<style>
.stApp{background:#fff;color:#1a1a1a}
[data-testid="stSidebar"]{background:#f8f9fa;border-right:1px solid #e0e0e0}
.active-item{color:#000;font-weight:800;border-left:3px solid #000;padding-left:20px;margin-top:8px}
.inactive-item{color:#bbb;border-left:1px solid #eee;padding-left:20px;margin-top:5px}
.sidebar-header{font-size:.85em;color:#999;text-transform:uppercase;letter-spacing:1.5px;margin-top:25px}
.sidebar-dojo{font-size:2.2rem!important;font-weight:800;font-style:italic;margin-bottom:-10px}
.slogan-warrior{font-size:1.1em;text-align:center;color:#888;letter-spacing:2px;text-transform:uppercase;margin-top:20px}
.slogan-quit{font-size:1.8em;text-align:center;color:#1a1a1a;font-style:italic;font-weight:800;margin-bottom:10px}
</style>
""", unsafe_allow_html=True)

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:

    st.markdown('<p class="sidebar-dojo">The-Dojo</p>', unsafe_allow_html=True)
    st.write(f"Participant: **{USER_NAME}**")

    st.divider()

    st.markdown(f'<p class="sidebar-header">Rank: {rank}</p>', unsafe_allow_html=True)

    for idx,p_name in enumerate(PHASE_SETS[rank]):
        style="active-item" if idx==st.session_state.phase else "inactive-item"
        st.markdown(f"<div class='{style}'>{p_name}</div>",unsafe_allow_html=True)

    st.divider()

    if st.button("Bow-Out", use_container_width=True):

        convo = "\n".join([
            f"{m['role']}: {m['content']}"
            for m in st.session_state.msgs[-20:]
        ])

        INSIGHT_PROMPT = f"""
Extract durable insights from this reflection session.

Conversation:
{convo}

Rules:
- Do not summarize the conversation
- Identify thinking patterns or tendencies
- Write 3–5 short insight sentences
"""

        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}

        try:

            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json={
                    "model":"llama-3.3-70b-versatile",
                    "messages":[{"role":"system","content":INSIGHT_PROMPT}],
                    "temperature":0.3
                },
                headers=headers,
                timeout=20
            )

            res.raise_for_status()

            insight = res.json()["choices"][0]["message"]["content"]

            supabase.table("ledger_wisdom").insert({
                "user_id":USER_ID,
                "timestamp":time.time(),
                "summary":insight
            }).execute()

        except Exception:
            pass

        st.session_state.msgs=[]
        st.session_state.phase=0
        st.rerun()

# ==================================================
# MAIN UI
# ==================================================
st.markdown("<p class='slogan-warrior'>Warriors Don't Always Win — Warriors Always Fight.</p>",unsafe_allow_html=True)
st.markdown("<p class='slogan-quit'>We. Never. Quit.</p>",unsafe_allow_html=True)

st.audio(MOOD_MUSIC[st.session_state.mood],format="audio/mp3",loop=True)

for msg in st.session_state.msgs[-10:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==================================================
# USER INPUT
# ==================================================
if prompt := st.chat_input("Speak from center..."):

    st.session_state.msgs.append({"role":"user","content":prompt})

    supabase.table("records").insert({
        "user_id":USER_ID,
        "timestamp":time.time(),
        "role":"user",
        "content":prompt,
        "rank":rank,
        "phase":str(st.session_state.phase)
    }).execute()

    # anti repetition memory
    recent_guidance="\n".join(
        [m["content"][:120] for m in st.session_state.msgs if m["role"]=="assistant"][-3:]
    )

    # session awareness
    session_length=len(st.session_state.msgs)

    if session_length<6:
        session_stage="Opening"
    elif session_length<16:
        session_stage="Working"
    else:
        session_stage="Closing"

    MASTER_PROMPT=f"""
IDENTITY
You are the Dojo Mentor for {USER_NAME}. Calm, observant, grounded.

Take a moment to consider the situation before responding.

LONG TERM TRAINING NOTES
{PAST_WISDOM}

RECENT GUIDANCE
Avoid repeating these ideas.
{recent_guidance}

SESSION STATE
Session length: {session_length}
Session stage: {session_stage}

Adjust tone naturally:
Opening → explore
Working → analyze
Closing → highlight insights

THE SOVEREIGN APPROACH
1. Observe the pattern
2. Acknowledge reality
3. Offer a practical adjustment

COMMUNICATION STYLE
Calm, direct, no therapy language, no corporate motivation.

INTERPRETATION RULE
Respond to meaning, not wording.

Use grounding metaphors: breath, focus, balance, pacing.

CURRENT STATE
Rank: {rank}
Phase: {PHASE_SETS[rank][st.session_state.phase]}

END EVERY RESPONSE WITH
[MOOD: neutral/uplifting/melancholy/intense]
"""

    headers={"Authorization":f"Bearer {st.secrets['GROQ_API_KEY']}"}

    try:

        res=requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "model":"llama-3.3-70b-versatile",
                "messages":[{"role":"system","content":MASTER_PROMPT}]+st.session_state.msgs[-10:],
                "temperature":0.6
            },
            headers=headers,
            timeout=20
        )

        res.raise_for_status()

        full_text=res.json()["choices"][0]["message"]["content"]

    except Exception:

        full_text="The Mentor pauses for a moment. Take a breath and try again. [MOOD: neutral]"

    clean_response=full_text.split("[MOOD:")[0].strip() if "[MOOD:" in full_text else full_text
    mood=full_text.split("[MOOD:")[1].split("]")[0].strip().lower() if "[MOOD:" in full_text else "neutral"

    st.session_state.mood=mood if mood in MOOD_MUSIC else "neutral"

    st.session_state.msgs.append({"role":"assistant","content":clean_response})

    supabase.table("records").insert({
        "user_id":USER_ID,
        "timestamp":time.time(),
        "role":"assistant",
        "content":clean_response,
        "rank":rank,
        "phase":str(st.session_state.phase)
    }).execute()

    if len(st.session_state.msgs)%4==0 and st.session_state.phase<3:
        st.session_state.phase+=1

    st.rerun()
