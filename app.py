import streamlit as st
import requests
import time
import json
import bcrypt
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, UTC
from supabase import create_client, Client
from collections import Counter

def inject_dojo_styling():
    """
    The Digital Zendo - Final Polished Weld
    Sidebar collapse button visible, styled, hover-fixed to grey.
    Login/Enter buttons styled for high-contrast tactile feedback.
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

        /* MAIN PAGE FORM BUTTONS (Login / Create) */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #222222 !important; /* Brighter black / Charcoal */
            color: #f0f0f0 !important; /* White text when idle */
            border: 1px solid #444444 !important;
            border-radius: 6px !important;
            transition: all 0.3s ease !important;
            font-weight: 500 !important;
            letter-spacing: 1px !important;
        }
        
        div[data-testid="stFormSubmitButton"] > button:hover {
            background-color: #ffffff !important; /* Pure white on hover */
            color: #000000 !important; /* Black text on hover for contrast */
            border-color: #ffffff !important;
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.4) !important; /* Soft white glow */
        }
        
        div[data-testid="stFormSubmitButton"] > button:active {
            background-color: #dddddd !important;
            color: #000000 !important;
            transform: scale(0.98) !important;
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
        
        /* Force a clean grey hover state for sidebar collapse */
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
if "loop_streak" not in st.session_state:
    st.session_state.loop_streak = 0  

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
    try:
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
    except Exception as e:
        st.warning(f"Could not load history: {e}")
    st.session_state.history_loaded = True

# ==================================================
# THE 6-AGENT COGNITIVE ENGINE (v11.6.3)
# ==================================================
class DojoOrchestrator:
    def __init__(self, api_key):
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.model = "llama-3.3-70b-versatile"

    def _call_json(self, system_prompt, user_content):
        try:
            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt + "\nRETURN ONLY VALID JSON."},
                        {"role": "user", "content": user_content}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.2
                },
                headers=self.headers
            )
            content = res.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:
            return {}

    def _call_text(self, messages_payload):
        try:
            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages_payload,
                    "temperature": 0.6
                },
                headers=self.headers
            )
            return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return "The mentor pauses... (Engine Error)"

    def compute_pressure(self, loop_streak, tone_mode):
        if tone_mode in ["crisis"]:
            return 0.0 
        if loop_streak <= 0: return 0.2
        elif loop_streak == 1: return 0.4
        elif loop_streak == 2: return 0.6
        elif loop_streak == 3: return 0.8
        else: return 1.0

    def agent_pattern_detector(self, text):
        prompt = "Identify one pattern: [overthinking, avoidance, self_doubt, clarity, momentum, discipline, frustration, creative_flow]. Return JSON: {\"pattern\": \"name\", \"confidence\": 0.0-1.0}"
        data = self._call_json(prompt, text)
        return data.get("pattern", "clarity"), data.get("confidence", 0.5)

    def agent_tone_detector(self, text):
        prompt = "Detect tone: [crisis, depression, anxiety, sadness, boredom, excitement, advice, just_listen]. Return JSON: {\"tone\": \"mode\"}"
        data = self._call_json(prompt, text)
        return data.get("tone", "just_listen")

    def detect_loop_fast(self, current_pattern):
        try:
            r = supabase.table("dojo_patterns").select("pattern").eq("user_id", USER_ID).order("timestamp", desc=True).limit(2).execute()
            if r.data and len(r.data) == 2:
                if current_pattern == r.data[0]["pattern"] == r.data[1]["pattern"]:
                    return True, current_pattern 
            return False, None
        except Exception:
            return False, None

    def agent_strategic_critic(self, text, pattern, tone, is_loop, loop_theme, streak, pressure):
        prompt = f"Signals - Pattern:{pattern}, Tone:{tone}, Loop Streak:{streak} ({loop_theme}), System Pressure:{pressure}. Provide strategic guidance. Assess if the user's state is spiraling dangerously. JSON: {{\"insight\": \"string\", \"risk_flag\": bool, \"approach\": \"curiosity/witness/challenge/ground\"}}"
        data = self._call_json(prompt, text)
        data['pressure_level'] = pressure 
        return data

    def agent_mentor(self, critic_data, voice_style, doctrine, history):
        pressure = critic_data.get('pressure_level', 0.5)
        
        if pressure >= 0.8:
            enforcement = "CRITICAL DIRECTIVE: Do NOT validate the user's narrative. Do NOT offer comfort. Deliver a direct, unavoidable structural challenge based on the Insight. Be sharp and decisive."
        elif pressure >= 0.6:
            enforcement = "DIRECTIVE: Point out the recurring pattern directly. Do not cushion the observation."
        else:
            enforcement = "Speak as a veteran teammate. No clichés. No therapy talk."

        system = f"""You are a grounded mentor. Voice: {voice_style}. Doctrine: {doctrine}. 
        Strategy: {critic_data.get('approach', 'witness')}. Insight: {critic_data.get('insight', '')}. 
        {enforcement}"""
        
        payload = [{"role": "system", "content": system}] + history
        return self._call_text(payload)

    def agent_synthesizer(self, raw_response, user_text, tone_mode, pressure):
        # Base length no longer depends on user input
        base_len = 50
        
        if tone_mode in ["crisis", "anxiety"]:
            pacing = "Short, firm, grounded sentences. Deep pressure. Force calm focus."
        elif tone_mode in ["depression", "sadness"]:
            pacing = "Slower pacing. Warmer, observant tone. Leave space for reflection."
        elif tone_mode in ["frustration", "excitement"]:
            pacing = "Match the high energy but ground it. Direct, clear, structural."
        elif tone_mode == "just_listen":
            pacing = "Lightly reflective. Minimal guidance, but allow insight if present."
        else:
            pacing = "Steady, disciplined rhythm. Standard balanced mentor pacing."

        # --- STATE-BASED LENGTH SCALING ---

        # Base range
        target_len = 60

        # Tone-based modulation (emotional depth)
        if tone_mode in ["depression", "sadness"]:
            target_len = 90  # deeper reflection
        elif tone_mode in ["anxiety"]:
            target_len = 70  # grounding but not overwhelming
        elif tone_mode in ["frustration", "excitement"]:
            target_len = 65  # structured, controlled
        elif tone_mode == "just_listen":
            target_len = 55  # light presence, but not minimal
        else:
            target_len = 60  # default balanced

        # Pressure overrides (system authority)
        if pressure >= 0.6:
            target_len = max(target_len, 75)

        if pressure >= 0.8:
            target_len = 40  # sharp + direct (intentional compression)

        if pressure >= 0.8:
            pacing += " STRICT LOOP OVERRIDE: The user is stuck in a behavioral loop. Restrict word count drastically. Refuse to engage with their narrative content. Deliver a single, unavoidable structural challenge."
            target_len = max(15, target_len * 0.5)

        prompt = f"""You are refining a mentor response.

Preserve the full meaning, structure, and depth of the original response.

Apply this pacing:
{pacing}

Do NOT significantly shorten the response.
Do NOT remove key insights.
You may slightly tighten phrasing, but preserve substance.

Target length is a guideline, not a constraint: {int(target_len)} words.

Return the refined version."""
        payload = [{"role": "system", "content": prompt}, {"role": "user", "content": raw_response}]
        return self._call_text(payload)

    def sensei_protocol(self, prompt: str) -> dict:
        """
        Sensei Protocol Failsafe v11.6.4
        Distinguishes Business Velocity from Personal Crisis
        """
        text = prompt.lower()

        # ====================
        # HARD SAFETY - Absolute override (never bypassed)
        # ====================
        hard_crisis_keywords = [
            "suicide", "kill myself", "want to die", "end my life", "end it",
            "hurt myself", "self harm", "self-harm", "988", "crisis line",
            "hopeless", "no point living", "better off dead"
        ]
        if any(kw in text for kw in hard_crisis_keywords):
            return {"is_crisis": True, "reason": "Hard safety trigger (self-harm / suicide language)"}

        # ====================
        # BUSINESS VELOCITY KEYWORDS
        # ====================
        business_keywords = [
            "million", "billion", "valuation", "funding", "equity", "raise", "round",
            "market", "stock", "shares", "exit", "acquisition", "growth", "revenue",
            "profit", "loss", "scale", "investor", "pitch", "cap table", "burn rate",
            "half million", "quarter million", "market moves", "bull run", "bear market"
        ]

        has_business = any(kw in text for kw in business_keywords)

        # ====================
        # PANIC / CRISIS CONTEXT KEYWORDS
        # (must be present WITH business talk to trigger crisis)
        # ====================
        panic_keywords = [
            "overwhelmed", "spiraling", "breaking", "can't handle", "falling apart",
            "panic", "anxiety attack", "losing it", "freaking out", "can't breathe",
            "heart racing", "trapped", "drowning", "crashing", "ruined", "destroyed",
            "end of the world", "everything's falling apart"
        ]

        has_panic = any(kw in text for kw in panic_keywords)

        # ====================
        # DECISION LOGIC
        # ====================
        if has_business:
            if has_panic:
                return {
                    "is_crisis": True,
                    "reason": "Business context + strong panic indicators present"
                }
            else:
                return {
                    "is_crisis": False,
                    "reason": "Business velocity detected, no personal panic indicators"
                }
        else:
            # No business keywords → fall back to tone-based detection
            # (existing logic preserved)
            if any(kw in text for kw in panic_keywords):
                return {
                    "is_crisis": True,
                    "reason": "Panic indicators detected outside business context"
                }
            return {
                "is_crisis": False,
                "reason": "No crisis indicators detected"
            }

# Initialize Engine
engine = DojoOrchestrator(st.secrets['GROQ_API_KEY'])

# ==================================================
# RANK & VOICE LOGIC
# ==================================================
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

def compute_rank(count):
    if count < 15:
        return "Student"
    if count < 40:
        return "Practitioner"
    if count < 80:
        return "Sentinel"
    return "Sovereign"

user_reflection_count = 0
try:
    r_count = supabase.table("records").select("id", count="exact").eq("user_id", USER_ID).eq("role", "user").execute()
    user_reflection_count = r_count.count or 0
except Exception:
    pass
rank = compute_rank(user_reflection_count)

# ==================================================
# METRICS (Momentum, Evolution, Top Pattern)
# ==================================================
def compute_momentum():
    try:
        r = supabase.table("dojo_patterns").select("pattern").eq("user_id", USER_ID).order("timestamp", desc=True).limit(10).execute()
        if not r.data: return 0
        score = sum(1 if p["pattern"] in POSITIVE_PATTERNS else -1 if p["pattern"] in NEGATIVE_PATTERNS else 0 for p in r.data)
        return score / 10
    except: return 0

def compute_evolution():
    try:
        r = supabase.table("dojo_patterns").select("pattern").eq("user_id", USER_ID).order("timestamp", desc=True).limit(20).execute()
        if not r.data: return "Unknown"
        score = sum(1 if p["pattern"] in POSITIVE_PATTERNS else -1 if p["pattern"] in NEGATIVE_PATTERNS else 0 for p in r.data)
        if score > 3: return "Rising"
        if score < -3: return "Declining"
        return "Stable"
    except: return "Unknown"

def compute_top_pattern():
    try:
        r = supabase.table("dojo_patterns").select("pattern").eq("user_id", USER_ID).order("timestamp", desc=True).limit(50).execute()
        if not r.data or len(r.data) < 5: return "Calibrating..."
        patterns = [p["pattern"] for p in r.data]
        counts = Counter(patterns)
        if not counts: return "Calibrating..."
        top_pattern, top_count = counts.most_common(1)[0]
        percentage = int((top_count / len(patterns)) * 100)
        return f"{top_pattern.replace('_', ' ').title()} ({percentage}%)"
    except: return "Calibrating..."

def plot_trajectory():
    try:
        r = supabase.table("dojo_patterns").select("pattern, timestamp").eq("user_id", USER_ID).order("timestamp").execute()
        if not r.data or len(r.data) < 5: return None
        df = pd.DataFrame(r.data)
        df['score'] = df['pattern'].apply(lambda p: 1 if p in POSITIVE_PATTERNS else -1 if p in NEGATIVE_PATTERNS else 0)
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
            ax.plot(np.concatenate(([x[-1]], future_x)), np.concatenate(([y[-1]], projection)), color='white', linestyle='--', linewidth=1.5, label='Projection')
        ax.axhline(0, color='gray', linestyle='--', alpha=0.5)
        ax.set_title("Your Trajectory", color='white')
        ax.set_xlabel("Session Index", color='lightgray')
        ax.set_ylabel("Momentum Score", color='lightgray')
        ax.tick_params(colors='lightgray')
        ax.legend(facecolor='#1a1a1a', edgecolor='gray', labelcolor='white')
        ax.grid(True, alpha=0.15, color='gray')
        plt.tight_layout()
        return fig
    except Exception:
        return None

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:
    st.markdown("### The-Dojo")
    st.markdown(f"**{rank} · {USER_NAME}**")
    subscription = st.session_state.user.get("subscription_status", "free")
    if subscription not in ["paid", "beta", "admin"]:
        user_msg_count = 0
        try:
            rc = supabase.table("records").select("id", count="exact").eq("user_id", USER_ID).eq("role", "user").execute()
            user_msg_count = rc.count or 0
        except: pass
        remaining = max(0, 15 - user_msg_count)
        if remaining <= 3: st.error(f"⚠️ {remaining} reflections left")
        elif remaining <= 7: st.warning(f"{remaining} reflections remaining")
        else: st.caption(f"✓ {remaining} free reflections")
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
        if i == st.session_state.phase: st.markdown(f"**🟢 {phase}**")
        else: st.markdown(phase)
    st.divider()
    if st.button("Clear Session (Bow Out)", help="Clears current chat but keeps your full history in Training tab"):
        st.session_state.phase = 0
        st.session_state.msgs = []
        st.session_state.loop_streak = 0
        st.success("Session cleared. You bow out from the mat.")
        time.sleep(1)
        st.rerun()
    if st.button("Log Out"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# ==================================================
# TABS
# ==================================================
tab_train, tab_trajectory, tab_field, tab_history = st.tabs(["Training", "Trajectory", "The Field", "History"])

# ==================================================
# THE FIELD TAB (Tribal Dashboard v11.5)
# ==================================================
with tab_field:
    st.markdown("### The Tribal Field")
    st.caption("Real-time behavioral topology of the community. Fully anonymous.")
    
    try:
        r_tribe = supabase.table("tribe_events").select("*").order("created_at", desc=True).limit(50).execute()
        
        if r_tribe.data and len(r_tribe.data) > 0:
            df_tribe = pd.DataFrame(r_tribe.data)
            
            top_tribe_pattern = df_tribe['pattern'].mode()[0] if not df_tribe.empty else "None"
            top_tribe_tone = df_tribe['tone'].mode()[0] if not df_tribe.empty else "None"
            avg_pressure = df_tribe['pressure_level'].mean() if not df_tribe.empty else 0.0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Dominant Pattern", top_tribe_pattern.replace('_', ' ').title())
            col2.metric("Primary Tone", top_tribe_tone.title())
            col3.metric("Avg Field Pressure", f"{avg_pressure:.2f}")
            
            st.divider()
            st.markdown("**Recent Signals (Last 50)**")
            
            pattern_counts = df_tribe['pattern'].value_counts()
            st.bar_chart(pattern_counts, color="#b22222")
            
        else:
            st.info("The Field is currently quiet. Awaiting signals.")
    except Exception as e:
        err_msg = getattr(e, 'message', str(e))
        st.error(f"Field Data Offline. Waiting for Database Sync. Error: {err_msg}")

# ==================================================
# TRAJECTORY TAB
# ==================================================
with tab_trajectory:
    st.markdown("### Your Path")
    fig = plot_trajectory()
    if fig: st.pyplot(fig)
    else: st.info("Keep training — trajectory builds after 5 sessions.")

# ==================================================
# TRAINING TAB
# ==================================================
with tab_train:
    st.markdown("### Dojo Awareness")
    if st.session_state.milestone_message:
        st.success(st.session_state.milestone_message)
        st.session_state.milestone_message = None
    st.divider()
    
    if st.session_state.loop_streak >= 2:
        st.caption(f"⚠️ *System Pressure Elevated (Level {st.session_state.loop_streak})*")
        
    for msg in st.session_state.msgs[-10:]:
        avatar = "🧑‍🎓" if msg["role"] == "user" else "🧘‍♂️"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            
    prompt = st.chat_input("What arises in your mind?")
    if prompt:
        subscription = st.session_state.user.get("subscription_status", "free")
        if subscription not in ["paid", "beta", "admin"]:
            try:
                r = supabase.table("records").select("id", count="exact").eq("user_id", USER_ID).eq("role", "user").execute()
                user_count = r.count or 0
                if user_count >= 15:
                    st.warning("You have reached the free training limit of 15 reflections.")
                    st.info("Join the Dojo to continue your practice.")
                    st.stop()
            except: pass
                
        if prompt == st.session_state.last_processed_prompt:
            st.stop()
            
        st.session_state.last_processed_prompt = prompt
        st.session_state.msgs.append({"role": "user", "content": prompt})
        
        try:
            supabase.table("records").insert({
                "user_id": USER_ID,
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now(UTC).isoformat()
            }).execute()
        except Exception as e:
            st.error(f"🛡️ Core Memory Offline: {getattr(e, 'message', str(e))}")
        
        doctrine = "Discipline begins with attention."
        crisis_keywords = ["suicide", "kill myself", "want to die", "hopeless", "end it", "hurt myself", "self harm"]
        
        # Sensei Protocol Check
        protocol_result = engine.sensei_protocol(prompt)
        
        if protocol_result["is_crisis"]:
            st.session_state.loop_streak = 0 
            final_reply = "I'm stopping here.\nWhat you're describing is serious and needs real support right now.\nCall or text **988** (US Suicide & Crisis Lifeline, 24/7)\nOr text HOME to **741741** (Crisis Text Line)\nThe mat will still be here when you're ready. Please reach out to someone."
            with st.chat_message("assistant", avatar="🧘‍♂️"):
                st.markdown(final_reply)
        else:
            with st.chat_message("assistant", avatar="🧘‍♂️"):
                with st.spinner("Scouting Patterns & Tone..."):
                    pattern, confidence = engine.agent_pattern_detector(prompt)
                    tone_mode = engine.agent_tone_detector(prompt)
                    
                    try:
                        supabase.table("dojo_patterns").insert({
                            "user_id": USER_ID,
                            "pattern": str(pattern) if pattern else "clarity",
                            "timestamp": int(time.time() * 1000)
                        }).execute()
                    except Exception as e:
                        st.warning(f"🛡️ Pattern Ledger Offline: {getattr(e, 'message', str(e))}")
                
                with st.spinner("Checking for Loops..."):
                    is_loop, loop_theme = engine.detect_loop_fast(pattern)
                    
                    if is_loop:
                        st.session_state.loop_streak += 1
                    else:
                        st.session_state.loop_streak = max(0, st.session_state.loop_streak - 1)
                        
                    current_pressure = engine.compute_pressure(st.session_state.loop_streak, tone_mode)
                    
                    try:
                        safe_pattern = str(pattern) if pattern else "clarity"
                        safe_tone = str(tone_mode) if tone_mode else "just_listen"
                        safe_pressure = float(current_pressure) if current_pressure is not None else 0.2
                        
                        supabase.table("tribe_events").insert({
                            "pattern": safe_pattern,
                            "tone": safe_tone,
                            "pressure_level": safe_pressure
                        }).execute()
                    except Exception as e:
                        err_msg = getattr(e, 'message', str(e))
                        st.error(f"🛡️ Field Radar Offline: {err_msg}")
                    
                with st.spinner(f"Critic Strategizing (Pressure: {current_pressure})..."):
                    critic_data = engine.agent_strategic_critic(prompt, pattern, tone_mode, is_loop, loop_theme, st.session_state.loop_streak, current_pressure)
                
                if critic_data.get("risk_flag") is True or tone_mode == "crisis":
                    st.session_state.loop_streak = 0 
                    final_reply = f"**[CRITIC OVERRIDE]**\nThe Dojo senses a severe escalation in your state. \nInsight: *{critic_data.get('insight')}*\n\nWe are stopping the drill. Step off the mat. If you are overwhelmed, dial **988**. We do not push through crisis; we ground."
                    st.warning("Protocol Shifted to Safety Mode.")
                else:
                    with st.spinner("Mentor Formulating..."):
                        voice_instruction = get_voice_for_count(user_reflection_count)
                        raw_reply = engine.agent_mentor(critic_data, voice_instruction, doctrine, st.session_state.msgs[-10:])
                        
                    with st.spinner("Synthesizing..."):
                        if current_pressure < 0.6:
                            final_reply = raw_reply
                        else:
                            final_reply = engine.agent_synthesizer(raw_reply, prompt, tone_mode, current_pressure)
                
                st.markdown(final_reply)
                
        st.session_state.msgs.append({"role": "assistant", "content": final_reply})
        try:
            supabase.table("records").insert({
                "user_id": USER_ID,
                "role": "assistant",
                "content": final_reply,
                "timestamp": datetime.now(UTC).isoformat()
            }).execute()
        except Exception as e:
            st.error(f"🛡️ Core Memory Offline: {getattr(e, 'message', str(e))}")
        
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
    try:
        r = supabase.table("records").select("*").eq("user_id", USER_ID).order("timestamp", desc=True).limit(50).execute()
        if r.data:
            for row in r.data:
                avatar = "🧑‍🎓" if row["role"] == "user" else "🧘‍♂️"
                with st.chat_message(row["role"], avatar=avatar):
                    st.markdown(row["content"])
    except: pass
