import streamlit as st
import requests
import time
import json
import bcrypt
import random
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, UTC
from supabase import create_client, Client
from collections import Counter

def inject_dojo_styling():
    """
    The Digital Zendo - Final Polished Weld
    Sidebar collapse button visible, styled, and hover-fixed to grey.
    """
    st.markdown("""
    <style>
        /* Import a Raw Brush Font from Google */
        @import url('https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&display=swap');
        
        .stApp {
            background-color: #0a0a0a !important;
            color: #f0f0f0 !important;
        }
        
        /* THE ALTAR (Title) - hand-painted feel with slight rotation, ink bleed shadow */
        .dojo-title {
            font-family: 'Ma Shan Zheng', cursive !important;
            font-size: 160px !important;
            color: rgba(178,34,34,0.75) !important;
            text-align: center !important;
            margin-top: -30px !important;
            margin-bottom: 60px !important;
            letter-spacing: 4px;
            transform: rotate(-1.5deg);
            text-shadow:
                0 0 6px rgba(178,34,34,0.25),
                0 0 30px rgba(178,34,34,0.12),
                0 0 80px rgba(178,34,34,0.06);
            animation: titleFade 2.5s ease;
        }
        
        @keyframes titleFade {
            from { opacity: 0; transform: translateY(-30px) rotate(-3deg); }
            to { opacity: 1; transform: translateY(0) rotate(-1.5deg); }
        }
        
        /* INK BLEED MESSAGES - improved ink-like bloom */
        [data-testid="stChatMessage"] {
            background-color: transparent !important;
            animation: inkBloom 1.4s ease !important;
            color: #f0f0f0 !important;
        }
        
        @keyframes inkBloom {
            0% { opacity: 0; transform: translateY(10px); filter: blur(6px); }
            40% { opacity: 0.6; filter: blur(2px); }
            100% { opacity: 1; transform: translateY(0); filter: blur(0px); }
        }
        
        /* MENTOR — center mist with true ink diffusion */
        [data-testid="stChatMessage"][aria-label="assistant message"] {
            text-align: center !important;
            background: radial-gradient(circle at 50% 40%, rgba(220,220,220,0.06), rgba(255,255,255,0.02)) !important;
            margin: 16px 12% !important;
            padding: 18px 22px !important;
            border-radius: 16px !important;
            backdrop-filter: blur(3px);
            box-shadow: 0 0 30px rgba(255,255,255,0.03);
        }
        
        /* STUDENT — right aligned ink with diffusion */
        [data-testid="stChatMessage"][aria-label="user message"] {
            text-align: right !important;
            background: radial-gradient(circle at 70% 40%, rgba(178,34,34,0.12), rgba(255,255,255,0.02)) !important;
            margin-left: 22% !important;
            padding: 16px 20px !important;
            border-radius: 16px 4px 4px 16px !important;
            box-shadow: 0 0 25px rgba(178,34,34,0.15);
        }
        
        /* Enforce brighter text in chat markdown */
        [data-testid="stChatMessage"] .stMarkdown,
        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] div {
            color: #f0f0f0 !important;
        }
        
        /* Avatar background */
        div[data-testid^="stChatMessageAvatar"] {
            background-color: #1a1a1a !important;
        }
        
        /* STONE TABLET SIDEBAR - mineral slate gradient */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #2f4f4f 0%, #1b2a2a 100%) !important;
            border-right: 1px solid rgba(139,69,19,0.25) !important;
            color: #f0f0f0 !important;
        }
        
        [data-testid="stSidebar"] * {
            color: #f0f0f0 !important;
        }
        
        /* Sidebar buttons - white-on-slate idle (pop), dark-on-slate hover (calm) */
        [data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] button {
            background: rgba(47, 79, 79, 0.6) !important;
            color: #ffffff !important;
            border: 1px solid #3a5a5a !important;
            border-radius: 6px !important;
            padding: 10px 16px !important;
            margin: 4px 0 !important;
            transition: all 0.2s ease !important;
            font-weight: 400 !important;
        }
        
        [data-testid="stSidebar"] .stButton > button:hover,
        [data-testid="stSidebar"] button:hover {
            background: rgba(30, 30, 30, 0.85) !important;
            color: #dcdcdc !important;
            border-color: #2f4f4f !important;
            transform: translateX(4px) !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.4) !important;
        }
        
        [data-testid="stSidebar"] .stButton > button:active,
        [data-testid="stSidebar"] button:active {
            background: rgba(20, 20, 20, 0.95) !important;
            color: #ffffff !important;
            transform: translateX(2px) !important;
        }
        
        /* Collapse button - visible and styled to match sidebar buttons */
        [data-testid="stSidebarCollapsedControl"] {
            background: rgba(47, 79, 79, 0.4) !important;
            color: #a8b5b5 !important;
            border: 1px solid rgba(58, 90, 90, 0.6) !important;
            border-radius: 4px !important;
            padding: 6px 10px !important;
            transition: all 0.2s ease !important;
            z-index: 99999 !important; /* Ensure it stays above other elements */
        }
        
        /* THE FIX: Force a clean grey hover state */
        [data-testid="stSidebarCollapsedControl"]:hover {
            background: rgba(105, 105, 105, 0.8) !important;
            color: #ffffff !important;
            border-color: rgba(150, 150, 150, 0.8) !important;
        }
        
        /* Ambient temple lighting - soft light from above */
        body::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 50% 10%, rgba(255,255,255,0.03), transparent 60%);
            pointer-events: none;
        }
        
        /* HIDE STREAMLIT CHROME BUT PRESERVE HEADER FOR BUTTON VISIBILITY */
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        header {background-color: transparent !important;}
    </style>
    
    <div class="dojo-title">The Dojo</div>
    """, unsafe_allow_html=True)

# ==================================================
# CONFIG - Force sidebar expanded on load
# ==================================================
st.set_page_config(
    page_title="The-Dojo",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
if "last_processed_prompt" not in st.session_state:
    st.session_state.last_processed_prompt = None

# ==================================================
# PATTERN LIBRARY
# ==================================================
PATTERN_LIBRARY = [
    "overthinking", "avoidance", "self_doubt", "clarity",
    "momentum", "discipline", "frustration", "creative_flow"
]
NEGATIVE_PATTERNS = ["overthinking", "avoidance", "self_doubt", "frustration"]
POSITIVE_PATTERNS = ["clarity", "momentum", "discipline", "creative_flow"]

# ==================================================
# PHASE SETS
# ==================================================
PHASE_SETS = {
    "Student": ["Welcome", "Warm-Up", "Training", "Cool Down"],
    "Practitioner": ["Welcome", "Warm-Up", "Training", "Cool Down"],
    "Sentinel": ["Welcome", "Warm-Up", "Training", "Cool Down"],
    "Sovereign": ["Welcome", "Warm-Up", "Training", "Cool Down"]
}

# ==================================================
# AUTH
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
# TONE & VOICE SYSTEM
# ==================================================
TONE_MODES = ["crisis", "depression", "anxiety", "sadness", "boredom", "excitement", "advice", "just_listen"]

RANK_VOICE = {
    "Student": "gentle and curious — ask open questions to help the practitioner explore gently. Never push. Earn trust slowly.",
    "Practitioner": "observant and pattern-naming — quietly point out recurring themes without judgment. 'This sounds familiar — what do you notice?'",
    "Sentinel": "clear and direct mirror — hold up an honest reflection of what is seen. Name patterns without cushioning. Trust them to handle it.",
    "Sovereign": "peer-level and blunt — speak as an equal. Honest and grounded. They've earned truth over comfort. 'You already know this — say it.'"
}

def get_voice_for_count(count):
    if count < 15:
        band = "Student"
        weight = count / 15.0
    elif count < 40:
        band = "Practitioner"
        weight = (count - 15) / 25.0
    elif count < 80:
        band = "Sentinel"
        weight = (count - 40) / 40.0
    else:
        band = "Sovereign"
        weight = 1.0
    prev_map = {"Practitioner": "Student", "Sentinel": "Practitioner", "Sovereign": "Sentinel"}
    if weight < 0.4 and band in prev_map:
        return RANK_VOICE[prev_map[band]]
    return RANK_VOICE[band]

def detect_tone_mode(message):
    prompt = f"""
Analyze this practitioner reflection and classify its dominant emotional/energetic tone.
Return JSON only with ONE of these exact modes: {', '.join(TONE_MODES)}
Reflection:
{message}
{{"tone": "one_of_the_modes"}}
"""
    headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": prompt}]},
            headers=headers
        )
        content = res.json()["choices"][0]["message"]["content"]
        start = content.find("{")
        end = content.rfind("}") + 1
        data = json.loads(content[start:end])
        tone = data.get("tone", "just_listen")
        return tone if tone in TONE_MODES else "just_listen"
    except:
        return "just_listen"

# ==================================================
# THOUGHT LOOP DETECTION
# ==================================================
def detect_thought_loop(user_id, current_message, window=6):
    try:
        r = supabase.table("records") \
            .select("content") \
            .eq("user_id", user_id) \
            .eq("role", "user") \
            .order("timestamp", desc=True) \
            .limit(window) \
            .execute()
        if not r.data or len(r.data) < 3:
            return False, None
        recent_msgs = [row["content"] for row in r.data]
        history_text = "\n".join([f"- {m}" for m in recent_msgs])
        prompt = f"""
You are detecting if the practitioner is in a thought loop.
Previous reflections (most recent first):
{history_text}
Current new reflection:
{current_message}
Is the core underlying theme, fear, avoidance, or doubt semantically repeating — same emotional core even if worded differently?
Answer with JSON only:
{{"is_loop": true, "loop_theme": "short description"}}
or
{{"is_loop": false, "loop_theme": null}}
"""
        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": prompt}]},
            headers=headers
        )
        content = res.json()["choices"][0]["message"]["content"]
        start = content.find("{")
        end = content.rfind("}") + 1
        data = json.loads(content[start:end])
        return data.get("is_loop", False), data.get("loop_theme", None)
    except Exception as e:
        print(f"Loop detection error: {e}")
        return False, None

# ==================================================
# PATTERN DETECTION
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

user_reflection_count = supabase.table("records") \
    .select("id", count="exact") \
    .eq("user_id", USER_ID) \
    .eq("role", "user") \
    .execute().count or 0
rank = compute_rank(user_reflection_count)

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
    score = sum(
        1 if p["pattern"] in POSITIVE_PATTERNS else -1 if p["pattern"] in NEGATIVE_PATTERNS else 0
        for p in r.data
    )
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
    score = sum(
        1 if p["pattern"] in POSITIVE_PATTERNS else -1 if p["pattern"] in NEGATIVE_PATTERNS else 0
        for p in r.data
    )
    if score > 3:
        return "Rising"
    if score < -3:
        return "Declining"
    return "Stable"

# ==================================================
# TOP PATTERN
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
# TRAJECTORY PLOT
# ==================================================
def plot_trajectory():
    r = supabase.table("dojo_patterns") \
        .select("pattern, timestamp") \
        .eq("user_id", USER_ID) \
        .order("timestamp") \
        .execute()
    if not r.data or len(r.data) < 5:
        return None
    df = pd.DataFrame(r.data)
    df['score'] = df['pattern'].apply(
        lambda p: 1 if p in POSITIVE_PATTERNS else -1 if p in NEGATIVE_PATTERNS else 0
    )
    df['index'] = range(len(df))
    df['rolling_avg'] = df['score'].rolling(window=5, min_periods=1).mean()
    x = df['index'].values
    y = df['rolling_avg'].values
    projection = None
    if len(x) >= 2:
        coeffs = np.polyfit(x, y, 1)
        future_x = np.array([x[-1] + i for i in range(1, 6)])
        projection = np.polyval(coeffs, future_x)
    fig, ax = plt.subplots(figsize=(8, 4), facecolor='#0a0a0a')
    ax.set_facecolor('#0a0a0a')
    ax.plot(df['index'], df['score'], color='grey', alpha=0.4, label='Raw Score')
    ax.plot(df['index'], df['rolling_avg'], color='#b22222', linewidth=2.5, label='Rolling Avg (5)')
    if projection is not None:
        ax.plot(
            np.concatenate(([x[-1]], future_x)),
            np.concatenate(([y[-1]], projection)),
            color='white', linestyle='--', linewidth=1.5, label='Projection'
        )
    ax.axhline(0, color='gray', linestyle='--', alpha=0.5)
    ax.set_title("Your Trajectory", color='white')
    ax.set_xlabel("Session Index", color='lightgray')
    ax.set_ylabel("Momentum Score", color='lightgray')
    ax.tick_params(colors='lightgray')
    ax.legend(facecolor='#1a1a1a', edgecolor='gray', labelcolor='white')
    ax.grid(True, alpha=0.15, color='gray')
    plt.tight_layout()
    return fig

# ==================================================
# SIDEBAR
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
# TABS
# ==================================================
tab_train, tab_trajectory, tab_history = st.tabs(["Training", "Trajectory", "History"])

# ==================================================
# TRAJECTORY TAB
# ==================================================
with tab_trajectory:
    st.markdown("### Your Path")
    fig = plot_trajectory()
    if fig:
        st.pyplot(fig)
    else:
        st.info("Keep training — trajectory builds after 5 sessions.")

# ==================================================
# TRAINING TAB
# ==================================================
with tab_train:
    st.markdown("### Dojo Awareness")
    if st.session_state.milestone_message:
        st.success(st.session_state.milestone_message)
        st.session_state.milestone_message = None
    st.divider()
    for msg in st.session_state.msgs[-10:]:
        avatar = "🧑‍🎓" if msg["role"] == "user" else "🧘‍♂️"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
    prompt = st.chat_input("What arises in your mind?")
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
            detected_pattern, confidence = detect_pattern_for_message(USER_ID, prompt)
            tone_mode = detect_tone_mode(prompt)
            is_loop, loop_theme = detect_thought_loop(USER_ID, prompt)
            voice_instruction = get_voice_for_count(user_reflection_count)
            persistent_pattern = None
            try:
                rp = supabase.table("dojo_patterns") \
                    .select("pattern") \
                    .eq("user_id", USER_ID) \
                    .order("timestamp", desc=True) \
                    .limit(3) \
                    .execute()
                if rp.data and len(rp.data) == 3:
                    if rp.data[0]["pattern"] == rp.data[1]["pattern"] == rp.data[2]["pattern"]:
                        persistent_pattern = rp.data[0]["pattern"]
            except:
                pass
            mirror = ""
            if persistent_pattern:
                mirror = f"I notice **{persistent_pattern.replace('_', ' ')}** appearing repeatedly in your reflections.\n\n"
            loop_instruction = ""
            if is_loop and loop_theme:
                loop_instruction = f"""
LOOP DETECTED: The practitioner is circling '{loop_theme}' again.
Do NOT name the loop directly. Approach from a completely different angle.
Ask a question they have not been asked before. Interrupt the pattern with novelty, not confrontation.
"""
            tone_instruction = f"Current emotional tone: {tone_mode}. Adapt accordingly — more grounding for anxiety, more presence for sadness, more curiosity for boredom, pure witness for just_listen, immediate calm anchoring for crisis."
            mentor_prompt = f"""
You are a calm, disciplined mentor guiding a practitioner through reflection.
Your role: help them observe patterns in thinking and behavior.
Never give direct advice. Guide with questions, clarity, and grounded insight.
Voice style: {voice_instruction}
{tone_instruction}
{loop_instruction}
{mirror}
If appropriate, weave in this teaching naturally:
{doctrine}
CRITICAL LENGTH RULES — FOLLOW EXACTLY OR RESPONSE WILL BE REJECTED:
1. LIGHT/NEUTRAL INPUT → 1-2 sentences max
2. MODERATE INPUT → 3-5 sentences, single paragraph
3. HEAVY INPUT → 2 short paragraphs max (100-150 words total)
Tone: grounded, non-judgmental, quietly supportive. No fluff, no lectures.
End in a way that invites continuation unless resolved.
"""
            try:
                headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
                res = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "system", "content": mentor_prompt}] + st.session_state.msgs[-10:]
                    },
                    headers=headers
                )
                reply = res.json()["choices"][0]["message"]["content"]
            except Exception:
                reply = "The mentor pauses for a moment. Please try again."
        words = reply.split()
        if len(words) > 150:
            reply = ' '.join(words[:150]) + "… (mentor pauses — reflect before continuing)"
        if st.session_state.msgs and st.session_state.msgs[-1]["role"] == "assistant" and st.session_state.msgs[-1]["content"] == reply:
            pass
        else:
            with st.chat_message("assistant", avatar="🧘‍♂️"):
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

# ==================================================
# HISTORY TAB
# ==================================================
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
            avatar = "🧑‍🎓" if row["role"] == "user" else "🧘‍♂️"
            with st.chat_message(row["role"], avatar=avatar):
                st.markdown(row["content"])
