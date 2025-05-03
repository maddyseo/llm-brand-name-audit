import openai
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import random

# Inject custom CSS
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

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "Run Audit"

if "saved_prompts" not in st.session_state:
    st.session_state.saved_prompts = []

if "audit_results" not in st.session_state:
    st.session_state.audit_results = []

# Sidebar navigation
with st.sidebar:
    st.markdown("### Navigation")
    audit_clicked = st.button("🏃‍♂️ Run Audit", key="nav_audit")
    prompts_clicked = st.button("✨ Generate Prompts", key="nav_prompts")
    saved_clicked = st.button("💾 Saved Prompts", key="nav_saved")

    if audit_clicked:
        st.session_state.page = "Run Audit"
    if prompts_clicked:
        st.session_state.page = "Generate Prompts"
    if saved_clicked:
        st.session_state.page = "Saved Prompts"

    st.markdown(f"""
        <style>
        [key="nav_audit"] > button {'{ background-color: rgba(255,255,255,0.5); color: black; }' if st.session_state.page == 'Run Audit' else ''}
        [key="nav_prompts"] > button {'{ background-color: rgba(255,255,255,0.5); color: black; }' if st.session_state.page == 'Generate Prompts' else ''}
        [key="nav_saved"] > button {'{ background-color: rgba(255,255,255,0.5); color: black; }' if st.session_state.page == 'Saved Prompts' else ''}
        </style>
    """, unsafe_allow_html=True)

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client_gs = gspread.authorize(creds)
sheet = client_gs.open("LLM Brand Mention Audit").sheet1

# --- PAGE: RUN AUDIT ---
if st.session_state.page == "Run Audit":
    st.title("LLM Brand Mention Audit - A Tool by Maddy")
    st.markdown("Enter prompts to check if your brand appears in ChatGPT's responses.")

    default_prompts = [
        "What’s the best shoe brand in USA",
        "What's most comfortable shoe you can recommend",
        "Best Addidas alternative",
        "Shoes suitable for running",
        "Top 3 shoe brands in USA"
    ]

    prompts = st.text_area("Enter one prompt per line:", value="\n".join(default_prompts))
    brand = st.text_input("Brand name to track (e.g., Nike):", value="Nike")

    if st.button("Run Audit"):
        prompt_list = prompts.split("\n")
        st.write("Running audits...")

        audit_results = []
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
                audit_results.append({"prompt": prompt, "brand": brand, "mentioned": "Yes" if mentioned else "No"})
            except Exception as e:
                audit_results.append({"prompt": prompt, "brand": brand, "mentioned": f"Error: {str(e)}"})

        st.session_state.audit_results = audit_results

        sheet.clear()
        sheet.append_row(["Prompt", "Brand", "Mentioned?"])
        for row in audit_results:
            sheet.append_row([row["prompt"], row["brand"], row["mentioned"]])

        st.success("Audit complete! ✅")

    # Display audit results from session state
    if st.session_state.audit_results:
        for idx, row in enumerate(st.session_state.audit_results):
            col1, col2 = st.columns([0.85, 0.15])
            col1.write(f"**Prompt {idx+1}:** {row['prompt']} → Mentioned: {row['mentioned']}")
            if col2.button("Save", key=f"save_{idx}"):
                if len(st.session_state.saved_prompts) >= 100:
                    st.warning("Cannot save: Maximum of 100 prompts reached.")
                else:
                    if row["prompt"] not in st.session_state.saved_prompts:
                        st.session_state.saved_prompts.append(row["prompt"])
                        st.success(f"Saved Prompt {idx+1} ✅")
                    else:
                        st.info(f"Prompt {idx+1} already saved.")

        if st.button("💾 Save All Prompts"):
            remaining_slots = 100 - len(st.session_state.saved_prompts)
            unsaved_prompts = [r["prompt"] for r in st.session_state.audit_results if r["prompt"] not in st.session_state.saved_prompts]
            to_save = unsaved_prompts[:remaining_slots]
            st.session_state.saved_prompts.extend(to_save)
            if len(unsaved_prompts) > remaining_slots:
                st.warning("Only some prompts were saved (max 100 reached).")
            else:
                st.success("All prompts saved!")

# --- PAGE: GENERATE PROMPTS ---
elif st.session_state.page == "Generate Prompts":
    st.title("✨ Generate Prompts for Your Business")

    if "generate_clicked" not in st.session_state:
        st.session_state.generate_clicked = True

    with st.expander("Fill in your business details to generate prompts", expanded=st.session_state.generate_clicked):
        business_name = st.text_input("Business Name (e.g., Aspen Services):")
        services_input = st.text_area("Services you offer (one per line):")
        business_description = st.text_area("Tell us more about your business:")
        location = st.text_input("Location (e.g., Brisbane, Gold Coast):")
        audience = st.text_input("Target audience (optional):")

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
            for _ in range(100):
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

# --- PAGE: SAVED PROMPTS ---
elif st.session_state.page == "Saved Prompts":
    st.title("💾 Saved Prompts")
    st.write(f"**{len(st.session_state.saved_prompts)}/100 prompts saved**")

    if st.session_state.saved_prompts:
        for idx, prompt in enumerate(st.session_state.saved_prompts):
            col1, col2 = st.columns([0.9, 0.1])
            col1.write(f"{idx+1}. {prompt}")
            if col2.button("❌", key=f"del_{idx}"):
                st.session_state.saved_prompts.pop(idx)
                st.experimental_rerun()
    else:
        st.info("No saved prompts yet.")
