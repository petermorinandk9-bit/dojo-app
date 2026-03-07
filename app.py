```python
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
# NOTICE
# ==================================================

IMPORTANT_NOTICE = """
### Important Notice

The Dojo is a reflection and personal development tool designed to support mindfulness and self-awareness.

It is **NOT a medical or mental health service**.

If you are in crisis please contact a professional.

United States: **988 Suicide & Crisis Lifeline**
"""

# ==================================================
# SUPABASE
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

    st.title("The-Dojo")
    st.info(IMPORTANT_NOTICE)

    login_tab, register_tab = st.tabs(["Enter Dojo","Create Account"])

    with login_tab:

        with st.form("login_form"):

            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.form_submit_button("Enter"):

                r = supabase.table("users").select("*").eq("username",username).execute()

                if r.data:

                    user = r.data[0]

                    stored_hash = user["password"]

                    if isinstance(stored_hash,str):
                        stored_hash = stored_hash.encode()

                    if bcrypt.checkpw(password.encode(), stored_hash):

                        st.session_state.user = user
                        st.rerun()

                    else:
                        st.error("Incorrect password")

                else:
                    st.error("User not found")

    with register_tab:

        with st.form("register_form"):

            username = st.text_input("Username")
            display = st.text_input("Display Name")
            password = st.text_input("Password", type="password")
            invite = st.text_input("Dojo Entry Code")

            agree = st.checkbox("I understand this is not a medical service.")

            if st.form_submit_button("Create"):

                if not agree:
                    st.error("You must acknowledge the notice")
                    st.stop()

                if invite != st.secrets["DOJO_ENTRY_CODE"]:
                    st.error("Invalid code")
                    st.stop()

                hashed = bcrypt.hashpw(password.encode(),bcrypt.gensalt()).decode()

                supabase.table("users").insert({
                    "username":username,
                    "display_name":display,
                    "password":hashed
                }).execute()

                st.success("Account created")

    st.stop()

USER_ID = st.session_state.user["id"]
USER_NAME = st.session_state.user["display_name"]

# ==================================================
# LOAD HISTORY
# ==================================================

if not st.session_state.history_loaded:

    r = supabase.table("records") \
        .select("*",count="exact") \
        .eq("user_id",USER_ID) \
        .order("timestamp") \
        .execute()

    if r.data:

        for row in r.data:

            st.session_state.msgs.append({
                "role":row["role"],
                "content":row["content"]
            })

    st.session_state.records_count = r.count if r.count else 0
    st.session_state.history_loaded = True

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

rank = compute_rank(st.session_state.records_count)

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
        .eq("user_id",USER_ID) \
        .order("timestamp",desc=True) \
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
# EVOLUTION
# ==================================================

def compute_evolution():

    r = supabase.table("dojo_patterns") \
        .select("pattern") \
        .eq("user_id",USER_ID) \
        .order("timestamp",desc=True) \
        .limit(20) \
        .execute()

    if not r.data:
        return "Unknown"

    score = 0

    for p in r.data:

        if p["pattern"] in POSITIVE_PATTERNS:
            score += 1

        if p["pattern"] in NEGATIVE_PATTERNS:
            score -= 1

    if score > 3:
        return "Rising"

    if score < -3:
        return "Declining"

    return "Stable"

# ==================================================
# PATTERN MIRROR
# ==================================================

def get_pattern_mirror():

    r = supabase.table("dojo_patterns") \
        .select("pattern") \
        .eq("user_id",USER_ID) \
        .order("timestamp",desc=True) \
        .limit(5) \
        .execute()

    if not r.data:
        return ""

    patterns = [p["pattern"] for p in r.data]

    common = max(set(patterns), key=patterns.count)

    if random.random() < 0.35:

        return f"I notice **{common}** appearing again in your reflections."

    return ""

# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.markdown("### The-Dojo")
    st.markdown(f"**{rank} · {USER_NAME}**")

    momentum = compute_momentum()
    evolution = compute_evolution()

    st.markdown(f"Momentum: **{round(momentum,2)}**")
    st.markdown(f"Evolution: **{evolution}**")

    st.progress((momentum + 1)/2)

# ==================================================
# CHAT
# ==================================================

tab_train,tab_history = st.tabs(["Training","History"])

with tab_train:

    st.markdown("### Dojo Awareness")

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

        mirror = get_pattern_mirror()

        mentor_prompt = f"""
Respond as a calm reflective mentor.

If relevant include this observation:

{mirror}
"""

        headers = {"Authorization":f"Bearer {st.secrets['GROQ_API_KEY']}"}

        res = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json={
        "model":"llama-3.3-70b-versatile",
        "messages":[{"role":"system","content":mentor_prompt}]
        + st.session_state.msgs[-10:]
        },
        headers=headers
        )

        reply = res.json()["choices"][0]["message"]["content"]

        with st.chat_message("assistant"):

            placeholder = st.empty()
            text=""

            for s in reply.split(". "):
                text += s + ". "
                placeholder.markdown(text)
                time.sleep(.3)

        st.session_state.msgs.append({"role":"assistant","content":reply})

        supabase.table("records").insert({
            "user_id":USER_ID,
            "role":"assistant",
            "content":reply,
            "timestamp":datetime.now(UTC).isoformat()
        }).execute()

        st.rerun()

with tab_history:

    r = supabase.table("records") \
        .select("*") \
        .eq("user_id",USER_ID) \
        .order("timestamp",desc=True) \
        .limit(50) \
        .execute()

    if r.data:

        for row in r.data:

            with st.chat_message(row["role"]):
                st.markdown(row["content"])
```
