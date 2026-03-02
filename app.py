import os
import streamlit as st
import sqlite3, time, json
import numpy as np
from openai import OpenAI

# ==================================================
# STREAMLIT → ENV BRIDGE (CRITICAL FOR CLOUD)
# ==================================================
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

client = OpenAI()

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
MIRROR_PROMPT = (
    "ROLE: Dojo Mirror\n"
    "Identify shield. Compare with past truths. "
    "Name recurring pattern."
)

SENTINEL_PROMPT = "ROLE: Sentinel. Validate action."

DB_PATH = "dojo_records.db"

# ==================================================
# LLM
# ==================================================
def llm(messages, temp=0.4):
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=temp
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"Model error: {str(e)[:80]}"

# ==================================================
# DB
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
            phase TEXT
        )
    """)
    c.commit()
    return c

def save(text, rank, phase):
    db().execute(
        "INSERT INTO records VALUES (NULL,?,?,?,?)",
        (time.time(), text, rank, phase)
    )
    db().commit()

# ==================================================
# RANK
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
# STATE
# ==================================================
st.set_page_config(page_title="The Dojo", layout="wide")

if "phase" not in st.session_state:
    st.session_state.phase = 0
if "msgs" not in st.session_state:
    st.session_state.msgs = []

def reset():
    st.session_state.msgs = []

# ==================================================
# HEADER
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
# SIDEBAR PATH (NON-SELECTABLE)
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
# CHAT
# ==================================================
phase = st.session_state.phase
phase_name = phase_names[phase]

st.subheader(phase_name)

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ==================================================
# PHASE ENGINE
# ==================================================

# Phase 0 — Arrival
if phase == 0:
    if p := st.chat_input("How are you arriving?"):
        st.session_state.msgs.append({"role": "user", "content": p})

        ans = llm([
            {"role": "system", "content": MASTER_PROMPT + "\n" + tone},
            {"role": "user", "content": p}
        ])

        st.session_state.msgs.append({"role": "assistant", "content": ans})
        st.session_state.phase = 1
        st.rerun()

# Phase 1 — Mirror
elif phase == 1:
    if p := st.chat_input("What’s showing up?"):
        st.session_state.msgs.append({"role": "user", "content": p})

        ans = llm([
            {"role": "system", "content": MIRROR_PROMPT + "\n" + tone},
            {"role": "user", "content": p}
        ])

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
        if len(last) > 10:
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

        ans = llm([
            {"role": "system", "content": SENTINEL_PROMPT + "\n" + tone},
            {"role": "user", "content": p}
        ])

        st.session_state.msgs.append({"role": "assistant", "content": ans})
        st.rerun()

    if st.session_state.msgs:
        last_ai = next(
            (m["content"] for m in reversed(st.session_state.msgs)
             if m["role"] == "assistant"),
            None
        )
        if last_ai:
            with st.container(border=True):
                st.markdown("**Sentinel:**")
                st.markdown(last_ai)

    if st.session_state.msgs and st.button("Complete"):
        st.session_state.phase = 0
        reset()
        st.rerun()
