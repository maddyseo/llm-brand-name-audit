
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
    .main {
        background-color: #ffffff;
        color: #000000;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #6a11cb, #2575fc);
        color: white;
    }
    [data-testid="stSidebar"] .stButton > button {
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
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255,255,255,0.3);
    }
    .stButton > button {
        display: block;
        width: 100%;
        padding: 10px 20px;
        margin: 5px 0;
        font-weight: bold;
        border-radius: 8px;
        color: white;
        background-color: #ff7f50;
        border: none;
        transition: background-color 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #6a11cb;
    }
    .zebra tr:nth-child(even) {
        background-color: rgba(255,255,255,0.03);
    }
    </style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "Run Audit"
if "audit_results" not in st.session_state:
    st.session_state.audit_results = []
if "saved_prompts" not in st.session_state:
    st.session_state.saved_prompts = []
if "saved_indices" not in st.session_state:
    st.session_state.saved_indices = set()

# Navigation
with st.sidebar:
    st.markdown("### Navigation")
    if st.button("🏃‍♂️ Run Audit"):
        st.session_state.page = "Run Audit"
    if st.button("✨ Generate Prompts"):
        st.session_state.page = "Generate Prompts"
    if st.button("💾 Saved Prompts"):
        st.session_state.page = "Saved Prompts"

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client_gs = gspread.authorize(creds)
sheet = client_gs.open("LLM Brand Mention Audit").sheet1

# -------- RUN AUDIT --------
if st.session_state.page == "Run Audit":
    st.title("Maddy")
    st.markdown("Enter prompts to check if your brand appears in ChatGPT's responses.")

    prompts_text = st.text_area("Enter one prompt per line:", value="What's the best shoe brand in USA\nWhat's most comfortable shoe you can recommend\nBest Addidas alternative\nShoes suitable for running\nTop 3 shoe brands in USA")
    brand = st.text_input("Brand name to track (e.g., Nike):", value="Nike")

    if st.button("Run Audit"):
        st.session_state.audit_results = []
        st.session_state.saved_indices = set()
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
                st.session_state.audit_results.append({
                    "Prompt": prompt,
                    "Brand": brand,
                    "Mentioned": f"Error: {str(e)}"
                })

    if st.session_state.audit_results:
        st.subheader("Audit Results")
        st.markdown("### Prompt | Brand | Mentioned | Save")
        df = pd.DataFrame(st.session_state.audit_results)
        for i, row in df.iterrows():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            col1.markdown(f"**{row['Prompt']}**")
            col2.write(row["Brand"])
            col3.write(row["Mentioned"])
            if i in st.session_state.saved_indices:
                col4.button("✅", key=f"saved_{i}", disabled=True, help="Already saved")
            else:
                if col4.button("➕", key=f"save_{i}", help="Save this prompt"):
                    if len(st.session_state.saved_prompts) < 100:
                        st.session_state.saved_prompts.append({
                            "Prompt": row["Prompt"],
                            "Result": row["Mentioned"],
                            "Date Saved": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        st.session_state.saved_indices.add(i)
                        st.experimental_rerun()
