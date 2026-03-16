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
It is **not a medical or mental health service**, and the guidance provided by the system should not be considered professional advice.
If you are in emotional crisis please contact a professional.
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
if "last_rank" not in st.session_state:
    st.session_state.last_rank = "Student"
# Guard to prevent double processing of the same user input
if "last_processed_prompt" not in st.session_state:
    st.session_state.last_processed_prompt = None

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
    "overthinking": (-0.4, 0.6),
    "avoidance": (-0.8, -0.4),
    "self_doubt": (-0.3, 0.4),
    "clarity": (0.6, 0.6),
    "momentum": (0.8, 0.2),
    "discipline": (0.5, 0.2),
    "frustration": (-0.4, 0.2),
    "creative_flow": (0.9, 0.7)
}

# ==================================================
# AUTH SYSTEM
# ==================================================
if st.session_state.user is None:
    st.markdown("# The-Dojo")
    st.info(IMPORTANT_NOTICE)
    login_tab, register_tab = st.tabs(["Enter Dojo", "Create Account"])
    with login_tab:
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Enter"):
                r = supabase.table("users").select("*").eq("username", username).execute()
                if r.data:
                    user = r.data[0]
                    stored_hash = user.get("password")
                    if stored_hash is None:
                        st.error("No password set for this account.")
                        st.stop()
                    if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Incorrect password")
                else:
                    st.error("User not found")
    with register_tab:
        with st.form("register"):
            username = st.text_input("Username")
            display = st.text_input("Display Name")
            password = st.text_input("Password", type="password")
            agree = st.checkbox("I understand this is not a medical service.")
            if st.form_submit_button("Create"):
                if not agree:
                    st.error("You must acknowledge the notice")
                    st.stop()
                hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                hashed_str = hashed_bytes.decode('utf-8')
                supabase.table("users").insert({
                    "username": username,
                    "display_name": display,
                    "password": hashed_str,
                    "subscription_status": "free"
                }).execute()
                st.success("Account created — please log in")
    st.stop()

USER_ID = st.session_state.user["id"]
USER_NAME = st.session_state.user["display_name"]

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

# Count real user reflections from Supabase for rank
user_reflection_count = supabase.table("records") \
    .select("id", count="exact") \
    .eq("user_id", USER_ID) \
    .eq("role", "user") \
    .execute().count or 0

rank = compute_rank(user_reflection_count)

# ==================================================
# PHASES
# ==================================================
PHASE_SETS = {
    "Student": ["Welcome", "Warm-Up", "Training", "Cool Down"],
    "Practitioner": ["Welcome", "Warm-Up", "Training", "Cool Down"],
    "Sentinel": ["Welcome", "Warm-Up", "Training", "Cool Down"],
    "Sovereign": ["Welcome", "Warm-Up", "Training", "Cool Down"]
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
# EVOLUTION
# ==================================================
def compute_evolution():
    r = supabase.table("dojo_patterns") \
        .select("pattern") \
        .eq("user_id", USER_ID) \
        .order("timestamp", desc=True) \
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
# PATTERN DETECTION
# ==================================================
def detect_patterns(user_id):
    recent = supabase.table("records") \
        .select("content") \
        .eq("user_id", user_id) \
        .eq("role", "user") \
        .order("timestamp", desc=True) \
        .limit(50) \
        .execute()
    if not recent.data or len(recent.data) < 10:
        return
    reflections = [row["content"] for row in recent.data]
    reflection_text = "\n".join(reflections)
    prompt = f"""
You are analyzing reflection entries from a practitioner.
Recent reflections:
{reflection_text}
Choose the SINGLE most relevant behavioral pattern from this list:
{PATTERN_LIBRARY}
Focus on behavioral patterns rather than temporary emotions.
Return JSON only in this format:
{{"patterns":[{{"pattern":"name","confidence":0.0}}]}}
"""
    headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
    res = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": prompt}]
        },
        headers=headers
    )
    try:
        content = res.json()["choices"][0]["message"]["content"]
        start = content.find("{")
        end = content.rfind("}") + 1
        data = json.loads(content[start:end])
        for p in data["patterns"]:
            supabase.table("dojo_patterns").insert({
                "user_id": user_id,
                "pattern": p["pattern"],
                "confidence_score": p["confidence"],
                "timestamp": datetime.now(UTC).isoformat()
            }).execute()
    except:
        pass

# ==================================================
# SIDEBAR – removed remaining count display
# ==================================================
with st.sidebar:
    st.markdown("### The-Dojo")
    st.markdown(f"**{rank} · {USER_NAME}**")
    subscription = st.session_state.user.get("subscription_status", "free")
    # Removed: free reflections remaining caption
    st.divider()
    momentum = compute_momentum()
    evolution = compute_evolution()
    st.markdown(f"Momentum: **{momentum:+.2f}**")
    st.markdown(f"Evolution: **{evolution}**")
    st.progress((momentum + 1) / 2)
    st.divider()
    for i, phase in enumerate(PHASE_SETS[rank]):
        if i == st.session_state.phase:
            st.markdown(f"**🟢 {phase}**")
        else:
            st.markdown(phase)
    st.divider()
    if st.button("Clear Session (Bow Out)", help="Clears current chat but keeps your full history in Training tab"):
        st.session_state.phase = 0
        st.session_state.msgs = []
        st.success("Session cleared. You bow out from the mat.")
        time.sleep(1)
        st.rerun()
    if st.button("Log Out"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ==================================================
# CHAT
# ==================================================
tab_train, tab_history = st.tabs(["Training", "History"])
with tab_train:
    st.markdown("### Dojo Awareness")
    if st.session_state.milestone_message:
        st.success(st.session_state.milestone_message)
        st.session_state.milestone_message = None
    st.divider()
    for msg in st.session_state.msgs[-10:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("Speak from center...")
    if prompt:
        subscription = st.session_state.user.get("subscription_status", "free")
        if subscription not in ["paid", "beta", "admin"]:
            # Still enforce the 15 limit with real-time Supabase count
            r = supabase.table("records") \
                .select("id", count="exact") \
                .eq("user_id", USER_ID) \
                .eq("role", "user") \
                .execute()
            user_count = r.count or 0
            if user_count >= 15:
                st.warning("You have reached the free training limit of 15 reflections.")
                st.info("Join the Dojo to continue your practice.")
                st.stop()

        # Only process this exact prompt once
        if prompt == st.session_state.last_processed_prompt:
            st.stop()  # already handled this input → skip

        st.session_state.last_processed_prompt = prompt

        st.session_state.msgs.append({"role": "user", "content": prompt})
        supabase.table("records").insert({
            "user_id": USER_ID,
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now(UTC).isoformat()
        }).execute()

        if len([m for m in st.session_state.msgs if m["role"] == "user"]) % 3 == 0:
            detect_patterns(USER_ID)

        doctrine = "Discipline begins with attention."

        # CRISIS DETECTION
        crisis_keywords = ["suicide", "kill myself", "want to die", "hopeless", "end it", "hurt myself", "self harm"]
        if any(word in prompt.lower() for word in crisis_keywords):
            reply = """
I'm stopping here.

What you're describing is serious and needs real support right now.

Call or text **988** (US Suicide & Crisis Lifeline, 24/7)
Or text HOME to **741741** (Crisis Text Line)

The mat will still be here when you're ready. Please reach out to someone.
"""
        else:
            # PATTERN PERSISTENCE DETECTION
            persistent_pattern = None
            try:
                r = supabase.table("dojo_patterns") \
                    .select("pattern") \
                    .eq("user_id", USER_ID) \
                    .order("timestamp", desc=True) \
                    .limit(3) \
                    .execute()
                if r.data and len(r.data) == 3:
                    if r.data[0]["pattern"] == r.data[1]["pattern"] == r.data[2]["pattern"]:
                        persistent_pattern = r.data[0]["pattern"]
            except:
                pass
            mirror = ""
            if persistent_pattern:
                mirror = f"I notice **{persistent_pattern.replace('_', ' ')}** appearing repeatedly in your reflections.\n\n"

            # UPDATED MENTOR PROMPT WITH LENGTH SCALING
            mentor_prompt = f"""
You are a calm, disciplined mentor guiding a practitioner through reflection.
Your role: help them observe patterns in thinking and behavior.
Never give direct advice. Guide with questions, clarity, and grounded insight.
{mirror}
If appropriate, weave in this teaching naturally:
{doctrine}

RESPONSE LENGTH & STRUCTURE RULES — FOLLOW EXACTLY:
- Light, calm, or neutral user message (low emotional weight): 1–3 short sentences only. Be concise, direct, and encouraging.
- Moderate emotion, mild frustration, or emerging pattern: 3–6 sentences, 1 short paragraph. Offer gentle reflection without overwhelming.
- High emotional weight, stuck in a loop, deep self-doubt, or major breakthrough: 1–3 full paragraphs (max 250 words total). Go deeper, slower, more layered — but still concise and focused. Never ramble or exceed 250 words.
- Always prioritize quality over quantity. End responses in a way that invites continuation unless the user seems resolved.
- Tone: grounded, non-judgmental, quietly supportive. No fluff, no lectures.
"""

            try:
                headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
                res = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "system", "content": mentor_prompt}]
                        + st.session_state.msgs[-10:]
                    },
                    headers=headers
                )
                reply = res.json()["choices"][0]["message"]["content"]
            except Exception:
                reply = "The mentor pauses for a moment. Please try again."

        # HARD WORD CAP (250 words max)
        words = reply.split()
        if len(words) > 250:
            reply = ' '.join(words[:250]) + "… (mentor pauses — reflect before continuing)"

        lines = reply.split('\n')
        reply = '\n'.join(lines[:8])  # rough 3–4 paragraph cap

        # SINGLE ASSISTANT MESSAGE – with duplicate guard
        if st.session_state.msgs and st.session_state.msgs[-1]["role"] == "assistant" and st.session_state.msgs[-1]["content"] == reply:
            # Already appended this exact reply → skip to prevent double
            pass
        else:
            with st.chat_message("assistant"):
                placeholder = st.empty()
                placeholder.markdown("The mentor reflects...")
                time.sleep(1.5)

                text = ""
                for sentence in reply.split(". "):
                    text += sentence + ". "
                    placeholder.markdown(text)
                    time.sleep(0.2)

                placeholder.markdown(reply)

            st.session_state.msgs.append({"role": "assistant", "content": reply})
            supabase.table("records").insert({
                "user_id": USER_ID,
                "role": "assistant",
                "content": reply,
                "timestamp": datetime.now(UTC).isoformat()
            }).execute()

        # PHASE ADVANCEMENT
        user_msgs_in_session = len([m for m in st.session_state.msgs if m["role"] == "user"])
        if user_msgs_in_session % 3 == 0 and user_msgs_in_session > 0:
            st.session_state.phase = (st.session_state.phase + 1) % 4
            phase_name = PHASE_SETS[rank][st.session_state.phase]
            st.session_state.milestone_message = f"→ Moving to {phase_name}"

        # RANK PROGRESSION CHECK
        old_rank = st.session_state.get("last_rank", "Student")
        new_rank = compute_rank(user_reflection_count + 1)  # approximate for display
        if new_rank != old_rank:
            st.session_state.last_rank = new_rank
            st.balloons()
            st.session_state.milestone_message = f"🥋 Rank Advanced: {new_rank}"

        st.rerun()

with tab_history:
    st.markdown("### Training History")
    r = supabase.table("records") \
        .select("*") \
        .eq("user_id", USER_ID) \
        .order("timestamp", desc=True) \
        .limit(50) \
        .execute()
    if r.data:
        for row in r.data:
            with st.chat_message(row["role"]):
                st.markdown(row["content"])
