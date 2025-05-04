import openai
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import random
import pandas as pd
from datetime import datetime

# --- CSS ---
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

# --- SESSION STATE ---
if "page" not in st.session_state: st.session_state.page = "Run Audit"
if "saved_prompts" not in st.session_state: st.session_state.saved_prompts = []
if "audit_results" not in st.session_state: st.session_state.audit_results = []

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### Navigation")
    audit_clicked = st.button("🏃‍♂️ Run Audit", key="nav_audit")
    prompts_clicked = st.button("✨ Generate Prompts", key="nav_prompts")
    saved_clicked = st.button("💾 Saved Prompts", key="nav_saved")
    if audit_clicked: st.session_state.page = "Run Audit"
    if prompts_clicked: st.session_state.page = "Generate Prompts"
    if saved_clicked: st.session_state.page = "Saved Prompts"
    st.markdown(f"""
        <style>
        [key="nav_audit"] > button {'{ background-color: rgba(255,255,255,0.5); color: black; }' if st.session_state.page == 'Run Audit' else ''}
        [key="nav_prompts"] > button {'{ background-color: rgba(255,255,255,0.5); color: black; }' if st.session_state.page == 'Generate Prompts' else ''}
        [key="nav_saved"] > button {'{ background-color: rgba(255,255,255,0.5); color: black; }' if st.session_state.page == 'Saved Prompts' else ''}
        </style>
    """, unsafe_allow_html=True)

# --- OpenAI ---
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client_gs = gspread.authorize(creds)
sheet = client_gs.open("LLM Brand Mention Audit").sheet1

# --- RUN AUDIT PAGE ---
if st.session_state.page == "Run Audit":
    st.title("Maddy")
    st.markdown("Enter prompts to check if your brand appears in ChatGPT's responses.")
    prompts = st.text_area("Enter one prompt per line:", "\n".join([
        "What’s the best shoe brand in USA",
        "What's most comfortable shoe you can recommend",
        "Best Addidas alternative",
        "Shoes suitable for running",
        "Top 3 shoe brands in USA"
    ]))
    brand = st.text_input("Brand name to track (e.g., Nike):", value="Nike")

    if st.button("Run Audit"):
        prompt_list = prompts.split("\n")
        results = []
        for prompt in prompt_list:
            if not prompt.strip(): continue
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                reply = response.choices[0].message.content
                mentioned = "Yes" if brand.lower() in reply.lower() else "No"
                results.append({"Prompt": prompt, "Brand": brand, "Mentioned": mentioned})
            except Exception as e:
                results.append({"Prompt": prompt, "Brand": brand, "Mentioned": f"Error: {str(e)}"})
        st.session_state.audit_results = results

    if st.session_state.audit_results:
        st.write("### Audit Results")
        for idx, row in enumerate(st.session_state.audit_results):
            cols = st.columns([4, 1, 1, 1])
            cols[0].write(row["Prompt"])
            cols[1].write(row["Brand"])
            cols[2].write(row["Mentioned"])
            save_key = f"savebtn_{idx}"
            if any(p["Prompt"] == row["Prompt"] for p in st.session_state.saved_prompts):
                cols[3].success("✅ Saved")
            else:
                if cols[3].button("➕", key=save_key):
                    if len(st.session_state.saved_prompts) < 100:
                        st.session_state.saved_prompts.append({
                            "Prompt": row["Prompt"],
                            "Result": row["Mentioned"],
                            "Date Saved": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        st.experimental_rerun()
                    else:
                        st.warning("Max 100 saved prompts!")

        df = pd.DataFrame(st.session_state.audit_results)
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Audit Results (.csv)", csv_data, file_name="audit_results.csv")

# --- GENERATE PROMPTS PAGE ---
elif st.session_state.page == "Generate Prompts":
    st.title("✨ Generate Prompts for Your Business")
    if "generate_clicked" not in st.session_state: st.session_state.generate_clicked = True
    with st.expander("Fill in your business details to generate prompts", expanded=st.session_state.generate_clicked):
        business_name = st.text_input("Business Name (e.g., Aspen Services):")
        services_input = st.text_area("Services you offer (one per line):")
        location = st.text_input("Location (e.g., Brisbane, Gold Coast):")
        prompt_count = st.number_input("How many prompts (1-100):", min_value=1, max_value=100, value=10)
        def generate_prompts(services, location, count):
            locs = [location]
            if "brisbane" in location.lower(): locs.extend(["Gold Coast", "Sunshine Coast", "Queensland"])
            templates = [
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
            return [random.choice(templates).format(service=random.choice(services), loc=random.choice(locs)) for _ in range(count)]
        if st.button("Generate Prompts"):
            if not business_name or not services_input or not location:
                st.warning("Fill all required fields.")
            else:
                services = [s.strip() for s in services_input.split("\n") if s.strip()]
                if not services: st.warning("Add at least one service.")
                else:
                    generated = generate_prompts(services, location, prompt_count)
                    st.success(f"Generated {len(generated)} prompts!")
                    for idx, prompt in enumerate(generated, 1): st.write(f"{idx}. {prompt}")
                    prompts_text = "\n".join(generated)
                    st.download_button("📥 Download Prompts (.txt)", prompts_text, file_name="generated_prompts.txt")
                    st.text_area("📋 Copy Prompts", prompts_text, height=300)

# --- SAVED PROMPTS PAGE ---
elif st.session_state.page == "Saved Prompts":
    st.title("💾 Saved Prompts")
    st.markdown(f"**{len(st.session_state.saved_prompts)}/100 prompts saved**")
    if st.session_state.saved_prompts:
        for idx, row in enumerate(st.session_state.saved_prompts):
            cols = st.columns([4, 1, 2, 1])
            cols[0].write(row["Prompt"])
            cols[1].write(row["Result"])
            cols[2].write(row["Date Saved"])
            if cols[3].button("❌", key=f"delete_{idx}"):
                st.session_state.saved_prompts.pop(idx)
                st.experimental_rerun()
    else:
        st.info("No saved prompts yet.")
