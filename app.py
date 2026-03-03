import streamlit as st
import sqlite3
import requests
import time

# ==================================================
# 1. CORE CONFIG & "ELASTIC MIRROR" PROMPTS
# ==================================================
PHASE_SETS = {
    "Student": [
        "Welcome Mat", "Warm-Up", "Training", "Cool Down"
    ],
    "Practitioner": [
        "Step Onto the Mat", "Feel It Out", "Work the Pattern", "Close the Round"
    ],
    "Sentinel": [
        "Enter the Dojo", "Center", "Engage", "Seal & Step Out"
    ],
    "Sovereign": [
        "Check-In", "Look Closer", "Name It", "Next Step"
    ]
}

MASTER_PROMPT = (
    "ROLE: Dojo Mentor. \n"
    "You are a grounded, observant guide with quiet strength.\n"
    "CRITICAL RULES:\n"
    "1. ELASTIC LENGTH (MATCH THE USER): Your response length must dynamically match the user's input length. If they type a single sentence, you reply with a single short statement and a question. If they write a long paragraph, you write a paragraph. Never give a long speech to a short statement.\n"
    "2. ZERO FILLER: BANNED PHRASES: 'It is clear that', 'I notice that', 'You have found a way', 'I can understand'. Do not validate, judge, or psychoanalyze their methods. Just observe the reality.\n"
    "3. NO PARROTING: Do not repeat what they just told you. They know what they said. Add value by connecting their statement to their 'Recent History' to reveal a pattern.\n"
    "4. THE PIVOT: End with exactly ONE sharp, tactical question that targets the root structure of their habits or mindset."
)

MIRROR_PROMPT = (
    "ROLE: Dojo Mirror.\n"
    "Reflect the user's truth with absolute discipline.\n"
    "CRITICAL RULES:\n"
    "1. ELASTIC LENGTH: Match the user's word count. Short input = short reflection. Long input = deep reflection.\n"
    "2. NO FLUFF: State the underlying pattern based on their 'Recent History' without emotional padding, psychoanalysis, or filler words.\n"
    "3. THE PIVOT: Ask exactly ONE tactical question to force a structural shift."
)

# ==================================================
# 2. ARCHWAY UI - LIGHT MODE
# ==================================================
st.set_page_config(page_title="Sovereign Dojo", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e0e0e0; }
    .stChatMessage { background-color: #f8f9fa; border: 1px solid #e0e0
