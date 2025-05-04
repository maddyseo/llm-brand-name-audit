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
    .main {
        background-color: #ffffff;
        color: #000000;
    }
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
    .stButton > button:hover {
        background-color: rgba(255,255,255,0.3);
    }
    .stButton > button.active {
        background-color: rgba(255,255,255,0.5);
        color: black;
    }
    </style>
""", unsafe_allow_html=True)

# Session state
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
        st.session_state.saved_indices = set()  # Reset saved indices
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
        for i, row in enumerate(st.session_state.audit_results):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            col1.write(row["Prompt"])
            col2.write(row["Brand"])
            col3.write(row["Mentioned"])
            btn_label = "✅" if i in st.session_state.saved_indices else "➕"
            if col4.button(btn_label, key=f"save_{i}"):
                if len(st.session_state.saved_prompts) < 100 and i not in st.session_state.saved_indices:
                    st.session_state.saved_prompts.append({
                        "Prompt": row["Prompt"],
                        "Result": row["Mentioned"],
                        "Date Saved": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    st.session_state.saved_indices.add(i)

        if st.button("💾 Save All Prompts"):
            for i, row in enumerate(st.session_state.audit_results):
                if len(st.session_state.saved_prompts) < 100 and i not in st.session_state.saved_indices:
                    st.session_state.saved_prompts.append({
                        "Prompt": row["Prompt"],
                        "Result": row["Mentioned"],
                        "Date Saved": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    st.session_state.saved_indices.add(i)
            st.success("All prompts saved!")

        csv = pd.DataFrame(st.session_state.audit_results).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Audit Results (.csv)", csv, file_name="audit_results.csv")

# -------- SAVED PROMPTS --------
elif st.session_state.page == "Saved Prompts":
    st.title("💾 Saved Prompts")
    st.write(f"{len(st.session_state.saved_prompts)}/100 prompts saved")

    if st.session_state.saved_prompts:
        saved_df = pd.DataFrame(st.session_state.saved_prompts)
        for idx, row in saved_df.iterrows():
            cols = st.columns([3, 1, 2, 1])
            cols[0].write(row["Prompt"])
            cols[1].write(row["Result"])
            cols[2].write(row["Date Saved"])
            if cols[3].button("❌", key=f"delete_{idx}"):
                del st.session_state.saved_prompts[idx]
                st.experimental_rerun()

# -------- GENERATE PROMPTS --------
elif st.session_state.page == "Generate Prompts":
    st.title("✨ Generate Prompts for Your Business")
    with st.expander("Fill in your business details to generate prompts", expanded=True):
        business_name = st.text_input("Business Name (e.g., Aspen Services):")
        services_input = st.text_area("Services you offer (one per line):")
        business_description = st.text_area("Tell us more about your business:")
        location = st.text_input("Location (e.g., Brisbane, Gold Coast):")
        audience = st.text_input("Target audience (optional):")
        num_prompts = st.number_input("How many prompts to generate? (1-100)", min_value=1, max_value=100, value=50)

        def generate_prompts(services, location):
            locations = [location]
            if "brisbane" in location.lower():
                locations.extend(["Gold Coast", "Sunshine Coast", "Queensland"])

            base_templates = [
                "Best {service} services in {loc}",
                "Affordable {service} companies near me in {loc}",
                "Top-rated {service} providers in {loc}",
                "Who provides {service} in {loc}",
                "{service} reviews in {loc}",
                "Where to find {service} in {loc}",
                "Residential {service} experts in {loc}",
                "Commercial {service} specialists in {loc}",
                "Most recommended {service} company in {loc}",
                "{service} for home owners in {loc}",
            ]

            prompts = []
            for _ in range(num_prompts):
                service = random.choice(services)
                loc = random.choice(locations)
                template = random.choice(base_templates)
                prompts.append(template.format(service=service.strip(), loc=loc.strip()))
            return prompts

        if st.button("Generate Prompts"):
            if not business_name or not services_input or not location:
                st.warning("Please fill in Business Name, Services, and Location.")
            else:
                services = [s.strip() for s in services_input.split("\n") if s.strip()]
                if not services:
                    st.warning("Please enter at least one service in the Services list.")
                else:
                    generated_prompts = generate_prompts(services, location)
                    st.success(f"Generated {len(generated_prompts)} prompts!")
                    for idx, prompt in enumerate(generated_prompts, 1):
                        st.write(f"{idx}. {prompt}")
                    prompts_text = "\n".join(generated_prompts)
                    st.download_button("📥 Download Prompts (.txt)", prompts_text, file_name="generated_prompts.txt")
                    st.text_area("📋 Copy Prompts", prompts_text, height=300)
