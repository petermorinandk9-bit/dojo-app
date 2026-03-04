import streamlit as st
import requests
import time
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

# ==================================================
# USER INFO
# ==================================================
USER_ID = st.session_state.user["id"]
USER_NAME = st.session_state.user["display_name"]

# ==================================================
# SESSION STATE
# ==================================================
if "msgs" not in st.session_state:
    st.session_state.msgs = []
    st.session_state.phase = 0
    st.session_state.mood = "neutral"

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
# PHASES
# ==================================================
PHASE_SETS = {
    "Student":["Welcome","Warm-Up","Training","Cool Down"],
    "Practitioner":["Welcome","Warm-Up","Training","Cool Down"],
    "Sentinel":["Welcome","Warm-Up","Training","Cool Down"],
    "Sovereign":["Welcome","Warm-Up","Training","Cool Down"]
}

# ==================================================
# STYLE
# ==================================================
st.markdown("""
<style>

.stApp{background:#fff;color:#1a1a1a}

[data-testid="stSidebar"]{
background:#f8f9fa;
border-right:1px solid #e0e0e0
}

.active-item{
color:#000;
font-weight:800;
border-left:3px solid #000;
padding-left:20px;
margin-top:8px
}

.inactive-item{
color:#bbb;
border-left:1px solid #eee;
padding-left:20px;
margin-top:5px
}

.sidebar-dojo{
font-size:2.2rem!important;
font-weight:800;
font-style:italic;
margin-bottom:-10px
}

.slogan-warrior{
font-size:1.1em;
text-align:center;
color:#888;
letter-spacing:2px;
text-transform:uppercase;
margin-top:20px
}

.slogan-quit{
font-size:1.8em;
text-align:center;
color:#1a1a1a;
font-style:italic;
font-weight:800;
margin-bottom:10px
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

    for i,p in enumerate(PHASE_SETS[rank]):

        style = "active-item" if i == st.session_state.phase else "inactive-item"

        st.markdown(
            f"<div class='{style}'>{p}</div>",
            unsafe_allow_html=True
        )

# ==================================================
# TABS
# ==================================================
tab_train, tab_history = st.tabs(["Training","History"])

# ==================================================
# HISTORY TAB
# ==================================================
with tab_history:

    st.subheader("Milestones")

    try:
        ms = supabase.table("dojo_milestones")\
            .select("*")\
            .eq("user_id", USER_ID)\
            .order("timestamp", desc=True)\
            .execute()

        if ms.data:
            for m in ms.data:
                st.write(m["milestone"])
    except:
        pass

    st.subheader("Patterns")

    try:
        pt = supabase.table("dojo_patterns")\
            .select("*")\
            .eq("user_id", USER_ID)\
            .order("timestamp", desc=True)\
            .execute()

        if pt.data:
            for p in pt.data:
                st.write(p["pattern"])
    except:
        pass

    st.subheader("Doctrine")

    try:
        dc = supabase.table("dojo_doctrine")\
            .select("*")\
            .eq("user_id", USER_ID)\
            .order("timestamp", desc=True)\
            .execute()

        if dc.data:
            for d in dc.data:
                st.write(d["doctrine"])
    except:
        pass

# ==================================================
# TRAINING TAB
# ==================================================
with tab_train:

    st.markdown(
        "<p class='slogan-warrior'>Warriors Don't Always Win — Warriors Always Fight.</p>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p class='slogan-quit'>We. Never. Quit.</p>",
        unsafe_allow_html=True
    )

    for msg in st.session_state.msgs[-10:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Speak from center..."):

        st.session_state.msgs.append({
            "role":"user",
            "content":prompt
        })

        supabase.table("records").insert({
            "user_id":USER_ID,
            "timestamp":time.time(),
            "role":"user",
            "content":prompt,
            "rank":rank,
            "phase":str(st.session_state.phase)
        }).execute()

        # session awareness trick
        session_summary = " ".join(
            [m["content"] for m in st.session_state.msgs if m["role"]=="user"][-3:]
        )

        MASTER_PROMPT = f"""
You are the Dojo Mentor for {USER_NAME}.

Session summary:
{session_summary}

Offer grounded reflection and practical guidance.

Rank: {rank}
Phase: {PHASE_SETS[rank][st.session_state.phase]}

End with
[MOOD: neutral/uplifting/melancholy/intense]
"""

        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}

        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "model":"llama-3.3-70b-versatile",
                "messages":[{"role":"system","content":MASTER_PROMPT}] + st.session_state.msgs[-10:],
                "temperature":0.6
            },
            headers=headers
        )

        full = res.json()["choices"][0]["message"]["content"]

        clean = full.split("[MOOD:")[0].strip()

        st.session_state.msgs.append({
            "role":"assistant",
            "content":clean
        })

        supabase.table("records").insert({
            "user_id":USER_ID,
            "timestamp":time.time(),
            "role":"assistant",
            "content":clean,
            "rank":rank,
            "phase":str(st.session_state.phase)
        }).execute()

        if len(st.session_state.msgs) % 4 == 0 and st.session_state.phase < 3:
            st.session_state.phase += 1

        st.rerun()
