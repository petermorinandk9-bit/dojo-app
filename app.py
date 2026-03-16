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
from collections import Counter

def inject_dojo_styling():
    """
    The Dojo UI Master Block
    Minimalist Zen-Dark styling + PWA meta tags
    """
    st.markdown("""
        <style>
        /* ========================================
           STREAMLIT CHROME REMOVAL
        ======================================== */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* ========================================
           ROOT & BACKGROUND
        ======================================== */
        .stApp {
            background-color: #0a0a0a;
            color: #e0e0e0;
        }
        
        /* ========================================
           SIDEBAR - SLATE ZEN
        ======================================== */
        [data-testid="stSidebar"] {
            background-color: #1a1a1a;
            border-right: 1px solid #2a2a2a;
        }
        
        [data-testid="stSidebar"] .element-container {
            color: #c0c0c0;
        }
        
        /* ========================================
           CHAT BUBBLES
        ======================================== */
        /* User messages - Right aligned, slate bubble */
        [data-testid="stChatMessageContainer"][data-testid*="user"] {
            background-color: #2a2a2a;
            border-radius: 12px;
            padding: 12px 16px;
            margin: 8px 0;
            margin-left: 20%;
            border-left: 3px solid #4a4a4a;
        }
        
        /* Assistant messages - Left aligned, dark bubble */
        [data-testid="stChatMessageContainer"][data-testid*="assistant"] {
            background-color: #1a1a1a;
            border-radius: 12px;
            padding: 12px 16px;
            margin: 8px 0;
            margin-right: 20%;
            border-left: 3px solid #0a0a0a;
        }
        
        /* ========================================
           INPUTS & BUTTONS
        ======================================== */
        .stTextInput input {
            background-color: #1a1a1a;
            color: #e0e0e0;
            border: 1px solid #2a2a2a;
            border-radius: 8px;
        }
        
        .stButton button {
            background-color: #2a2a2a;
            color: #e0e0e0;
            border: 1px solid #3a3a3a;
            border-radius: 8px;
            transition: all 0.2s ease;
        }
        
        .stButton button:hover {
            background-color: #3a3a3a;
            border-color: #4a4a4a;
        }
        
        /* ========================================
           PROGRESS BAR
        ======================================== */
        .stProgress > div > div {
            background-color: #4a4a4a;
        }
        
        /* ========================================
           TABS
        ======================================== */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #1a1a1a;
            border-bottom: 1px solid #2a2a2a;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #808080;
            border-radius: 8px 8px 0 0;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #2a2a2a;
            color: #e0e0e0;
        }
        
        /* ========================================
           DIVIDERS
        ======================================== */
        hr {
            border-color: #2a2a2a;
        }
        
        /* ========================================
           TYPOGRAPHY
        ======================================== */
        h1, h2, h3 {
            color: #f0f0f0;
            font-weight: 300;
            letter-spacing: 0.5px;
        }
        
        .stMarkdown {
            color: #d0d0d0;
            line-height: 1.6;
        }
        
        /* ========================================
           SCROLLBAR
        ======================================== */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #0a0a0a;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #2a2a2a;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #3a3a3a;
        }
        </style>
        
        <!-- PWA MANIFEST & META TAGS -->
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="#0a0a0a">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="The Dojo">
        <link rel="apple-touch-icon" href="/icon-192.png">
    """, unsafe_allow_html=True)

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="The-Dojo", layout="wide")
inject_dojo_styling()

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
# PATTERN DETECTION (Upgrade 1: per reflection, after crisis check)
# ==================================================
def detect_pattern_for_message(user_id, message):
    prompt = f"""
You are analyzing a practitioner reflection.

Reflection:
{message}

Choose the SINGLE most relevant behavioral pattern from this list:
{PATTERN_LIBRARY}

Focus on behavior patterns rather than temporary emotions.

Return JSON only:
{{"pattern":"name","confidence":0.0}}
"""

    headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": prompt}]
            },
            headers=headers
        )

        content = res.json()["choices"][0]["message"]["content"]
        start = content.find("{")
        end = content.rfind("}") + 1
        data = json.loads(content[start:end])

        pattern = data["pattern"]
        confidence = data["confidence"]

        supabase.table("dojo_patterns").insert({
            "user_id": user_id,
            "pattern": pattern,
            "confidence_score": confidence,
            "timestamp": datetime.now(UTC).isoformat()
        }).execute()

        return pattern, confidence

    except Exception as e:
        print(f"Pattern detection error: {e}")
        return None, 0.0

# ==================================================
# TOP PATTERN FREQUENCY (Upgrade 5)
# ==================================================
def compute_top_pattern():
    r = supabase.table("dojo_patterns") \
        .select("pattern") \
        .eq("user_id", USER_ID) \
        .order("timestamp", desc=True) \
        .limit(50) \
        .execute()
    
    if not r.data or len(r.data) < 5:
        return "Calibrating..."
    
    patterns = [p["pattern"] for p in r.data]
    counts = Counter(patterns)
    
    if not counts:
        return "Calibrating..."
    
    top_pattern, top_count = counts.most_common(1)[0]
    percentage = int((top_count / len(patterns)) * 100)
    
    return f"{top_pattern.replace('_', ' ').title()} ({percentage}%)"

# ==================================================
# SIDEBAR (with free reflections urgency + top pattern)
# ==================================================
with st.sidebar:
    st.markdown("### The-Dojo")
    st.markdown(f"**{rank} · {USER_NAME}**")
    subscription = st.session_state.user.get("subscription_status", "free")
    if subscription not in ["paid", "beta", "admin"]:
        user_msg_count = supabase.table("records") \
            .select("id", count="exact") \
            .eq("user_id", USER_ID) \
            .eq("role", "user") \
            .execute().count or 0
        remaining = max(0, 15 - user_msg_count)
        if remaining <= 3:
            st.error(f"⚠️ {remaining} reflections left")
        elif remaining <= 7:
            st.warning(f"{remaining} reflections remaining")
        else:
            st.caption(f"✓ {remaining} free reflections")
    st.divider()
    momentum = compute_momentum()
    evolution = compute_evolution()
    top_pattern = compute_top_pattern()
    st.markdown(f"Momentum: **{momentum:+.2f}**")
    st.markdown(f"Evolution: **{evolution}**")
    st.markdown(f"**Top Pattern:** {top_pattern}")
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

        if prompt == st.session_state.last_processed_prompt:
            st.stop()

        st.session_state.last_processed_prompt = prompt

        st.session_state.msgs.append({"role": "user", "content": prompt})
        supabase.table("records").insert({
            "user_id": USER_ID,
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now(UTC).isoformat()
        }).execute()

        doctrine = "Discipline begins with attention."

        crisis_keywords = ["suicide", "kill myself", "want to die", "hopeless", "end it", "hurt myself", "self harm"]
        if any(word in prompt.lower() for word in crisis_keywords):
            reply = """
I'm stopping here.

What you're describing is serious and needs real support right now.

Call or text **988** (US Suicide & Crisis Lifeline, 24/7)
Or text HOME to **741741** (Crisis Text Line)

The mat will still be here when you're ready. Please reach out to someone.
"""
            detected_pattern = None
            confidence = 0.0
        else:
            # Detect pattern only if not crisis
            detected_pattern, confidence = detect_pattern_for_message(USER_ID, prompt)

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

            mentor_prompt = f"""
You are a calm, disciplined mentor guiding a practitioner through reflection.
Your role: help them observe patterns in thinking and behavior.
Never give direct advice. Guide with questions, clarity, and grounded insight.
{mirror}
If appropriate, weave in this teaching naturally:
{doctrine}

CRITICAL LENGTH RULES — FOLLOW EXACTLY OR RESPONSE WILL BE REJECTED:

1. LIGHT/NEUTRAL INPUT (casual check-in, simple question, brief share):
   → 1-2 sentences max
   → Example: "Good to see you here. What's on your mind today?"

2. MODERATE INPUT (mild frustration, exploring an idea, noticing a pattern):
   → 3-5 sentences, single paragraph
   → Example: "That awareness is the first step. What happens right before you avoid the task?"

3. HEAVY INPUT (deep struggle, breakthrough moment, stuck in loop):
   → 2 short paragraphs max (100-150 words total)
   → Example: "This loop has deep roots. Notice how it begins... [short reflection]. What small step feels possible right now?"

When uncertain, choose shorter. Default to brevity.
NEVER exceed 150 words under any circumstance.

Tone: grounded, non-judgmental, quietly supportive. No fluff, no lectures.
End in a way that invites continuation unless resolved.
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

        # HARD WORD CAP (150 words max - stricter)
        words = reply.split()
        if len(words) > 150:
            reply = ' '.join(words[:150]) + "… (mentor pauses — reflect before continuing)"

        # SINGLE ASSISTANT MESSAGE
        if st.session_state.msgs and st.session_state.msgs[-1]["role"] == "assistant" and st.session_state.msgs[-1]["content"] == reply:
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

        user_msgs_in_session = len([m for m in st.session_state.msgs if m["role"] == "user"])
        if user_msgs_in_session % 3 == 0 and user_msgs_in_session > 0:
            st.session_state.phase = (st.session_state.phase + 1) % 4
            phase_name = PHASE_SETS[rank][st.session_state.phase]
            st.session_state.milestone_message = f"→ Moving to {phase_name}"

        old_rank = st.session_state.get("last_rank", "Student")
        new_rank = compute_rank(user_reflection_count + 1)
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
