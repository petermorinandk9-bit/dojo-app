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
    st.markdown("# The-Dojo")
    st.info(IMPORTANT_NOTICE)
    login_tab, register_tab = st.tabs(["Enter Dojo","Create Account"])
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
                        st.error("No password set for this account. Please contact support.")
                        st.stop()

                    # Normalize to bytes safely
                    if isinstance(stored_hash, str):
                        # Clean any weird characters that might have crept in
                        cleaned = ''.join(c for c in stored_hash if c.isprintable())
                        try:
                            stored_hash_bytes = cleaned.encode('utf-8')
                        except Exception:
                            st.error("Stored password hash is corrupted (encoding issue). Please reset your password.")
                            st.stop()
                    elif isinstance(stored_hash, bytes):
                        stored_hash_bytes = stored_hash
                    else:
                        st.error("Unexpected password hash type in database. Please contact support.")
                        st.stop()

                    # Quick bcrypt format check
                    if not stored_hash_bytes.startswith(b'$2') or len(stored_hash_bytes) < 59:
                        st.error("Stored password is not a valid bcrypt hash. Please reset your password or contact support.")
                        st.stop()

                    try:
                        if bcrypt.checkpw(password.encode('utf-8'), stored_hash_bytes):
                            st.session_state.user = user
                            st.rerun()
                        else:
                            st.error("Incorrect password")
                    except ValueError as ve:
                        if "Invalid salt" in str(ve):
                            st.error("Password hash is corrupted or invalid (invalid salt). Please reset your password.")
                        else:
                            st.error(f"Password verification failed: {str(ve)}")
                    except Exception as e:
                        st.error(f"Unexpected login error: {str(e)}")
                else:
                    st.error("User not found")
    with register_tab:
        with st.form("register"):
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
                hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                hashed_str = hashed_bytes.decode('utf-8')
                supabase.table("users").insert({
                    "username": username,
                    "display_name": display,
                    "password": hashed_str
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
    if count<15:
        return "Student"
    if count<40:
        return "Practitioner"
    if count<80:
        return "Sentinel"
    return "Sovereign"

rank = compute_rank(st.session_state.records_count)

# ==================================================
# PHASES
# ==================================================
PHASE_SETS={
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
# EVOLUTION ENGINE
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
# PATTERN GRAPH & LOOP DETECTION
# ==================================================
def compute_pattern_graph():
    r = supabase.table("dojo_patterns") \
        .select("pattern") \
        .eq("user_id", USER_ID) \
        .order("timestamp") \
        .limit(50) \
        .execute()
    
    if not r.data or len(r.data) < 2:
        return {}
    
    patterns = [row["pattern"] for row in r.data[::-1]]  # oldest to newest
    graph = {}
    
    for i in range(len(patterns) - 1):
        from_p = patterns[i]
        to_p = patterns[i + 1]
        key = (from_p, to_p)
        graph[key] = graph.get(key, 0) + 1
    
    return graph

def detect_pattern_loop(graph):
    if not graph:
        return None
    
    # Find the strongest transition (highest count)
    strongest = max(graph.items(), key=lambda x: x[1])
    (from_p, to_p), count = strongest
    
    if count >= 3:
        return (from_p, to_p, count)
    
    return None

# ==================================================
# PATTERN DETECTION
# ==================================================
def detect_patterns(user_id):
    recent = supabase.table("records") \
        .select("content") \
        .eq("user_id",user_id) \
        .eq("role","user") \
        .order("timestamp",desc=True) \
        .limit(50) \
        .execute()
    if not recent.data or len(recent.data)<10:
        return
    reflections = [row["content"] for row in recent.data]
    prompt = f"""
Choose the best pattern from:
{PATTERN_LIBRARY}
Return JSON only
{{"patterns":[{{"pattern":"name","confidence":0.0}}]}}
"""
    headers = {"Authorization":f"Bearer {st.secrets['GROQ_API_KEY']}"}
    res = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json={
            "model":"llama-3.3-70b-versatile",
            "messages":[{"role":"system","content":prompt}]
        },
        headers=headers
    )
    try:
        content = res.json()["choices"][0]["message"]["content"]
        start = content.find("{")
        end = content.rfind("}") + 1
        if start == -1 or end == 0:
            return
        data = json.loads(content[start:end])
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
# MILESTONES
# ==================================================
def check_milestones():
    user_count = len([m for m in st.session_state.msgs if m["role"] == "user"])
    milestones = {
        1:"First step onto the mat.",
        7:"Consistency begins.",
        30:"Discipline forming.",
        60:"Deep reflection developing."
    }
    if user_count in milestones:
        existing = supabase.table("dojo_milestones") \
            .select("*") \
            .eq("user_id",USER_ID) \
            .eq("milestone",milestones[user_count]) \
            .execute()
        if not existing.data:
            supabase.table("dojo_milestones").insert({
                "user_id":USER_ID,
                "milestone":milestones[user_count],
                "timestamp":datetime.now(UTC).isoformat()
            }).execute()
            st.session_state.milestone_message = milestones[user_count]

# ==================================================
# DOCTRINE
# ==================================================
def get_doctrine():
    try:
        r = supabase.table("dojo_doctrine").select("*").execute()
        if r.data:
            choice = random.choice(r.data)
            return choice.get("text") or choice.get("doctrine")
    except:
        pass
    return "Discipline begins with attention."

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:
    st.markdown("### The-Dojo")
    st.markdown(f"**{rank} · {USER_NAME}**")
    st.divider()
    momentum = compute_momentum()
    evolution = compute_evolution()
    st.markdown(f"Momentum: **{momentum:+.2f}**")
    st.markdown(f"Evolution: **{evolution}**")
    st.progress((momentum+1)/2)
    st.divider()
    r = supabase.table("dojo_patterns") \
        .select("pattern,timestamp") \
        .eq("user_id",USER_ID) \
        .order("timestamp",desc=True) \
        .limit(50) \
        .execute()
    if r.data:
        df = pd.DataFrame(r.data)
        xs = []
        ys = []
        for p in df["pattern"]:
            coord = PATTERN_COORDS.get(p,(0,0))
            xs.append(coord[0])
            ys.append(coord[1])
        fig,ax = plt.subplots()
        ax.scatter(xs,ys)
        ax.axhline(0)
        ax.axvline(0)
        ax.set_xlim(-1,1)
        ax.set_ylim(-1,1)
        ax.set_title("Mental State Map")
        st.pyplot(fig)
        st.bar_chart(df["pattern"].value_counts())
    st.divider()
    for i,phase in enumerate(PHASE_SETS[rank]):
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
tab_train,tab_history = st.tabs(["Training","History"])

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
        st.session_state.msgs.append({"role":"user","content":prompt})
        check_milestones()
        supabase.table("records").insert({
        "user_id":USER_ID,
        "role":"user",
        "content":prompt,
        "timestamp":datetime.now(UTC).isoformat()
        }).execute()
        user_count=len([m for m in st.session_state.msgs if m["role"]=="user"])
        if user_count%7==0:
            detect_patterns(USER_ID)
        
        # ===============================
        # PRIORITIZED PATTERN LOGIC
        # ===============================
        graph = compute_pattern_graph()
        loop = detect_pattern_loop(graph)
        loop_message = ""
        mirror = ""
        
        if loop:
            from_p, to_p, count = loop
            loop_message = f"I notice that {from_p.replace('_',' ')} often leads into {to_p.replace('_',' ')} for you (seen {count} times).\n\n"
        else:
            # Only check for single patterns if no loop is currently dominating
            recent_pattern = None
            try:
                rp = supabase.table("dojo_patterns") \
                    .select("pattern") \
                    .eq("user_id",USER_ID) \
                    .order("timestamp",desc=True) \
                    .limit(1) \
                    .execute()
                if rp.data:
                    recent_pattern = rp.data[0]["pattern"]
            except:
                pass
            
            if recent_pattern and random.random() < 0.3:
                mirror = f"I notice a pattern of {recent_pattern.replace('_',' ')} appearing in your reflections.\n\n"
        
        doctrine=get_doctrine()
        tone_instruction = ""
        momentum = compute_momentum()
        if momentum < -0.3:
            tone_instruction = "The practitioner appears to be struggling. Respond with patience and grounding.\n\n"
        elif momentum > 0.3:
            tone_instruction = "The practitioner shows strong forward movement. Reinforce discipline and clarity.\n\n"
        evolution = compute_evolution()
        if evolution == "Declining":
            tone_instruction += "Encourage stabilization and awareness.\n\n"
        elif evolution == "Rising":
            tone_instruction += "Encourage continued discipline and clarity.\n\n"
        mentor_prompt=f"""
Respond as a calm reflective mentor.

{tone_instruction}{loop_message}{mirror}If appropriate weave this teaching naturally:

{doctrine}
"""
        headers={"Authorization":f"Bearer {st.secrets['GROQ_API_KEY']}"}
        res=requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json={
        "model":"llama-3.3-70b-versatile",
        "messages":[{"role":"system","content":mentor_prompt}]
        + st.session_state.msgs[-10:]
        },
        headers=headers
        )
        reply=res.json()["choices"][0]["message"]["content"]
        with st.chat_message("assistant"):
            placeholder=st.empty()
            placeholder.markdown("Thinking...")
            time.sleep(2)
            text=""
            for s in reply.split(". "):
                text+=s+". "
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
