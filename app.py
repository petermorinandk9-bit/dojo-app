import streamlit as st
import sqlite3

# ==================================================
# SYSTEM SETTINGS - v11.3.4 | UI Streamlining
# ==================================================

def init_db():
    conn = sqlite3.connect('dojo_ledger.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patterns
                 (timestamp TEXT, pattern_type TEXT, description TEXT)''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON patterns(timestamp DESC)')
    conn.commit()
    conn.close()

def get_top_patterns():
    conn = sqlite3.connect('dojo_ledger.db')
    c = conn.cursor()
    c.execute("SELECT description FROM patterns ORDER BY timestamp DESC LIMIT 3")
    patterns = c.fetchall()
    conn.close()
    return [p[0] for p in patterns]

def check_qualitative_advancement(user_input, history, current_phase):
    """Delayed Advance Logic with 5-turn background safety."""
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

    ready_signals = ["ready", "deeper", "pattern", "understand", "move on", "stabilized"]
    return any(signal in user_input.lower() for signal in ready_signals)

# ==================================================
# MAIN INTERFACE
# ==================================================
def main():
    st.set_page_config(page_title="The Dojo", layout="centered")
    init_db()

    # --- SIDEBAR: SOVEREIGN UI ---
    with st.sidebar:
        st.title("Sovereign UI")
        st.divider()
        
        # Rank and Progression (No Counters)
        if "phase" in st.session_state:
            st.markdown(f"### **Current Rank**\n{st.session_state.phase}")
            # Progress bar based on phase index
            progress_map = {"Welcome Mat": 0.33, "The Studio": 0.66, "Seal": 1.0}
            st.progress(progress_map.get(st.session_state.phase, 0.0))
        
        st.divider()
        
        # System Controls
        st.subheader("System Actions")
        if st.button("Bow-Out (Reset)", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # --- MAIN CONTENT ---
    st.title("The Dojo")
    st.caption("v11.3.4 | Strength in Reserve")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "phase" not in st.session_state:
        st.session_state.phase = "Welcome Mat"

    # Display History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Input
    if prompt := st.chat_input("Speak from center..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Logic Gating
        if check_qualitative_advancement(prompt, st.session_state.messages, st.session_state.phase):
            if st.session_state.phase == "Welcome Mat":
                st.session_state.phase = "The Studio"
                response = "Ground is solid. You're stable. \n\nMoving to **The Studio** — where we work the mechanics. \n\nWhat's the pattern you're seeing?"
            elif st.session_state.phase == "The Studio":
                st.session_state.phase = "Seal"
                response = "You held center through that. Strong work. \n\nFinal phase now — let's **Seal** this insight. \n\nWhat's the one thing that's clear now?"
            else:
                response = "Sealed. This round is in the ledger. Respect. Mat's here when you need it again."
        else:
            response = "Hold your position. Let this settle and stabilize before we advance."

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
