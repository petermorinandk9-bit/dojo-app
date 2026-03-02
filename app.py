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
No advice, no fixing — just witness and reflect.
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
CRISIS_PROMPT = "ROLE: Sensei. Ground the user. Short, calming, breathing-focused lines only."
CLUSTER_NAMER_ROLE = "Name the shared theme in 1–3 archetypal words."

DB_PATH = "dojo_records.db"

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
            {"role":"system","content":"YES/NO crisis?"},
            {"role":"user","content":text[:500]}
        ], temp=0)
        return "YES" in r.upper()
    except:
        return True

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
    if any(phrase in t for phrase in ["thank you", "thanks", "feeling better", "feel better", "much better", "spirits lifted"]):
        return "light_closure"
    if any(phrase in t for phrase in ["great help", "a lot better", "you've been a great help", "thank you so much"]):
        return "strong_closure"
    return None

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

def reset():
    st.session_state.msgs = []
    st.session_state["_match_count"] = None
    st.session_state.exchange_count[st.session_state.phase] = 0

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
# CHAT (persistent across phases)
# ==================================================
for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

phase_name = PHASE_SETS[rank][st.session_state.phase]
st.subheader(phase_name)

# ==================================================
# PHASE ENGINE (3+ exchanges + closure detection)
# ==================================================
MIN_EXCHANGES = 3

if p := st.chat_input("Speak..."):
    st.session_state.msgs.append({"role":"user","content":p})
    phase = st.session_state.phase
    sentiment = detect_sentiment(p)
    closure = detect_closure(p)
    st.session_state.exchange_count[phase] += 1

    # Phase 0 - Arrival
    if phase == 0:
        role = CRISIS_PROMPT if detect_crisis(p) else MASTER_PROMPT + "\n" + tone
        ans = llm(AGENTS["logic"], [{"role":"system","content":role}] + st.session_state.msgs[-10:])
        st.session_state.msgs.append({"role":"assistant","content":ans})

        if closure == "light_closure" or (sentiment == "positive" and st.session_state.exchange_count[phase] >= MIN_EXCHANGES):
            st.session_state.phase = 1
        st.rerun()

    # Phase 1 - Mirror
    elif phase == 1:
        matches = semantic_matches(p)
        sys = MIRROR_PROMPT + "\n" + tone + "\n" + "\n".join(matches)
        core = llm(AGENTS["logic"], [{"role":"system","content":sys}] + st.session_state.msgs[-10:], temp=0.4)
        soft = llm(AGENTS["fast"], [{"role":"system","content":"Refine tone, keep insight."}, {"role":"user","content":core}])
        st.session_state.msgs.append({"role":"assistant","content":soft})

        if closure == "light_closure" or (sentiment == "positive" and st.session_state.exchange_count[phase] >= MIN_EXCHANGES):
            st.session_state.phase = 2
        st.rerun()

    # Phase 2 - Seal
    elif phase == 2:
        last = next((m["content"] for m in reversed(st.session_state.msgs) if m["role"]=="assistant"), "")
        if last:
            st.write("**Reflection:**", last)
        if st.button("Seal") or closure == "strong_closure":
            if len(last) > 10:
                save(last, rank, phase_name)
                d = semantic_density(last)
                st.caption(f"Semantic density: {d:.2f}")
                st.session_state.msgs.append({"role":"assistant","content":"Good job working through this. I'm proud of you for showing up and staying with it."})
                st.session_state.phase = 3
                st.rerun()
            else:
                st.warning("Insight too thin.")
        if sentiment == "positive" and st.session_state.exchange_count[phase] >= MIN_EXCHANGES:
            st.session_state.phase = 3
            st.rerun()

    # Phase 3 - Action / Cool Down
    elif phase == 3:
        core = llm(AGENTS["fast"], [{"role":"system","content":SENTINEL_PROMPT}] + st.session_state.msgs[-5:], temp=0.1)
        soft = llm(AGENTS["logic"], [{"role":"system","content":"Encourage gently."}, {"role":"user","content":core}])
        st.session_state.msgs.append({"role":"assistant","content":soft})

        if closure == "strong_closure" or (sentiment == "positive" and st.session_state.exchange_count[phase] >= MIN_EXCHANGES):
            st.session_state.msgs.append({"role":"assistant","content":"You've done great work today. Is there anything else we can work on before we close the round?"})
            st.session_state.phase = 0
            reset()
        st.rerun()

# ==================================================
# MAP
# ==================================================
if "_clusters" in st.session_state:
    st.divider()
    st.subheader("Sovereign Map")
    clusters = st.session_state._clusters
    if not clusters:
        st.info("No clusters yet — seal more distinct insights.")
    else:
        labeled = []
        for i, c in enumerate(clusters):
            texts = [t for _, t, _ in c["i"][:5]]
            label = llm(AGENTS["fast"], [
                {"role":"system","content":CLUSTER_NAMER_ROLE},
                {"role":"user","content":"\n".join(texts)}
            ], temp=0.2)
            label = label.strip() or f"C{i+1}"
            labeled.append((label, c))
        data = [
            {"Time": pd.to_datetime(ts, unit="s"), "Pattern": label, "Truth": content}
            for label, c in labeled
            for ts, content, _ in c["i"]
        ]
        df = pd.DataFrame(data)
        st.altair_chart(
            alt.Chart(df).mark_circle(size=120, opacity=0.8).encode(
                x="Time:T", y="Pattern:N", color="Pattern:N", tooltip=["Time","Pattern","Truth"]
            ).interactive().properties(height=350),
            use_container_width=True
        )
else:
    st.caption("Generate Sovereign Map to visualize pattern landscape.")
