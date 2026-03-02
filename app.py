import streamlit as st
import sqlite3, time, json, os
import numpy as np
from litellm import completion, embedding

# ==================================================
# 0. BOOTSTRAP (Secrets → Env)
# ==================================================
for key in ["OPENAI_API_KEY", "GROQ_API_KEY"]:
    if key in st.secrets:
        os.environ[key] = st.secrets[key]

# ==================================================
# 1. AGENTS
# ==================================================
AGENTS = {
    "logic": "groq/llama-3.3-70b-versatile",
    "fast": "groq/llama-3.1-8b-instant"
}

# ==================================================
# 2. DOJO CONFIG
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
CRISIS_PROMPT = "ROLE: Sensei. Stabilize gently."
SENTINEL_PROMPT = "ROLE: Sentinel. Validate action."

# 🔧 REFINED MIRROR
MIRROR_PROMPT = """ROLE: Dojo Mirror

Return ONLY compressed pattern insight.

Rules:
- max 3 short lines
- no advice
- no encouragement
- no metaphor
- no explanation
- no questions

If user already names pattern → compress it.
Name shield + pattern if present.
"""

DB_PATH = "dojo_records.db"

# ==================================================
# 3. LLM + EMBEDDING
# ==================================================
def llm(model, messages, temp=0.3):
    try:
        r = completion(
            model=model,
            messages=messages,
            temperature=temp,
            timeout=25
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"Flicker — {str(e)[:50]}"

def embed(text):
    try:
        r = embedding(model="text-embedding-3-small", input=[text[:1000]])
        return r.data[0].embedding
    except:
        return None

def detect_crisis(text):
    try:
        r = completion(
            model=AGENTS["logic"],
            messages=[
                {"role": "system", "content": "YES/NO crisis?"},
                {"role": "user", "content": text[:400]},
            ],
            max_tokens=5,
            temperature=0,
        )
        return "YES" in r.choices[0].message.content.upper()
    except:
        return True

# ==================================================
# 4. DATABASE
# ==================================================
@st.cache_resource
def db():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("""
        CREATE TABLE IF NOT EXISTS records(
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
    if q is None:
        return []
    q = np.array(q)
    rows = db().execute(
        "SELECT content, vector FROM records WHERE vector IS NOT NULL"
    ).fetchall()

    sims = []
    for c, v in rows:
        try:
            v_arr = np.array(json.loads(v))
            s = np.dot(q, v_arr) / (np.linalg.norm(q) * np.linalg.norm(v_arr))
            sims.append((s, c))
        except:
            pass

    sims.sort(reverse=True)
    return [x[1] for x in sims[:k]]

# ==================================================
# 5. STATE
# ==================================================
st.set_page_config(page_title="The Dojo", layout="wide")

if "phase" not in st.session_state:
    st.session_state.phase = 0
if "msgs" not in st.session_state:
    st.session_state.msgs = []

def reset():
    st.session_state.msgs = []

# ==================================================
# 6. RANK COMPUTE
# ==================================================
def compute_rank(count):
    if count < 10:
        return "Student"
    elif count < 25:
        return "Practitioner"
    elif count < 50:
        return "Sentinel"
    else:
        return "Sovereign"

# ==================================================
# 7. HEADER
# ==================================================
st.title("The Dojo")

count = db().execute("SELECT COUNT(*) FROM records").fetchone()[0]
rank = compute_rank(count)
tone = RANK_TONE[rank]
phase_names = PHASE_SETS[rank]

st.progress(min(count / 50, 1.0))
st.markdown(f"**Rank:** {rank} • **Ledger:** {count} sealed")
st.caption(RANK_CAPTION[rank])

# ==================================================
# 8. SIDEBAR PATH DISPLAY
# ==================================================
with st.sidebar:
    st.markdown("### Rank Path")
    ranks = ["Student", "Practitioner", "Sentinel", "Sovereign"]
    for r in ranks:
        if r == rank:
            st.markdown(f"➡️ **{r}**")
        elif ranks.index(r) < ranks.index(rank):
            st.markdown(f"**{r}**")
        else:
            st.markdown(f":gray[{r}]")

    st.divider()

    st.markdown("### Phase Progress")
    for i, p in enumerate(phase_names):
        if i == st.session_state.phase:
            st.markdown(f"➡️ **{p}**")
        elif i < st.session_state.phase:
            st.markdown(f"**{p}**")
        else:
            st.markdown(f":gray[{p}]")

    st.divider()

    if st.button("Reset Round"):
        st.session_state.phase = 0
        reset()
        st.rerun()

# ==================================================
# 9. CHAMBER
# ==================================================
phase = st.session_state.phase
phase_name = phase_names[phase]

st.subheader(phase_name)

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ==================================================
# 10. PHASE FLOW
# ==================================================
# Phase 0 — Arrival
if phase == 0:
    if p := st.chat_input("How are you arriving?"):
        st.session_state.msgs.append({"role": "user", "content": p})

        role = MASTER_PROMPT + "\n" + tone
        if detect_crisis(p):
            role = CRISIS_PROMPT

        ans = llm(
            AGENTS["logic"],
            [{"role": "system", "content": role}] + st.session_state.msgs[-10:]
        )

        st.session_state.msgs.append({"role": "assistant", "content": ans})
        st.session_state.phase = 1
        st.rerun()

# Phase 1 — Mirror
elif phase == 1:
    if p := st.chat_input("What’s showing up?"):
        st.session_state.msgs.append({"role": "user", "content": p})

        matches = semantic_matches(p)
        sys = MIRROR_PROMPT + "\n" + "\n".join(matches)

        ans = llm(
            AGENTS["logic"],
            [{"role": "system", "content": sys},
             {"role": "user", "content": p}],
            temp=0.2
        )

        st.session_state.msgs.append({"role": "assistant", "content": ans})
        st.session_state.phase = 2
        st.rerun()

# Phase 2 — Seal
elif phase == 2:
    last = next(
        (m["content"] for m in reversed(st.session_state.msgs)
         if m["role"] == "assistant"),
        ""
    )

    if last:
        st.write("**Reflection:**", last)

    if st.button("Seal"):
        if len(last) > 5:
            save(last, rank, phase_name)
            st.session_state.phase = 3
            reset()
            st.rerun()
        else:
            st.warning("Insight too thin.")

# Phase 3 — Action
elif phase == 3:
    if p := st.chat_input("Next step"):
        st.session_state.msgs.append({"role": "user", "content": p})

        ans = llm(
            AGENTS["fast"],
            [{"role": "system", "content": SENTINEL_PROMPT},
             {"role": "user", "content": p}],
            temp=0.1
        )

        st.session_state.msgs.append({"role": "assistant", "content": ans})
        st.rerun()

    if st.session_state.msgs and st.button("Complete"):
        st.session_state.phase = 0
        reset()
        st.rerun()
