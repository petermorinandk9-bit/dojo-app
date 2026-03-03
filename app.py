import streamlit as st
import sqlite3

# ==================================================
# SYSTEM SETTINGS - v11.3.2 | Kenpo-Grounded Soul
# ==================================================

# Core Philosophy: Zanshin (Mind that remains)
# Relaxed alertness. Strength in reserve.

def init_db():
    """Initialize database with performance index."""
    conn = sqlite3.connect('dojo_ledger.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patterns
                 (timestamp TEXT, pattern_type TEXT, description TEXT)''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON patterns(timestamp DESC)')
    conn.commit()
    conn.close()

def get_top_patterns():
    """Optimized query - LIMIT 3 with index."""
    conn = sqlite3.connect('dojo_ledger.db')
    c = conn.cursor()
    c.execute("SELECT description FROM patterns ORDER BY timestamp DESC LIMIT 3")
    patterns = c.fetchall()
    conn.close()
    return [p[0] for p in patterns]

def check_qualitative_advancement(user_input, history, current_phase):
    """
    Phase-gated advancement logic.
    5-turn safety override resets on phase transition.
    """
    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0
    if "last_phase" not in st.session_state:
        st.session_state.last_phase = current_phase

    if st.session_state.last_phase != current_phase:
        st.session_state.turn_count = 0
        st.session_state.last_phase = current_phase

    st.session_state.turn_count += 1

    # Safety Override: Force advance to prevent stalls
    if st.session_state.turn_count >= 5:
        st.session_state.turn_count = 0
        return True

    # Claude's Qualitative Signals
    ready_signals = ["ready", "deeper", "pattern", "understand", "move on", "stabilized"]
    return any(signal in user_input.lower() for signal in ready_signals)

def sensei_protocol():
    """Claude's Crisis Trigger: Firm, Unwavering, Direct."""
    st.error("### ⚠️ SENSEI PROTOCOL — ACTIVE")
    st.write("I'm pulling you off the mat. This is beyond sparring.")
    st.write("You need immediate support from someone trained for this level. Not later — now.")
    st.divider()
    st.write("**988** — Call or text 24/7 (Suicide & Crisis Lifeline)")
    st.write("**HOME to 741741** — Crisis Text Line")
    st.info("The mat will be here when you're ready. But first, you need support above my weight class. Go.")

# ==================================================
# MAIN APPLICATION
# ==================================================
def main():
    st.set_page_config(page_title="The Dojo", layout="centered")
    init_db()

    st.title("The Dojo")
    st.caption("v11.3.2 | Zanshin (Mind That Remains)")

    # Sidebar: Sovereign Controls
    with st.sidebar:
        st.header("Sovereign Controls")
        if st.button("Bow-Out (Reset)"):
            keys = list(st.session_state.keys())
            for key in keys:
                del st.session_state[key]
            st.rerun()

        st.divider()
        st.markdown("### Emergency Line")
        st.info("988 | 741741")

    # Load historical patterns
    historical_patterns = get_top_patterns()

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "phase" not in st.session_state:
        st.session_state.phase = "Welcome Mat"

    # Display History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Input with Claude's 'Center' Cue
    if prompt := st.chat_input("Speak from center..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Logic Gate: Transition Dialogue via Claude
        if check_qualitative_advancement(prompt, st.session_state.messages, st.session_state.phase):
            if st.session_state.phase == "Welcome Mat":
                st.session_state.phase = "The Studio"
                response = """Ground is solid. You're stable.
                
Moving to **The Studio** — where we work the mechanics. 

What's the pattern you're seeing?"""
            elif st.session_state.phase == "The Studio":
                st.session_state.phase = "Seal"
                response = """You held center through that. Strong work.
                
Final phase now — let's **Seal** this insight.

What's the one thing that's clear now?"""
            else:
                response = "Sealed. This round is in the ledger. Respect. Mat's here when you need it again."
        else:
            # Holding pattern responses
            response = "Hold your position. Let this settle and stabilize before we advance."

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
