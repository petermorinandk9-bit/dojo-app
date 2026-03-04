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
# AUTH
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

                res = supabase.table("users").select("*").eq("username", u_name).eq("password", u_pass).execute()

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
# LOAD HISTORY
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
# LOAD WISDOM
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
    "Student": ["Welcome","Warm-Up","Training","Cool Down"],
    "Practitioner": ["Welcome","Warm-Up","Training","Cool Down"],
    "Sentinel": ["Welcome","Warm-Up","Training","Cool Down"],
    "Sovereign": ["Welcome","Warm-Up","Training","Cool Down"]
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
# STYLE + DOJO CREST
# ==================================================
st.markdown("""
<style>

.stApp{
    background:#ffffff;
}

/* Watermark crest */

.stApp::before{
content:"";
position:fixed;
top:50%;
left:50%;
transform:translate(-50%,-50%);
width:700px;
height:700px;
opacity:0.05;
background-repeat:no-repeat;
background-size:contain;
z-index:-1;

background-image:url("data:image/svg+xml;utf8,
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 500 500'>
<circle cx='250' cy='250' r='230' stroke='black' stroke-width='6' fill='none'/>
<circle cx='250' cy='250' r='190' stroke='black' stroke-width='2' fill='none'/>

<text x='250' y='90' text-anchor='middle' font-size='18' font-family='serif'>
Warriors Don't Always Win - Warriors Always Fight
</text>

<text x='250' y='260' text-anchor='middle' font-size='42' font-weight='bold' font-family='serif'>
The-Dojo
</text>

<text x='250' y='420' text-anchor='middle' font-size='20' font-family='serif'>
We. Never. Quit.
</text>
</svg>");
}

[data-testid="stSidebar"]{
background:#f8f9fa;
border-right:1px solid #e0e0e0;
}

.active-item{
color:#000;
font-weight:800;
border-left:3px solid #000;
padding-left:20px;
margin-top:8px;
}

.inactive-item{
color:#bbb;
border-left:1px solid #eee;
padding-left:20px;
margin-top:5px;
}

.sidebar-dojo{
font-size:2.2rem!important;
font-weight:800;
font-style:italic;
margin-bottom:-10px;
}

.slogan-warrior{
font-size:1.1em;
text-align:center;
color:#888;
letter-spacing:2px;
text-transform:uppercase;
margin-top:20px;
}

.slogan-quit{
font-size:1.8em;
text-align:center;
color:#1a1a1a;
font-style:italic;
font-weight:800;
margin-bottom:10px;
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:

    st.markdown('<p class="sidebar-dojo">The-Dojo</p>', unsafe_allow_html=True)

    st.markdown(f"**{rank} · {USER_NAME}**")

    st.divider()

    for idx,p_name in enumerate(PHASE_SETS[rank]):
        style="active-item" if idx==st.session_state.phase else "inactive-item"
        st.markdown(f"<div class='{style}'>{p_name}</div>",unsafe_allow_html=True)

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
# CHAT INPUT
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

    MASTER_PROMPT=f"""
You are the Dojo Mentor for {USER_NAME}.

Observe patterns, acknowledge reality, and offer practical adjustments.

Rank: {rank}
Phase: {PHASE_SETS[rank][st.session_state.phase]}

End every response with
[MOOD: neutral/uplifting/melancholy/intense]
"""

    headers={"Authorization":f"Bearer {st.secrets['GROQ_API_KEY']}"}

    res=requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json={
            "model":"llama-3.3-70b-versatile",
            "messages":[{"role":"system","content":MASTER_PROMPT}]+st.session_state.msgs[-10:],
            "temperature":0.6
        },
        headers=headers
    )

    full_text=res.json()["choices"][0]["message"]["content"]

    clean_response=full_text.split("[MOOD:")[0].strip() if "[MOOD:" in full_text else full_text
    mood=full_text.split("[MOOD:")[1].split("]")[0].strip().lower() if "[MOOD:" in full_text else "neutral"

    st.session_state.mood=mood if mood in MOOD_MUSIC else "neutral"

    st.session_state.msgs.append({"role":"assistant","content":clean_response})

    if len(st.session_state.msgs)%4==0 and st.session_state.phase<3:
        st.session_state.phase+=1

    st.rerun()
