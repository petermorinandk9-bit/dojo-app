import streamlit as st
import requests
import time
import json
import bcrypt
import random
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, UTC
from supabase import create_client, Client

# ==================================================
# CONFIG
# ==================================================

st.set_page_config(page_title="The-Dojo", layout="wide")

# ==================================================
# IMPORTANT NOTICE
# ==================================================

IMPORTANT_NOTICE = """
### Important Notice

The Dojo is a reflection and personal development tool designed to support mindfulness, discipline, and self-awareness.

It is **not a medical or mental health service**, and the guidance provided by the system should not be considered professional advice, diagnosis, or treatment.

If you are experiencing severe emotional distress or thoughts of self-harm, please seek support from a qualified professional.

**United States:** Call or text **988** (Suicide & Crisis Lifeline)

By continuing to use The Dojo, you acknowledge these limitations and accept responsibility for how you use the system.
"""

# ==================================================
# SUPABASE CONNECTION
# ==================================================

@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_supabase()

# ==================================================
# SESSION STATE
# ==================================================

if "user" not in st.session_state:
    st.session_state.user = None

if "msgs" not in st.session_state:
    st.session_state.msgs = []

if "phase" not in st.session_state:
    st.session_state.phase = 0

if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = False

if "milestone_message" not in st.session_state:
    st.session_state.milestone_message = None

# ==================================================
# PATTERN LIBRARY
# ==================================================

PATTERN_LIBRARY = [
    "overthinking",
    "avoidance",
    "self_doubt",
    "clarity",
    "momentum",
    "discipline",
    "frustration",
    "creative_flow"
]

NEGATIVE_PATTERNS = [
    "overthinking",
    "avoidance",
    "self_doubt",
    "frustration"
]

POSITIVE_PATTERNS = [
    "clarity",
    "momentum",
    "discipline",
    "creative_flow"
]

PATTERN_COORDS = {
    "overthinking":(-0.4,0.6),
    "avoidance":(-0.8,-0.4),
    "self_doubt":(-0.3,0.4),
    "clarity":(0.6,0.6),
    "momentum":(0.8,0.2),
    "discipline":(0.5,0.2),
    "frustration":(-0.4,0.2),
    "creative_flow":(0.9,0.7)
}

# ==================================================
# AUTH SYSTEM
# ==================================================

if st.session_state.user is None:

    st.markdown("""
    <style>
    .login-header{text-align:center;font-style:italic;font-weight:800;font-size:3.5rem;}
    .login-sub{text-align:center;color:#666;margin-bottom:30px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="login-header">The-Dojo</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-sub">Forge your discipline. Step onto the mat.</p>', unsafe_allow_html=True)

    st.info(IMPORTANT_NOTICE)

    login_tab, register_tab = st.tabs(["Enter Dojo","Create Account"])

    with login_tab:

        with st.form("login_form"):

            username = st.text_input("Username").lower().strip()
            password = st.text_input("Password", type="password")

            login_btn = st.form_submit_button("Enter the Dojo")

            if login_btn:

                res = supabase.table("users").select("*").eq("username", username).execute()

                if res.data:

                    user = res.data[0]

                    if bcrypt.checkpw(password.encode(), user["password"].encode()):

                        st.session_state.user = user
                        st.success("Welcome back.")
                        time.sleep(1)
                        st.rerun()

                    else:
                        st.error("Incorrect password")

                else:
                    st.error("User not found")

    with register_tab:

        with st.form("register_form"):

            new_user = st.text_input("Username").lower().strip()
            display_name = st.text_input("Display Name")
            new_pass = st.text_input("Password", type="password")
            invite_code = st.text_input("Dojo Entry Code", type="password")

            agree = st.checkbox(
                "I understand that The Dojo is not a medical or mental health service."
            )

            register_btn = st.form_submit_button("Create Account")

            if register_btn:

                if not agree:
                    st.error("You must acknowledge the notice.")
                    st.stop()

                if invite_code != st.secrets["DOJO_ENTRY_CODE"]:
                    st.error("Invalid dojo entry code.")
                    st.stop()

                hashed_pw = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()

                supabase.table("users").insert({
                    "username": new_user,
                    "display_name": display_name,
                    "password": hashed_pw
                }).execute()

                st.success("Account created.")

    st.stop()

USER_ID = st.session_state.user["id"]
USER_NAME = st.session_state.user["display_name"]

# ==================================================
# RANK
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
# LOAD HISTORY
# ==================================================

if not st.session_state.history_loaded:

    r = supabase.table("records") \
        .select("*", count="exact") \
        .eq("user_id", USER_ID) \
        .order("timestamp") \
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
# MOMENTUM
# ==================================================

def compute_momentum():

    r = supabase.table("dojo_patterns") \
        .select("pattern") \
        .eq("user_id", USER_ID) \
        .order("timestamp", desc=True) \
        .limit(10) \
        .execute()

    if not r.data:
        return 0

    score = 0

    for p in r.data:

        if p["pattern"] in POSITIVE_PATTERNS:
            score += 1

        if p["pattern"] in NEGATIVE_PATTERNS:
            score -= 1

    return score / 10

# ==================================================
# PATTERN DETECTION
# ==================================================

def detect_patterns(user_id):

    recent_msgs = supabase.table("records") \
        .select("content") \
        .eq("user_id", user_id) \
        .eq("role","user") \
        .order("timestamp", desc=True) \
        .limit(50) \
        .execute()

    if not recent_msgs.data or len(recent_msgs.data) < 10:
        return

    reflections = [row["content"] for row in recent_msgs.data]

    prompt = f"""
Choose the best matching pattern from:

{PATTERN_LIBRARY}

Return JSON only.

{{"patterns":[{{"pattern":"name","confidence":0.0}}]}}

Reflections:
{chr(10).join(reflections)}
"""

    headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}

    res = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json={
            "model":"llama-3.3-70b-versatile",
            "messages":[{"role":"system","content":prompt}],
            "temperature":0.2
        },
        headers=headers
    )

    try:

        content = res.json()["choices"][0]["message"]["content"]
        data = json.loads(content)

        for p in data["patterns"]:

            supabase.table("dojo_patterns").insert({

                "user_id":user_id,
                "pattern":p["pattern"],
                "confidence_score":p["confidence"],
                "timestamp":datetime.now(UTC).isoformat()

            }).execute()

    except:
        pass

# ==================================================
# SIDEBAR DASHBOARD
# ==================================================

with st.sidebar:

    st.markdown("### The-Dojo")
    st.markdown(f"**{rank} · {USER_NAME}**")

    st.divider()

    momentum = compute_momentum()

    st.markdown("**Momentum**")
    st.progress((momentum + 1) / 2)

    r = supabase.table("dojo_patterns") \
        .select("pattern,timestamp") \
        .eq("user_id", USER_ID) \
        .order("timestamp", desc=True) \
        .limit(50) \
        .execute()

    if r.data:

        df = pd.DataFrame(r.data)

        xs=[]
        ys=[]

        for p in df["pattern"]:

            coord = PATTERN_COORDS.get(p,(0,0))
            xs.append(coord[0])
            ys.append(coord[1])

        fig, ax = plt.subplots()

        ax.scatter(xs,ys)

        ax.axhline(0)
        ax.axvline(0)

        ax.set_xlim(-1,1)
        ax.set_ylim(-1,1)

        ax.set_title("Mental State Map")

        st.pyplot(fig)

        st.bar_chart(df["pattern"].value_counts())

    st.divider()

    for i, phase in enumerate(PHASE_SETS[rank]):

        if i == st.session_state.phase:
            st.markdown(f"**🟢 {phase}**")
        else:
            st.markdown(phase)

    st.divider()

    if st.button("Bow Out"):

        st.session_state.phase = 0
        st.session_state.msgs = []

        st.success("You bow out from the mat.")

        time.sleep(1)
        st.rerun()

    if st.button("Log Out"):

        for key in list(st.session_state.keys()):
            del st.session_state[key]

        st.rerun()

# ==================================================
# CHAT
# ==================================================

tab_train, tab_history = st.tabs(["Training","History"])

with tab_train:

    st.markdown("### Dojo Awareness")

    st.divider()

    for msg in st.session_state.msgs[-10:]:

        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Speak from center...")

    if prompt:

        st.session_state.msgs.append({"role":"user","content":prompt})

        supabase.table("records").insert({
            "user_id":USER_ID,
            "role":"user",
            "content":prompt,
            "timestamp":datetime.now(UTC).isoformat()
        }).execute()

        user_count = len([m for m in st.session_state.msgs if m["role"]=="user"])

        if user_count % 7 == 0:
            detect_patterns(USER_ID)

        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}

        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "model":"llama-3.3-70b-versatile",
                "messages":[{"role":"system","content":"Respond as a calm reflective mentor."}]
                + st.session_state.msgs[-10:]
            },
            headers=headers
        )

        reply = res.json()["choices"][0]["message"]["content"]

        with st.chat_message("assistant"):

            placeholder = st.empty()
            placeholder.markdown("Thinking...")

            time.sleep(2)

            text=""

            for s in reply.split(". "):

                text += s + ". "
                placeholder.markdown(text)
                time.sleep(.4)

        st.session_state.msgs.append({"role":"assistant","content":reply})

        supabase.table("records").insert({
            "user_id":USER_ID,
            "role":"assistant",
            "content":reply,
            "timestamp":datetime.now(UTC).isoformat()
        }).execute()

        st.rerun()

with tab_history:

    st.markdown("### Training History")

    r=supabase.table("records") \
        .select("*") \
        .eq("user_id",USER_ID) \
        .order("timestamp",desc=True) \
        .limit(50) \
        .execute()

    if r.data:

        for row in r.data:

            with st.chat_message(row["role"]):
                st.markdown(row["content"])

