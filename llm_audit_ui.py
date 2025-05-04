import openai
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import random
import datetime
import pandas as pd

# ----- CUSTOM CSS -----
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
    .stButton > button:hover {
        background-color: rgba(255,255,255,0.3);
    }
    .stButton > button.active {
        background-color: rgba(255,255,255,0.5);
        color: black;
    }
    </style>
""", unsafe_allow_html=True)

# ----- SESSION STATE -----
if "page" not in st.session_state:
    st.session_state.page = "Run Audit"
if "saved_prompts" not in st.session_state:
    st.session_state.saved_prompts = []
if "saved_indices" not in st.session_state:
    st.session_state.saved_indices = set()

# ----- SIDEBAR -----
with st.sidebar:
    st.markdown("### Navigation")
    audit_clicked = st.button("🏃‍♂️ Run Audit", key="nav_audit")
    prompts_clicked = st.button("✨ Generate Prompts", key="nav_prompts")
    saved_clicked = st.button("💾 Saved Prompts", key="nav_saved")

    if audit_clicked: st.session_state.page = "Run Audit"
    if prompts_clicked: st.session_state.page = "Generate Prompts"
    if saved_clicked: st.session_state.page = "Saved Prompts"

    # Active style
    st.markdown(f"""
        <style>
        [key="nav_audit"] > button {'{ background-color: rgba(255,255,255,0.5); color: black; }' if st.session_state.page == 'Run Audit' else ''}
        [key="nav_prompts"] > button {'{ background-color: rgba(255,255,255,0.5); color: black; }' if st.session_state.page == 'Generate Prompts' else ''}
        [key="nav_saved"] > button {'{ background-color: rgba(255,255,255,0.5); color: black; }' if st.session_state.page == 'Saved Prompts' else ''}
        </style>
    """, unsafe_allow_html=True)

# ----- GOOGLE SHEETS SETUP -----
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client_gs = gspread.authorize(creds)
sheet = client_gs.open("LLM Brand Mention Audit").sheet1

# ----- PAGE: RUN AUDIT -----
if st.session_state.page == "Run Audit":
    st.title("Maddy")
    st.markdown("Enter prompts to check if your brand appears in ChatGPT's responses.")

    default_prompts = [
        "What's the best shoe brand in USA",
        "What's most comfortable shoe you can recommend",
        "Best Addidas alternative",
        "Shoes suitable for running",
        "Top 3 shoe brands in USA"
    ]

    prompts_input = st.text_area("Enter one prompt per line:", value="\n".join(default_prompts))
    brand = st.text_input("Brand name to track (e.g., Nike):", value="Nike")

    if "audit_results" not in st.session_state:
        st.session_state.audit_results = []

    if st.button("Run Audit"):
        st.session_state.audit_results = []
        prompt_list = [p.strip() for p in prompts_input.split("\n") if p.strip()]
        for prompt in prompt_list:
            try:
                # Simulated API call here
                # response = openai.Completion.create(...)
                reply = f"Simulated response mentioning {brand}"  # Replace with real API
                mentioned = brand.lower() in reply.lower()
                st.session_state.audit_results.append({
                    "prompt": prompt,
                    "brand": brand,
                    "mentioned": "Yes" if mentioned else "No"
                })
            except Exception as e:
                st.session_state.audit_results.append({
                    "prompt": prompt,
                    "brand": brand,
                    "mentioned": f"Error: {str(e)}"
                })

    if st.session_state.audit_results:
        st.subheader("Audit Results")
        # Build DataFrame with Save buttons
        cols = ["Prompt", "Brand", "Mentioned", "Action"]
        result_rows = []
        for idx, result in enumerate(st.session_state.audit_results):
            save_label = "✅ Saved" if idx in st.session_state.saved_indices else "+"
            save_color = "green" if idx in st.session_state.saved_indices else "gray"
            save_btn = st.button(save_label, key=f"save_{idx}")
            if save_btn and idx not in st.session_state.saved_indices:
                st.session_state.saved_prompts.append({
                    "prompt": result["prompt"],
                    "result": result["mentioned"],
                    "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                st.session_state.saved_indices.add(idx)

            result_rows.append([
                result["prompt"],
                result["brand"],
                result["mentioned"],
                save_label
            ])

        # Display table
        df = pd.DataFrame(result_rows, columns=cols)
        st.dataframe(df.drop(columns=["Action"]))

        # Save All button
        if st.button("💾 Save All Prompts"):
            for idx, result in enumerate(st.session_state.audit_results):
                if idx not in st.session_state.saved_indices:
                    st.session_state.saved_prompts.append({
                        "prompt": result["prompt"],
                        "result": result["mentioned"],
                        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    st.session_state.saved_indices.add(idx)
            st.success("All unsaved prompts saved ✅")

        # Download CSV
        csv_data = pd.DataFrame(st.session_state.audit_results)[["prompt", "brand", "mentioned"]]
        csv = csv_data.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Audit Results (.csv)", csv, "audit_results.csv", "text/csv")

# ----- PAGE: SAVED PROMPTS -----
elif st.session_state.page == "Saved Prompts":
    st.title("💾 Saved Prompts")
    st.markdown(f"{len(st.session_state.saved_prompts)}/100 prompts saved")

    if st.session_state.saved_prompts:
        df_saved = pd.DataFrame(st.session_state.saved_prompts)
        for idx, row in df_saved.iterrows():
            col1, col2, col3, col4 = st.columns([5, 1, 1, 1])
            col1.write(row["prompt"])
            col2.write(row["result"])
            col3.write(row["date"])
            if col4.button("❌", key=f"del_{idx}"):
                st.session_state.saved_prompts.pop(idx)
                st.experimental_rerun()

# ----- PAGE: GENERATE PROMPTS -----
elif st.session_state.page == "Generate Prompts":
    st.title("✨ Generate Prompts for Your Business")
    business_name = st.text_input("Business Name (e.g., Aspen Services):")
    services_input = st.text_area("Services you offer (one per line):")
    business_description = st.text_area("Tell us more about your business:")
    location = st.text_input("Location (e.g., Brisbane, Gold Coast):")
    audience = st.text_input("Target audience (optional):")
    prompt_count = st.number_input("Number of prompts (1-100)", min_value=1, max_value=100, value=10)

    if st.button("Generate Prompts"):
        if not business_name or not services_input or not location:
            st.warning("Please fill in Business Name, Services, and Location.")
        else:
            services = [s.strip() for s in services_input.split("\n") if s.strip()]
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
            for _ in range(int(prompt_count)):
                template = random.choice(base_templates)
                service = random.choice(services)
                prompts.append(template.format(service=service, loc=location))
            st.success(f"Generated {len(prompts)} prompts!")
            for i, p in enumerate(prompts, 1):
                st.write(f"{i}. {p}")

            st.download_button("📥 Download Prompts (.txt)", "\n".join(prompts), "generated_prompts.txt")

