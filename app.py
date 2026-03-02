import streamlit as st
import sqlite3, time, json, os
import numpy as np, pandas as pd, altair as alt
from litellm import completion, embedding

# ==================================================
# AGENTS (Groq-only)
# ==================================================
AGENTS = {
    "logic": "groq/llama-3.3-70b-versatile",
    "fast": "groq/llama-3.1-8b-instant"
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

MASTER_PROMPT = "ROLE: Communicator. Gentle Warrior."
MIRROR_PROMPT = """
ROLE: Dojo Mirror
TASK:
1. Name the felt state or shield in simple, grounded words.
2. Gently point to any echo from past entries if close.
3. Offer one quiet insight — no advice, no fixing.
STYLE: Warm, minimal, human. Max 3 lines.
"""
SENTINEL_PROMPT = "ROLE: Sentinel. Validate the next step briefly and clearly."
CRISIS_PROMPT = "ROLE: Sensei. Ground the user. Short, calming lines only."
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
        r = completion(
            model=AGENTS["logic"],
            messages=[{"role":"system","content":"YES/NO crisis?"},{"role":"user","content":text[:500]}],
            max_tokens=5,
            temperature=0
        )
        return "YES" in r.choices[0].message.content.upper()
    except:
        return True

def detect_sentiment(text):
    try:
        r = completion(
            model=AGENTS["fast"],
            messages=[{"role":"system","content":"POSITIVE/NEUTRAL/NEGATIVE/STUCK sentiment?"},{"role":"user","content":text[:500]}],
            max_tokens=5,
            temperature=0
        )
        sentiment = r.choices[0].message.content.upper()
        if "POSITIVE" in sentiment:
            return "positive"
        elif "NEGATIVE" in sentiment or "STUCK" in sentiment:
            return "negative"
        else:
            return "neutral"
    except:
        return "neutral"

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
    for c,v in rows:
        try:
            v = np.array(json.loads(v))
            s = np.dot(q,v)/(np.linalg.norm(q)*np.linalg.norm(v))
            sims.append((s,c))
        except: pass
    sims.sort(reverse=True)
    return [x[1] for x in sims[:k]]

def semantic_density(text):
    words = len(text.split())
    unique = len(set(text.lower().split()))
    return unique/words if words else 0

def cluster_records(th=0.85):
    rows = db().execute("SELECT timestamp,content,vector FROM records WHERE vector IS NOT NULL").fetchall()
    clusters = []
    for ts,c,v in rows:
        try: v = np.array(json.loads(v))
        except: continue
        placed = False
        for cl in clusters:
            s = np.dot(v,cl["c"])/(np.linalg.norm(v)*np.linalg.norm(cl["c"]))
            if s > th:
                cl["i"].append((ts,c,v))
                cl["c"] = np.mean([x[2] for x in cl["i"]], axis=0)
                placed = True; break
        if not placed:
            clusters.append({"c":v, "i":[(ts,c,v)]})
    return clusters

# ==================================================
# STATE
# ==================================================
st.set_page_config(page_title="The Dojo", layout="wide")
if "phase" not in st.session_state: st.session_state.phase = 0
if "msgs" not in st.session_state: st.session_state.msgs = []
if "_match_count" not in st.session_state: st.session_state["_match_count"] = None
if "_embed_fail" not in st.session_state: st.session_state["_embed_fail"] = False
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

def compute_rank(count):
    if count < 10: return "Student"
    elif count < 25: return "Practitioner"
    elif count < 50: return "Sentinel"
    else: return "Sovereign"

rank = compute_rank(count)
tone = RANK_TONE[rank]

st.progress(min(count/50, 1.0))
st.markdown(f"**Rank:** {rank} • **Ledger:** {count} sealed • **{min(int(count/50*100),100)}% claimed**")
st.caption(RANK_CAPTION[rank])

# ==================================================
# SIDEBAR PATH (read-only, greyed future ranks)
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
# CHAT
# ==================================================
for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

phase_name = PHASE_SETS[rank][st.session_state.phase]
st.subheader(phase_name)

# ==================================================
# PHASE ENGINE (multi-exchange + sentiment-based progression)
# ==================================================
MIN_EXCHANGES = 3  # require at least 3 exchanges per phase

if p := st.chat_input("Speak..."):
    st.session_state.msgs.append({"role":"user","content":p})
    phase = st.session_state.phase
    sentiment = detect_sentiment(p)
    st.session_state.exchange_count[phase] += 1

    # Phase 0 - Arrival
    if phase == 0:
        role = CRISIS_PROMPT if detect_crisis(p) else MASTER_PROMPT + "\n" + tone
        ans = llm(AGENTS["logic"], [{"role":"system","content":role}] + st.session_state.msgs[-10:])
        st.session_state.msgs.append({"role":"assistant","content":ans})
        if sentiment == "positive" and st.session_state.exchange_count[phase] >= MIN_EXCHANGES:
            st.session_state.phase = 1
            reset()

    # Phase 1 - Mirror
    elif phase == 1:
        matches = semantic_matches(p)
        sys = MIRROR_PROMPT + "\n" + tone + "\n" + "\n".join(matches)
        core = llm(AGENTS["logic"], [{"role":"system","content":sys}] + st.session_state.msgs[-10:], temp=0.4)
        soft = llm(AGENTS["fast"], [{"role":"system","content":"Refine tone, keep insight."}, {"role":"user","content":core}])
        st.session_state.msgs.append({"role":"assistant","content":soft})
        if sentiment == "positive" and st.session_state.exchange_count[phase] >= MIN_EXCHANGES:
            st.session_state.phase = 2
            reset()

    # Phase 2 - Seal
    elif phase == 2:
        last = next((m["content"] for m in reversed(st.session_state.msgs) if m["role"]=="assistant"), "")
        if last:
            st.write("**Reflection:**", last)
        if st.button("Seal"):
            if len(last) > 10:
                save(last, rank, phase_name)
                d = semantic_density(last)
                st.caption(f"Semantic density: {d:.2f}")
                st.session_state.phase = 3
                reset()
                st.rerun()
            else:
                st.warning("Insight too thin.")
        if sentiment == "positive" and st.session_state.exchange_count[phase] >= MIN_EXCHANGES:
            st.session_state.phase = 3
            reset()

    # Phase 3 - Action
    elif phase == 3:
        core = llm(AGENTS["fast"], [{"role":"system","content":SENTINEL_PROMPT}] + st.session_state.msgs[-5:], temp=0.1)
        soft = llm(AGENTS["logic"], [{"role":"system","content":"Encourage gently."}, {"role":"user","content":core}])
        st.session_state.msgs.append({"role":"assistant","content":soft})
        if sentiment == "positive" and st.session_state.exchange_count[phase] >= MIN_EXCHANGES:
            st.session_state.msgs.append({"role":"assistant","content":"Is there anything else we can work on today?"})
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
            label = label.strip() if label and label.strip() else f"C{i+1}"
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
