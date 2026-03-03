import streamlit as st
import sqlite3
from datetime import datetime

# --- SYSTEM SETTINGS & ARCHITECTURE ---
# Version: 11.2.7 (Safety Override Patch)
# Philosophy: Gentle Warrior / Kenpo-Grounded
# ---------------------------------------

def init_db():
    conn = sqlite3.connect('dojo_ledger.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patterns 
                 (timestamp TEXT, pattern_type TEXT, description TEXT)''')
    conn.commit()
    return conn

def get_top_patterns(conn):
    """LIMITER: Only pull the Top 3 recurring patterns to avoid context inflation."""
    c = conn.cursor()
    c.execute("SELECT description FROM patterns ORDER BY timestamp DESC LIMIT 3")
    patterns = c.fetchall()
    return [p[0] for p in patterns]

def check_qualitative_advancement(user_input, history):
    """
    STABILIZATION LOGIC: Checks for user growth.
    ADDED: 5-Turn Safety Override to prevent holding loops.
    """
    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0
    
    st.session_state.turn_count += 1
    
    # Safety Override: If they have engaged for 5 turns, force the gate open.
    if st.session_state.turn_count >= 5:
        st.session_state.turn_count = 0 # Reset for next phase
        return True
        
    # Standard Qualitative Logic (simplified for block)
    # In full build, this calls the 8B model to assess stabilization.
    return "ready to move on" in user_input.lower() 

def sensei_protocol():
    """HARD-CODED SAFETY: Instantly identified distress resources."""
    st.error("### SENSEI PROTOCOL ACTIVATED")
    st.write("**If you are in immediate distress, please use these resources:**")
    st.write("- **Crisis Text Line:** Text 741741")
    st.write("- **Suicide & Crisis Lifeline:** Call or Text 988")
    st.divider()

def main():
    st.set_page_config(page_title="The Dojo", layout="centered")
    conn = init_db()
    
    # UI: Welcome Mat / Header
    st.title("The Dojo")
    st.caption("v11.2.7 | Strength in Reserve")

    # Side Bar: Sovereign Controls
    with st.sidebar:
        st.header("Sovereign Controls")
        if st.button("Bow-Out (Reset)"):
            # Per your request: No visual effects added, just a clean state reset.
            st.session_state.clear()
            st.rerun()
        
        st.divider()
        st.markdown("### Sensei Protocol")
        st.info("988 | 741741")

    # Persistent Memory Integration
    historical_patterns = get_top_patterns(conn)
    
    # Initialize Session State
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.phase = "Welcome Mat"

    # Display Chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Input Logic
    if prompt := st.chat_input("Enter the Dojo..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Logic: Determine Advancement
        if check_qualitative_advancement(prompt, st.session_state.messages):
            # Phase Logic (Example: Welcome Mat -> The Studio)
            if st.session_state.phase == "Welcome Mat":
                st.session_state.phase = "The Studio"
                response = "You have stabilized. We are moving from the Welcome Mat into The Studio. State your intent."
            else:
                response = "The patterns are clear. Let us go deeper."
        else:
            response = "Stay here a moment longer. Stabilize the thought before we advance."

        # Display Assistant Response
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
