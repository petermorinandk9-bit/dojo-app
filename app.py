import streamlit as st
import requests
import time
import random
import json
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

USER_ID = st.session_state.user["id"]
USER_NAME = st.session_state.user["display_name"]

# ==================================================
# SESSION STATE
# ==================================================
if "msgs" not in st.session_state:
    st.session_state.msgs = []
    st.session_state.phase = 0

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
# PATTERN DETECTION ENGINE
# ==================================================
def detect_patterns(user_id):
    # Fetch recent user messages (last 50)
    recent_msgs = supabase.table("records")\
        .select("content")\
        .eq("user_id", user_id)\
        .eq("role", "user")\
        .order("timestamp", desc=True)\
        .limit(50)\
        .execute()

    if not recent_msgs.data or len(recent_msgs.data) < 10:
        return  # too few messages to detect patterns

    reflections = [row["content"] for row in recent_msgs.data]

    pattern_prompt = f"""
You are a perceptive pattern analyst. Review the user's recent reflections below.

Prioritize detecting NEGATIVE recurring patterns (highest priority):
- avoidant behavior / procrastination
- hesitation or overanalysis before decisions
- chronic self-criticism / negative self-talk loops
- abandonment of projects or commitments
- impulsive decisions followed by regret
- blame shifting or externalizing responsibility

Also detect positive patterns (secondary):
- growing discipline / consistency
- sustained curiosity / exploration
- reflective self-awareness

Only report patterns that clearly appear at least 3 times across messages.
Use neutral, observational language — no judgments or labels like "you are avoidant".

For each detected pattern, provide:
- pattern: short, precise, neutral description (do NOT include trajectory words like strengthening/weakening)
- confidence: float between 0.0 and 1.0 (higher = stronger repetition & clarity)

Return ONLY valid JSON — no extra text, no explanations:

{{
  "patterns": [
    {{"pattern": "Recurring hesitation before committing to decisions.", "confidence": 0.78}},
    {{"pattern": "Repeated self-critical evaluation of progress.", "confidence": 0.65}}
  ]
}}

Reflections (most recent first):
{chr(10).join(f"- {r}" for r in reflections)}
"""

    headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
    res = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": pattern_prompt}],
            "temperature": 0.15,
            "max_tokens": 400
        },
        headers=headers
    )

    try:
        content = res.json()["choices"][0]["message"]["content"].strip()
        if content.startswith("```json"):
            content = content.split("```json")[1].split("```")[0].strip()
        data = json.loads(content)
        detected_patterns = data.get("patterns", [])

        for p in detected_patterns:
            pattern_text = p.get("pattern")
            new_confidence = float(p.get("confidence", 0.5))

            if not pattern_text or new_confidence < 0.4:
                continue

            # Check for similar existing pattern
            existing = supabase.table("dojo_patterns")\
                .select("id, pattern, confidence_score")\
                .eq("user_id", user_id)\
                .ilike("pattern", f"%{pattern_text.split(' —')[0].strip()}%")\
                .order("timestamp", desc=True)\
                .limit(1)\
                .execute()

            now_iso = datetime.utcnow().isoformat()

            if existing.data:
                # Update existing pattern
                old_confidence = existing.data[0]["confidence_score"]
                diff = new_confidence - old_confidence

                if diff > 0.05:
                    trajectory = "strengthening"
                elif diff < -0.05:
                    trajectory = "weakening"
                else:
                    trajectory = "stable"

                # Check for reversal (simple heuristic: new pattern sentiment opposite to old)
                old_text = existing.data[0]["pattern"].lower()
                new_text = pattern_text.lower()
                negative_words = ["hesitation", "avoid", "self-critical", "abandon", "impulsive", "blame"]
                if any(w in old_text for w in negative_words) and not any(w in new_text for w in negative_words):
                    trajectory = "reversing"
                elif any(w in new_text for w in negative_words) and not any(w in old_text for w in negative_words):
                    trajectory = "reversing"

                supabase.table("dojo_patterns")\
                    .update({
                        "pattern": pattern_text,
                        "confidence_score": new_confidence,
                        "trajectory_state": trajectory,
                        "timestamp": now_iso
                    })\
                    .eq("id", existing.data[0]["id"])\
                    .execute()
            else:
                # Insert new pattern
                supabase.table("dojo_patterns").insert({
                    "user_id": user_id,
                    "pattern": pattern_text,
                    "confidence_score": new_confidence,
                    "trajectory_state": "emerging",
                    "timestamp": now_iso
                }).execute()

        # Simple cluster detection (run after individual patterns)
        recent_patterns = supabase.table("dojo_patterns")\
            .select("pattern")\
            .eq("user_id", user_id)\
            .order("timestamp", desc=True)\
            .limit(20)\
            .execute()

        if len(recent_patterns.data) >= 4:
            pattern_list = [p["pattern"] for p in recent_patterns.data]
            from collections import Counter
            pairs = Counter()
            for i in range(len(pattern_list)):
                for j in range(i+1, len(pattern_list)):
                    pair = tuple(sorted([pattern_list[i], pattern_list[j]]))
                    pairs[pair] += 1

            for (p1, p2), count in pairs.items():
                if count >= 3:  # appeared together at least 3 times in recent history
                    cluster_name = f"{p1.split('.')[0].strip()} + {p2.split('.')[0].strip()}"
                    cluster_conf = min(0.9, 0.4 + count * 0.1)

                    existing_cluster = supabase.table("dojo_pattern_clusters")\
                        .select("*")\
                        .eq("user_id", user_id)\
                        .eq("cluster_name", cluster_name)\
                        .execute()

                    if existing_cluster.data:
                        supabase.table("dojo_pattern_clusters")\
                            .update({
                                "confidence_score": cluster_conf,
                                "timestamp": now_iso
                            })\
                            .eq("id", existing_cluster.data[0]["id"])\
                            .execute()
                    else:
                        supabase.table("dojo_pattern_clusters").insert({
                            "user_id": user_id,
                            "cluster_name": cluster_name,
                            "patterns": f"{p1} | {p2}",
                            "confidence_score": cluster_conf,
                            "timestamp": now_iso
                        }).execute()

    except Exception:
        pass  # silent fail

# ==================================================
# ENHANCED PATTERN MEMORY FETCH
# ==================================================
def get_current_pattern_memory():
    # Fetch patterns with priority: strengthening > highest confidence > most recent
    patterns = supabase.table("dojo_patterns")\
        .select("pattern, trajectory_state, confidence_score")\
        .eq("user_id", USER_ID)\
        .execute()

    if not patterns.data:
        return "No current pattern detected."

    # Priority 1: any strengthening patterns
    strengthening = [p for p in patterns.data if p["trajectory_state"] == "strengthening"]
    if strengthening:
        top = max(strengthening, key=lambda x: x["confidence_score"])
        return f"Pattern: {top['pattern']}\nTrajectory: {top['trajectory_state']}\nConfidence: {top['confidence_score']:.2f}"

    # Priority 2: highest confidence
    top_conf = max(patterns.data, key=lambda x: x["confidence_score"])
    return f"Pattern: {top_conf['pattern']}\nTrajectory: {top_conf['trajectory_state']}\nConfidence: {top_conf['confidence_score']:.2f}"

# ==================================================
# FETCH LATEST DOCTRINE & MILESTONE
# ==================================================
def fetch_latest(table, field):
    try:
        r = supabase.table(table)\
            .select("*")\
            .eq("user_id", USER_ID)\
            .order("timestamp", desc=True)\
            .limit(1)\
            .execute()

        if r.data:
            return r.data[0][field]
    except:
        pass
    return None

latest_doctrine = fetch_latest("dojo_doctrine", "doctrine")
latest_milestone = fetch_latest("dojo_milestones", "milestone")

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
# SIDEBAR
# ==================================================
with st.sidebar:
    st.markdown("### The-Dojo")
    st.markdown(f"**{rank} · {USER_NAME}**")
    st.divider()

    for i,p in enumerate(PHASE_SETS[rank]):
        if i == st.session_state.phase:
            st.markdown(f"**{p}**")
        else:
            st.markdown(p)

    st.divider()

    if st.button("Bow Out"):
        st.session_state.phase = 0
        st.session_state.msgs = []
        st.success("You bow out from the mat. Training continues tomorrow.")
        time.sleep(1)
        st.rerun()

# ==================================================
# TABS
# ==================================================
tab_train, tab_history = st.tabs(["Training","History"])

# ==================================================
# TRAINING
# ==================================================
with tab_train:
    # ===============================
    # DOJO AWARENESS BANNER
    # ===============================
    with st.container():
        st.markdown("### Dojo Awareness")
        current_pattern_mem = get_current_pattern_memory()
        st.write(f"**Current Pattern Memory:**\n{current_pattern_mem}")
        if latest_doctrine:
            st.write(f"**Recent Doctrine:** {latest_doctrine}")
        if latest_milestone:
            st.write(f"**Recent Milestone:** {latest_milestone}")
        st.write(f"**Current Phase:** {PHASE_SETS[rank][st.session_state.phase]}")
        st.divider()

    # ===============================
    # CHAT HISTORY
    # ===============================
    for msg in st.session_state.msgs[-10:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ===============================
    # USER INPUT (placed last so it appears at bottom)
    # ===============================
    prompt = st.chat_input("Speak from center...")

    if prompt:
        st.session_state.msgs.append({
            "role":"user",
            "content":prompt
        })

        # Run pattern detection roughly every 6–8 user messages
        user_msg_count = len([m for m in st.session_state.msgs if m["role"] == "user"])
        if user_msg_count % 7 == 0 and user_msg_count >= 10:
            detect_patterns(USER_ID)

        session_summary = " ".join(
            [m["content"] for m in st.session_state.msgs if m["role"]=="user"][-3:]
        )

        # ===============================
        # RANK STYLE
        # ===============================
        rank_style = {
            "Student":"supportive instructor who explains ideas clearly",
            "Practitioner":"focused coach giving practical guidance",
            "Sentinel":"reflective strategist who points out patterns",
            "Sovereign":"minimalist mentor who guides through questions"
        }

        # ===============================
        # MASTER PROMPT with upgraded pattern memory
        # ===============================
        current_pattern_mem = get_current_pattern_memory()

        MASTER_PROMPT = f"""
You are a calm, grounded, perceptive human mentor speaking to {USER_NAME}.
Mentor style: {rank_style[rank]}

LONG-TERM MEMORY:
{current_pattern_mem}
Doctrine: {latest_doctrine}
Milestone: {latest_milestone}
(Weave these quietly into your understanding. Never name or point to them directly.)

RECENT CONTEXT:
Session summary: {session_summary}

YOUR OBJECTIVE:
Offer a steady, outside perspective that helps the person notice what they may not yet see clearly — without praising, fixing, or directing.

STRICT COMMUNICATION RULES:
• Look past the surface story to the underlying tension, hesitation, or quiet assumption.
• Never repeat, mirror, echo, or rephrase anything the user said.
• No therapy phrasing, no "I hear," no "it sounds like," no emotional validation.
• Avoid motivational language, pep talks, slogans, corporate-speak.
• No martial arts imagery, dojo references, or teacher–student posturing.
• Speak like a thoughtful, experienced adult — plain, calm, direct, human.
• Match response length to the depth and weight of what the user shared: brief and light for casual or surface-level inputs, longer and more considered (up to 10–12 sentences) only when the reflection is deeper, more personal, or carries real emotional or existential weight. Avoid unnecessary length. Let proportion guide you.

CURRENT STATE:
Rank: {rank}
Phase: {PHASE_SETS[rank][st.session_state.phase]}
"""

        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "model":"llama-3.3-70b-versatile",
                "messages":[{"role":"system","content":MASTER_PROMPT}] + st.session_state.msgs[-10:]
            },
            headers=headers
        )
        reply = res.json()["choices"][0]["message"]["content"]

        thinking_phrases = [
            "Let me think a moment…",
            "Give me a moment to consider this…",
            "Let me reflect on that for a second…",
            "One moment while I think about that…",
            "Let me consider that carefully…"
        ]
        selected_phrase = random.choice(thinking_phrases)

        # Gradual reveal with contemplation first
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown(selected_phrase)

            # Initial contemplation delay
            time.sleep(2.0)

            # Dynamic thinking pause
            char_delay = min(len(reply) / 120, 4)
            time.sleep(char_delay)

            # Reveal response sentence by sentence
            current_text = ""
            sentences = reply.split(". ")
            for i, sentence in enumerate(sentences):
                if i > 0:
                    current_text += ". "
                current_text += sentence
                if i == len(sentences) - 1 and not sentence.endswith("."):
                    current_text += "."
                message_placeholder.markdown(current_text)
                if i < len(sentences) - 1:
                    time.sleep(0.6)

        st.session_state.msgs.append({
            "role":"assistant",
            "content":reply
        })

        if len(st.session_state.msgs) % 4 == 0 and st.session_state.phase < 3:
            st.session_state.phase += 1

        st.rerun()
