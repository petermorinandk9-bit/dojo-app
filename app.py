import streamlit as st
import requests
import time
import random
import json
import bcrypt
from datetime import datetime
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
# SESSION SAFETY
# ==================================================
if "user" not in st.session_state:
    st.session_state.user = None

if "msgs" not in st.session_state:
    st.session_state.msgs = []

if "phase" not in st.session_state:
    st.session_state.phase = 0

# ==================================================
# AUTH SYSTEM
# ==================================================
if st.session_state.user is None:

    st.markdown("""
    <style>
    .stApp {background:#ffffff;}
    .login-header{text-align:center;font-style:italic;font-weight:800;font-size:3.5rem;}
    .login-sub{text-align:center;color:#666;margin-bottom:30px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="login-header">The-Dojo</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-sub">Forge your discipline. Step onto the mat.</p>', unsafe_allow_html=True)

    login_tab, register_tab = st.tabs(["Enter Dojo", "Create Account"])

    # ===============================
    # LOGIN
    # ===============================
    with login_tab:

        with st.form("login_form"):

            username = st.text_input("Username").lower().strip()
            password = st.text_input("Password", type="password")

            login_btn = st.form_submit_button("Enter the Dojo")

            if login_btn:

                res = supabase.table("users") \
                    .select("*") \
                    .eq("username", username) \
                    .execute()

                if res.data:

                    user = res.data[0]
                    stored_hash = user["password"]

                    if bcrypt.checkpw(password.encode(), stored_hash.encode()):

                        st.session_state.user = user
                        st.success("Welcome back.")
                        time.sleep(1)
                        st.rerun()

                    else:
                        st.error("Incorrect password")

                else:
                    st.error("User not found")

    # ===============================
    # REGISTER
    # ===============================
    with register_tab:

        with st.form("register_form"):

            new_user = st.text_input("Username").lower().strip()
            display_name = st.text_input("Display Name")
            new_pass = st.text_input("Password", type="password")

            register_btn = st.form_submit_button("Create Account")

            if register_btn:

                existing = supabase.table("users") \
                    .select("username") \
                    .eq("username", new_user) \
                    .execute()

                if existing.data:
                    st.error("Username already exists")

                else:

                    hashed_pw = bcrypt.hashpw(
                        new_pass.encode(),
                        bcrypt.gensalt()
                    ).decode()

                    supabase.table("users").insert({
                        "username": new_user,
                        "display_name": display_name,
                        "password": hashed_pw
                    }).execute()

                    st.success("Account created. You may now enter the dojo.")

    st.stop()

USER_ID = st.session_state.user["id"]
USER_NAME = st.session_state.user["display_name"]

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
# LOAD HISTORY
# ==================================================
if "history_loaded" not in st.session_state:

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
# PATTERN DETECTION ENGINE
# ==================================================
def detect_patterns(user_id):

    recent_msgs = supabase.table("records") \
        .select("content") \
        .eq("user_id", user_id) \
        .eq("role", "user") \
        .order("timestamp", desc=True) \
        .limit(50) \
        .execute()

    if not recent_msgs.data or len(recent_msgs.data) < 10:
        return

    reflections = [row["content"] for row in recent_msgs.data]

    pattern_prompt = f"""
Analyze reflections for recurring thinking patterns.

Return JSON only:

{{
"patterns":[
{{"pattern":"short description","confidence":0.0}}
]
}}

Reflections:
{chr(10).join(reflections)}
"""

    headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}

    res = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json={
            "model":"llama-3.3-70b-versatile",
            "messages":[{"role":"system","content":pattern_prompt}],
            "temperature":0.2,
            "max_tokens":200
        },
        headers=headers
    )

    try:

        content = res.json()["choices"][0]["message"]["content"]
        data = json.loads(content)

        for p in data["patterns"]:

            supabase.table("dojo_patterns").insert({

                "user_id": user_id,
                "pattern": p["pattern"],
                "confidence_score": p["confidence"],
                "timestamp": datetime.utcnow().isoformat()

            }).execute()

    except:
        pass

# ==================================================
# MEMORY FETCH
# ==================================================
def get_current_pattern_memory():

    try:

        r = supabase.table("dojo_patterns") \
            .select("pattern,confidence_score") \
            .eq("user_id", USER_ID) \
            .order("timestamp", desc=True) \
            .limit(1) \
            .execute()

        if r.data:

            p = r.data[0]

            return f"Pattern: {p['pattern']} (confidence {p['confidence_score']:.2f})"

    except:
        pass

    return "No pattern detected."

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:

    st.markdown("### The-Dojo")
    st.markdown(f"**{rank} · {USER_NAME}**")

    st.divider()

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

    st.markdown(get_current_pattern_memory())

    st.divider()

    for msg in st.session_state.msgs[-10:]:

        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Speak from center...")

    if prompt:

        st.session_state.msgs.append({"role":"user","content":prompt})

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

                text+=s+". "
                placeholder.markdown(text)
                time.sleep(.5)

        st.session_state.msgs.append({"role":"assistant","content":reply})

        st.rerun()
