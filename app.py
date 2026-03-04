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
    .login-header {text-align:center;font-style:italic;font-weight:800;font-size:3.5rem;color:#1a1a1a;}
    .login-sub {text-align:center;color:#666;font-size:1.1rem;margin-bottom:30px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="login-header">The-Dojo</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-sub">Forge your discipline. Step onto the mat.</p>', unsafe_allow_html=True)

    tab_login, tab_signup, tab_manual = st.tabs(["Login","Create Account","The Manual"])

    with tab_login:
        with st.form("login_form"):

            u_name = st.text_input("Username").lower().strip()
            u_pass = st.text_input("Password", type="password")

            if st.form_submit_button("Enter the Dojo", use_container_width=True):

                res = supabase.table("users").select("*").eq("username",u_name).eq("password",u_pass).execute()

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
            st.session_state.msgs.append({"role": r["role"],"content": r["content"]})

    st.session_state.records_count = r_res.count if r_res.count else 0
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
# HISTORY TAB (NEW)
# ==================================================
tab_train, tab_history = st.tabs(["Training","History"])

# ==================================================
# HISTORY VIEW
# ==================================================
with tab_history:

    st.subheader("Training History")

    rec = supabase.table("records").select("*").eq("user_id",USER_ID).order("timestamp",desc=True).limit(50).execute()

    for r in rec.data:
        st.markdown(f"**{r['role']}** — {r['content']}")

    st.divider()

    st.subheader("Milestones")

    ms = supabase.table("dojo_milestones").select("*").eq("user_id",USER_ID).order("timestamp",desc=True).execute()
    for m in ms.data:
        st.write(m["milestone"])

    st.subheader("Patterns")

    pt = supabase.table("dojo_patterns").select("*").eq("user_id",USER_ID).order("timestamp",desc=True).execute()
    for p in pt.data:
        st.write(p["pattern"])

    st.subheader("Doctrine")

    dc = supabase.table("dojo_doctrine").select("*").eq("user_id",USER_ID).order("timestamp",desc=True).execute()
    for d in dc.data:
        st.write(d["doctrine"])

# ==================================================
# MAIN TRAINING
# ==================================================
with tab_train:

    for msg in st.session_state.msgs[-10:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

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

        # ==================================================
        # SESSION SUMMARY (12 line awareness trick)
        # ==================================================
        session_summary = " ".join(
            [m["content"] for m in st.session_state.msgs if m["role"]=="user"][-3:]
        )

        MASTER_PROMPT=f"""
You are the Dojo Mentor for {USER_NAME}.

SESSION SUMMARY
{session_summary}

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

        clean_response=full_text.split("[MOOD:")[0].strip()
        mood=full_text.split("[MOOD:")[1].split("]")[0].strip().lower()

        st.session_state.mood=mood

        st.session_state.msgs.append({"role":"assistant","content":clean_response})

        supabase.table("records").insert({
            "user_id":USER_ID,
            "timestamp":time.time(),
            "role":"assistant",
            "content":clean_response,
            "rank":rank,
            "phase":str(st.session_state.phase)
        }).execute()

        # ==================================================
        # MILESTONE CHECK
        # ==================================================
        new_rank = compute_rank(st.session_state.records_count + 1)

        if new_rank != rank:

            supabase.table("dojo_milestones").insert({
                "user_id":USER_ID,
                "timestamp":time.time(),
                "milestone":f"{new_rank} Rank Achieved"
            }).execute()

        if len(st.session_state.msgs)%4==0 and st.session_state.phase<3:
            st.session_state.phase+=1

        st.rerun()
