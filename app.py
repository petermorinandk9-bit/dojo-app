import streamlit as st
import sqlite3
from datetime import datetime

# ==================================================
# SYSTEM SETTINGS - v11.4.0 | The Ritual & The Ledger
# ==================================================

# Core Philosophy: Zanshin (Mind That Remains)
# Archetype: Sovereign Architect / Gentle Warrior

def init_db():
    """Initialize the Persistent Memory Ledger and Seal Rewards."""
    conn = sqlite3.connect('dojo_ledger.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patterns
                 (timestamp TEXT, pattern_type TEXT, description TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS seals
                 (timestamp TEXT, seal_type TEXT, achievement TEXT)''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON patterns(timestamp DESC)')
    conn.commit()
    conn.close()

def get_top_patterns():
    """Evolving Mirror: Pulls Top 3 patterns for contextual awareness."""
    conn = sqlite3.connect('dojo_ledger.db')
    c = conn.cursor()
    c.execute("SELECT description FROM patterns ORDER BY timestamp DESC LIMIT 3")
    patterns = [p[0] for p in c.fetchall()]
    conn.close()
    return patterns

def trigger_seal_reward(achievement):
    """Rewards: Awards a 'Seal' for breakthroughs or session completion."""
    conn = sqlite3.connect('dojo_ledger.db')
    c = conn.cursor()
    c.execute("INSERT INTO seals (timestamp, seal_type, achievement) VALUES (?, ?, ?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Breakthrough", achievement))
    conn.commit()
    conn.close()
    st.toast(f"💠 Seal Awarded: {achievement}", icon="🛡️")

def check_qualitative_advancement(user_input, history, current_phase):
    """Delayed Advance Logic: 5-turn background safety override."""
    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0
    if "last_phase" not in st.session_state:
        st.session_state.last_phase = current_phase

    if st.session_state.last_phase != current_phase:
        st.session_state.turn_count = 0
        st.session_state.last_phase = current_phase

    st.session_state.turn_count += 1

    # Force advance after 5 turns to prevent logic stalls
    if st.session_state.turn_count >= 5:
        st.session_state.turn_count = 0
        return True

    ready_signals = ["ready", "deeper", "pattern", "understand", "move on", "stabilized", "integration"]
    return any(signal in user_input.lower() for signal in ready_signals)

# ==================================================
# MAIN INTERFACE
# ==================================================
def main():
    st.set_page_config(page_title="The Dojo", layout="centered")
    init_db()

    # --- SESSION STATE INITIALIZATION ---
    if "phase" not in st.session_state:
        st.session_state.phase = "Welcome Mat"
    if "rank" not in st.session_state:
        st.session_state.rank = "Student"
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- SIDEBAR: THE RITUAL & THE RANKS ---
    with st.sidebar:
        # 1. RANKS
        st.markdown("### **Ranks**")
        ranks = ["Student", "Disciple", "Sovereign", "Architect"]
        for r in ranks:
            if r == st.session_state.rank:
                st.markdown(f"#### **{r}**") # Bold Black
            else:
                st.markdown(f"<span style='color: grey; font-size: 1.1em;'>{r}</span>", unsafe_allow_html=True)
        
        st.divider()

        # 2. PHASES (The Ritual)
        st.markdown("### **Phases**")
        phases = ["Welcome Mat", "The Studio", "Integration", "Cool Down"]
        for p in phases:
            if p == st.session_state.phase:
                st.markdown(f"#### **{p}**") # Bold Black
            else:
                st.markdown(f"<span style='color: grey; font-size: 1.1em;'>{p}</span>", unsafe_allow_html=True)
        
        st.divider()
        
        # 3. ACTION
        if st.button("Bow-Out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # --- MAIN CONTENT ---
    st.title("The Dojo")
    st.caption("v11.4.0 | Zanshin (Mind That Remains)")

    # Sensei Protocol integrated within the messaging flow
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Input
    if prompt := st.chat_input("Speak from center..."):
        # CRISIS DETECTION (Hard-coded Sensei Protocol)
        crisis_keywords = ["kill myself", "suicide", "hurt myself", "end it all"]
        if any(k in prompt.lower() for k in crisis_keywords):
            st.error("### ⚠️ SENSEI PROTOCOL — ACTIVE")
            st.write("I'm pulling you off the mat. This is beyond sparring.")
            st.write("You need immediate support. Call/text **988** or text **741741**. Go.")
            return

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # LOGIC GATING: Transition Protocol
        if check_qualitative_advancement(prompt, st.session_state.messages, st.session_state.phase):
            if st.session_state.phase == "Welcome Mat":
                st.session_state.phase = "The Studio"
                response = "Ground is solid. You're stable. \n\nMoving to **The Studio** — where we work the mechanics. What's the pattern you're seeing?"
            elif st.session_state.phase == "The Studio":
                st.session_state.phase = "Integration"
                trigger_seal_reward("Breakthrough Recognition")
                response = "You held center through that. Strong work. \n\nFinal phase now — let's **Integrate** this insight. What's clear now?"
            elif st.session_state.phase == "Integration":
                st.session_state.phase = "Cool Down"
                response = "Integration acknowledged. The pattern is in the ledger. \n\nMoving to **Cool Down**. Breathe. What stays with you?"
            else:
                trigger_seal_reward("Session Completion")
                response = "The session is complete. The mat is yours whenever you're ready to train."
                # Example: Advance to Disciple after first completion
                if st.session_state.rank == "Student":
                    st.session_state.rank = "Disciple"
        else:
            response = "Hold your position. Let this thought stabilize before we advance."

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
