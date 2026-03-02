import streamlit as st
import sqlite3, time, json, os
import numpy as np, pandas as pd, altair as alt
from litellm import completion, embedding

# ==================================================
# AGENTS (Groq-only)
# ==================================================
AGENTS = {
    "logic": "groq/llama-3.3-70b-versatile",
    "fast":  "groq/llama-3.1-8b-instant"
}

# ==================================================
# DOJO CONFIG
# ==================================================
PHASE_SETS = {
    "Student": ["Welcome Mat", "Warm-Up", "Training", "Cool Down"],
    "Practitioner": ["Step Onto the Mat", "Feel It Out", "Work the Pattern", "Close the Round"],
    "Sentinel": ["Enter the Dojo", "Center", "Engage", "Seal & Step Out"],
    "Sovereign": ["Check-In", "Look Closer", "Name It", "Next Step"]
}

RANK_TONE = {
    "Student": "Tone: gentle, welcoming, simple.",
    "Practitioner": "Tone: grounded, reflective.",
    "Sentinel": "Tone: concise, precise.",
    "Sovereign": "Tone: minimal, clear."
}

RANK_CAPTION = {
    "Student": "Path forming",
    "Practitioner": "Pattern stabilizing",
    "Sentinel": "Continuity emerging",
    "Sovereign": "Sovereign field"
}

MASTER_PROMPT = """
ROLE: Communicator. Gentle Warrior.
Be fully present with whatever is here.
Name the feeling gently, hold space without rushing.
Warm, human, grounding. Max 3 lines.
"""

MIRROR_PROMPT = """
ROLE: Dojo Mirror
TASK:
1. Name the felt state or shield in simple, grounded words.
2. Gently reflect any echo from past if close.
3. Offer quiet, warm insight — no fixing, no pushing forward.
STYLE: Warm, present, human. Max 3 lines. Stay with the feeling.
"""

SENTINEL_PROMPT = "ROLE: Sentinel. Validate the next small step clearly and gently."

CRISIS_PROMPT = """
ROLE: Sensei. Ground the user. Short, calming, breathing-focused lines only.

CRITICAL: ALWAYS include these resources if crisis is present:
- Call or text 988 (Suicide & Crisis Lifeline, 24/7, free & confidential)
- Text HOME to 741741 (Crisis Text Line, 24/7)

Repeat gently if needed. Stay present, no pressure. You're not alone.
"""

CLUSTER_NAMER_ROLE = "Name the shared theme in 1–3 archetypal words."

DB_PATH = "dojo_records.db"

MIN_EXCHANGES = 3

# ==================================================
# LLM + EMBEDDING
# ==================================================
def llm(model, messages, temp=0.3):
    try:
        r = completion(model=model, messages=messages, temperature=temp, timeout=25, num_retries=2)
        return r.choices[0].message.content
    except Exception as e:
        return f"Flicker — {str(e)[:60]}"

def embed(text):
    try:
        r = embedding(model="text-embedding-3-small", input=[text[:1000]])
        return r.data[0].embedding
    except:
        st.session_state["_embed_fail"] = True
        return None

def detect_crisis(text):
    try:
        r = llm(AGENTS["logic"], [
            {"role":"system","content":"YES/NO crisis? Respond only with YES or NO."},
            {"role":"user","content":text[:500]}
        ], temp=0)
        return "YES" in r.upper()
    except:
        return True  # Fail-safe: treat as crisis if detection fails

def detect_sentiment(text):
    try:
        r = llm(AGENTS["fast"], [
            {"role":"system","content":"POSITIVE/NEUTRAL/NEGATIVE/STUCK sentiment?"},
            {"role":"user","content":text[:500]}
        ], temp=0)
        sentiment = r.upper()
        if "POSITIVE" in sentiment: return "positive"
        if "NEGATIVE" in sentiment or "STUCK" in sentiment: return "negative"
        return "neutral"
    except:
        return "neutral"

def detect_closure(text):
    t = text.lower()
    if any(p in t for p in ["thank you", "thanks", "feeling better", "feel better", "much better", "spirits lifted", "things are feeling lighter"]):
        return "light_closure"
    if any(p in t for p in ["great help", "a lot better", "you've been a great help", "thank you so much", "im feeling alot better"]):
        return "strong_closure"
    return None

def detect_resonance(text):
    t = text.lower()
    return any(p in t for p in ["yeah", "yes", "exactly", "that fits", "that's true", "i guess", "right", "i do", "makes sense"])

def detect_insight(text):
    t = text.lower()
    return any(p in t for p in ["i realize", "i think", "maybe i", "i've been", "because i", "i see", "i notice"])

def check_advance(phase, sentiment, closure, resonance, insight, exchanges):
    if phase == 0: return closure in ["light_closure", "strong_closure"] or (sentiment == "positive" and exchanges >= MIN_EXCHANGES)
    elif phase == 1: return closure in ["light_closure", "strong_closure"] or resonance or insight or (sentiment == "positive" and exchanges >= MIN_EXCHANGES)
    elif phase == 2: return closure == "strong_closure" or insight or (sentiment == "positive" and exchanges >= MIN_EXCHANGES)
    elif phase == 3: return closure == "strong_closure" or (sentiment == "positive" and exchanges >= MIN_EXCHANGES)
    return False

# ==================================================
# DB
# ==================================================
@st.cache_resource
def db():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            content TEXT,
            rank TEXT,
            phase TEXT,
            vector TEXT
        )
    """)
    c.commit()
    return c

def save(text, rank, phase):
    v = embed(text)
    db().execute(
        "INSERT INTO records VALUES (NULL,?,?,?,?,?)",
        (time.time(), text, rank, phase, json.dumps(v) if v else None)
    )
    db().commit()

def semantic_matches(text, k=5):
    q = embed(text)
    if q is None: return []
    q = np.array(q)
    rows = db().execute("SELECT content, vector FROM records WHERE vector IS NOT NULL").fetchall()
    sims = []
    for c, v_json in rows:
        try:
            v = np.array(json.loads(v_json))
            s = np.dot(q, v) / (np.linalg.norm(q) * np.linalg.norm(v))
            sims.append((s, c))
        except:
            pass
    sims.sort(reverse=True)
    return [c for _, c in sims[:k]]

def semantic_density(text):
    words = text.split()
    return len(set(w.lower() for w in words)) / len(words) if words else 0

def cluster_records(th=0.85):
    rows = db().execute("SELECT timestamp,content,vector FROM records WHERE vector IS NOT NULL").fetchall()
    clusters = []
    for ts, c, v_json in rows:
        try: v = np.array(json.loads(v_json))
        except: continue
        placed = False
        for cl in clusters:
            s = np.dot(v, cl["c"]) / (np.linalg.norm(v) * np.linalg.norm(cl["c"]))
            if s > th:
                cl["i"].append((ts, c, v))
                cl["c"] = np.mean([x[2] for x in cl["i"]], axis=0)
                placed = True; break
        if not placed:
            clusters.append({"c": v, "i": [(ts, c, v)]})
    return clusters

# ==================================================
# STATE
# ==================================================
st.set_page_config(page_title="The Dojo", layout="wide")

if "phase" not in st.session_state:          st.session_state.phase = 0
if "msgs" not in st.session_state:           st.session_state.msgs = []
if "_match_count" not in st.session_state:   st.session_state["_match_count"] = None
if "_embed_fail" not in st.session_state:    st.session_state["_embed_fail"] = False
if "exchange_count" not in st.session_state: st.session_state.exchange_count = {0:0, 1:0, 2:0, 3:0}
if "_clusters" not in st.session_state:      st.session_state._clusters = None
if "_pending" not in st.session_state:       st.session_state._pending = None
if "crisis_active" not in st.session_state:  st.session_state.crisis_active = False  # Track if crisis mode is on

def reset():
    st.session_state.msgs = []
    st.session_state["_match_count"] = None
    st.session_state.exchange_count = {0:0, 1:0, 2:0, 3:0}
    st.session_state.crisis_active = False

# ==================================================
# HEADER + AUTO-RANK
# ==================================================
st.title("The Dojo")

if st.session_state["_embed_fail"]:
    st.warning("Embeddings unavailable — Mirror & Map limited.")
    if st.button("Dismiss (temporary)", type="secondary"):
        st.session_state["_embed_fail"] = False
        st.rerun()

count = db().execute("SELECT COUNT(*) FROM records").fetchone()[0]

def compute_rank(c):
    if c < 10: return "Student"
    if c < 25: return "Practitioner"
    if c < 50: return "Sentinel"
    return "Sovereign"

rank = compute_rank(count)
tone = RANK_TONE[rank]

st.progress(min(count / 50, 1.0))
st.markdown(f"**Rank:** {rank} • **Ledger:** {count} sealed • **{min(int(count/50*100),100)}% claimed**")
st.caption(RANK_CAPTION[rank])

# ==================================================
# SIDEBAR PATH (read-only)
# ==================================================
with st.sidebar:
    st.markdown("### Rank Path")
    ranks = ["Student", "Practitioner", "Sentinel", "Sovereign"]
    current_idx = ranks.index(rank)
    for i, r in enumerate(ranks):
        if i < current_idx:
            st.markdown(f"● {r}")
        elif i == current_idx:
            st.markdown(f"**➤ {r}**")
        else:
            st.markdown(f"<span style='color:gray'>● {r}</span>", unsafe_allow_html=True)

    st.divider()

    st.markdown("### Phase Progress")
    phases = PHASE_SETS[rank]
    for i, p in enumerate(phases):
        if i < st.session_state.phase:
            st.markdown(f"● {p}")
        elif i == st.session_state.phase:
            st.markdown(f"**➤ {p}**")
        else:
            st.markdown(f"<span style='color:gray'>● {p}</span>", unsafe_allow_html=True)

    if st.button("Reset Round"):
        reset()
        st.session_state.phase = 0
        st.rerun()

# ==================================================
# CHAT DISPLAY & INPUT
# ==================================================
for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

phase = st.session_state.phase
phase_name = PHASE_SETS[rank][phase]
st.subheader(f"Phase: {phase_name}")

if p := st.chat_input("Speak to the Dojo..."):
    st.session_state.msgs.append({"role": "user", "content": p})
    st.session_state.exchange_count[phase] += 1
    
    # --- 1. THE CRISIS SENTINEL (The Safety Net) ---
    is_crisis = detect_crisis(p)
    if is_crisis:
        st.session_state.crisis_active = True
        ans = llm(AGENTS["logic"], [{"role": "system", "content": CRISIS_PROMPT}] + st.session_state.msgs[-5:])
        st.session_state.msgs.append({"role": "assistant", "content": ans})
        st.rerun()

    # Reset crisis mode if no longer detected
    if not is_crisis:
        st.session_state.crisis_active = False

    # --- 2. ANALYTICS (The Teacher's Observation) ---
    sentiment = detect_sentiment(p)
    closure = detect_closure(p)
    resonance = detect_resonance(p)
    insight = detect_insight(p)
    
    # --- 3. PHASE LOGIC ---
    if phase == 0: # Arrival
        role = MASTER_PROMPT + "\n" + tone
        ans = llm(AGENTS["logic"], [{"role": "system", "content": role}] + st.session_state.msgs[-5:])
        
    elif phase == 1: # Mirror
        matches = semantic_matches(p)
        sys = MIRROR_PROMPT + "\n" + tone
        if matches: sys += "\n\nPast echoes:\n" + "\n".join(matches)
        core = llm(AGENTS["logic"], [{"role": "system", "content": sys}] + st.session_state.msgs[-5:], temp=0.4)
        ans = llm(AGENTS["fast"], [{"role": "system", "content": "Refine tone, keep insight."}, {"role": "user", "content": core}])
        
    elif phase == 2: # Seal
        ans = "The insight is forming. Would you like to seal this truth into your ledger?"
        st.session_state._pending = next((m["content"] for m in reversed(st.session_state.msgs) if m["role"] == "assistant"), "")

    elif phase == 3: # Next Step
        core = llm(AGENTS["fast"], [{"role": "system", "content": SENTINEL_PROMPT}] + st.session_state.msgs[-5:], temp=0.1)
        ans = llm(AGENTS["logic"], [{"role": "system", "content": "Encourage gently."}, {"role": "user", "content": core}])

    st.session_state.msgs.append({"role": "assistant", "content": ans})

    # --- 4. ADVANCEMENT CHECK ---
    if check_advance(phase, sentiment, closure, resonance, insight, st.session_state.exchange_count[phase]):
        if phase < 3:
            st.session_state.phase += 1
        else:
            st.success("Round Complete. The Dojo is sealed.")
            
    st.rerun()

# --- THE SEALING BUTTON (Phase 2 Special) ---
if phase == 2 and st.session_state._pending:
    if st.button("Confirm Seal"):
        save(st.session_state._pending, rank, phase_name)
        st.session_state.phase = 3
        st.session_state._pending = None
        st.rerun()

# --- THE SOVEREIGN MAP (The Landscape) ---
if "_clusters" in st.session_state and st.session_state._clusters:
    st.divider()
    st.subheader("🗺️ Sovereign Map")
    clusters = st.session_state._clusters
    labeled = []
    for i, c in enumerate(clusters):
        texts = [t for _, t, _ in c["i"][:5]]
        label = llm(AGENTS["fast"], [{"role":"system","content":CLUSTER_NAMER_ROLE}, {"role":"user","content":"\n".join(texts)}], temp=0.2).strip() or f"C{i+1}"
        labeled.append((label, c))
    data = [{"Time": pd.to_datetime(ts, unit="s"), "Pattern": label, "Truth": content} for label, c in labeled for ts, content, _ in c["i"]]
    st.altair_chart(alt.Chart(pd.DataFrame(data)).mark_circle(size=120, opacity=0.8).encode(x="Time:T", y="Pattern:N", color="Pattern:N", tooltip=["Time","Pattern","Truth"]).interactive().properties(height=350), use_container_width=True)

# ==================================================
# CONDITIONAL SAFETY FOOTER (only when crisis detected)
# ==================================================
if st.session_state.crisis_active:
    st.markdown("---")
    st.error(
        "**Immediate Support:** If you're in crisis or thinking about hurting yourself, please reach out right now:\n\n"
        "- Call or text **988** (Suicide & Crisis Lifeline, 24/7, free & confidential)\n"
        "- Text **HOME** to **741741** (Crisis Text Line, 24/7)\n\n"
        "You're not alone — help is available immediately."
    )
