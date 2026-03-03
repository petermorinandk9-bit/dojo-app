import streamlit as st
import sqlite3

# ==================================================
# SYSTEM SETTINGS - v11.3.1 | Sovereign Alignment
# ==================================================

def init_db():
    """Initialize database with performance index for pattern recognition."""
    conn = sqlite3.connect('dojo_ledger.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patterns
                 (timestamp TEXT, pattern_type TEXT, description TEXT)''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON patterns(timestamp DESC)')
    conn.commit()
    conn.close()

def get_top_patterns():
    """Retrieves Top 3 patterns to guide AI context without inflation."""
    conn = sqlite3.connect('dojo_ledger.db')
    c = conn.cursor()
    c.execute("""
        SELECT description 
        FROM patterns 
        ORDER BY timestamp DESC 
        LIMIT 3
    """)
    patterns = c.fetchall()
    conn.close()
    return [p[0] for p in patterns]

def check_qualitative_advancement(user_input, history, current_phase):
    """
    Delayed Advance Logic: Forces stabilization before movement.
    Safety: 5-turn override ensures no 'stuck' loops.
    """
    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0
    if "last_phase" not in st.session_state:
        st.session_state.last_phase = current_phase

    if st.session_state.last_phase != current_phase:
        st.session_state.turn_count = 0
        st.session_state.last_phase = current_phase

    st.session_state.turn_count += 1

    if st.session_state.turn_count >= 5:
        st.session_state.turn_count = 0
        return True

    return "ready" in user_input.lower() or "move on" in user_input.lower()

def sensei_protocol():
    """The Unwavering Safety Net."""
    st.error("### SENSEI PROTOCOL ACTIVATED")
    st.write("**Strength in Reserve. If you need support, use these lines now:**")
    st.write("- **Lifeline:** Call or Text **988**")
    st.write("- **Crisis Text:** Text **HOME** to **741741**")
    st.divider()

# ==================================================
# MAIN DOJO INTERFACE
# ==================================================
def main():
    st.set_page_config(page_title="The Dojo", layout="centered")
    init_db()

    st.title("The Dojo")
    st.caption("v11.3.1 | Gentle Warrior | Strength in Reserve")

    with st.sidebar:
        st.header("Sovereign Controls")
        if st.button("Bow-Out (Reset)"):
            keys = list(st.session_state.keys())
            for key in keys:
                del st.session_state[key]
            st.rerun()

        st.divider()
        st.markdown("### Sensei Protocol")
        st.info("988 | Text HOME to 741741")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "phase" not in st.session_state:
        st.session_state.phase = "Welcome Mat"

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Speak from center..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Logic Gating: Claude-Refined Dialogue
        if check_qualitative_advancement(prompt, st.session_state.messages, st.session_state.phase):
            if st.session_state.phase == "Welcome Mat":
                st.session_state.phase = "The Studio"
                response = "Your focus has stabilized. We are moving from the Welcome Mat into **The Studio**. State your intent for this space."
            else:
                response = "The pattern is acknowledged. Let us move deeper into the work."
        else:
            response = "Hold your position. Let this thought settle and stabilize before we advance."

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
