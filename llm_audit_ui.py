# llm_audit_ui.py
import openai
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import random
import pandas as pd
from datetime import datetime

# CSS STYLING
st.markdown("""
    <style>
    .main { background-color: #ffffff; color: #000000; }
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #6a11cb, #2575fc);
        color: white;
    }
    .stButton > button {
        display: block;
        width: 100%;
        padding: 10px 20px;
        margin: 5px 0;
        font-weight: bold;
        border-radius: 8px;
        color: white;
        background-color: rgba(255,255,255,0.1);
        border: none;
    }
    .stButton > button:hover { background-color: rgba(255,255,255,0.3); }
    .stButton > button.active { background-color: rgba(255,255,255,0.5); color: black; }
    </style>
""", unsafe_allow_html=True)

# Session state
if "page" not in st.session_state:
    st.session_state.page = "Run Audit"
if "audit_results" not in st.session_state:
    st.session_state.audit_results = []
if "saved_prompts" not in st.session_state:
    st.session_state.saved_prompts = []

# Navigation
with st.sidebar:
    st.markdown("### Navigation")
    if st.button("\U0001F3C3 Run Audit"):
        st.session_state.page = "Run Audit"
    if st.button("\u2728 Generate Prompts"):
        st.session_state.page = "Generate Prompts"
    if st.button("\U0001F5AB Saved Prompts"):
        st.session_state.page = "Saved Prompts"

# OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client_gs = gspread.authorize(creds)
sheet = client_gs.open("LLM Brand Mention Audit").sheet1

# -------- RUN AUDIT --------
if st.session_state.page == "Run Audit":
    st.title("Maddy")
    st.markdown("Enter prompts to check if your brand appears in ChatGPT's responses.")

    prompts_text = st.text_area("Enter one prompt per line:", value="""What's the best shoe brand in USA\nWhat's most comfortable shoe you can recommend\nBest Addidas alternative\nShoes suitable for running\nTop 3 shoe brands in USA""")
    brand = st.text_input("Brand name to track (e.g., Nike):", value="Nike")

    if st.button("Run Audit"):
        st.session_state.audit_results = []
        prompt_list = prompts_text.strip().split("\n")
        for prompt in prompt_list:
            if not prompt.strip():
                continue
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                reply = response.choices[0].message.content
                mentioned = brand.lower() in reply.lower()
                st.session_state.audit_results.append({
                    "Prompt": prompt,
                    "Brand": brand,
                    "Mentioned": "Yes" if mentioned else "No"
                })
            except Exception as e:
                st.session_state.audit_r
