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
    body, .main, .block-container {
        background-color: #ffffff;
        color: #000000;
    }
    .block-container {
        max-width: 100%;
        padding: 2rem 3rem;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #6a11cb, #2575fc);
        color: white;
    }
    .sidebar-item {
        padding: 10px 15px;
        margin: 5px 0;
        border-radius: 5px;
        cursor: pointer;
    }
    .sidebar-item:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
    .sidebar-item-active {
        background-color: rgba(255, 255, 255, 0.3);
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar navigation logic
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "Run Audit"

def sidebar_item(label, key):
    selected = st.session_state.selected_page == key
    css_class = "sidebar-item-active" if selected else "sidebar-item"
    st.sidebar.markdown(f'<div class="{css_class}">{label}</div>', unsafe_allow_html=True)
    if st.sidebar.button(label, key=key):
        st.session_state.selected_page = key

st.sidebar.markdown("## Navigation")
sidebar_item("🏃‍♂️ Run Audit", "Run Audit")
sidebar_item("✨ Generate Prompts", "Generate Prompts")

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client_gs = gspread.authorize(creds)
sheet = client_gs.open("LLM Brand Mention Audit").sheet1

# ----------------------
# PAGE 1: RUN AUDIT
if st.session_state.selected_page == "Run Audit":
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

        results = []

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

                results.append([prompt, brand, "Yes" if mentioned else "No"])

            except Exception as e:
                results.append([prompt, brand, f"Error: {str(e)}"])

        # Update Google Sheet
        sheet.clear()
        sheet.append_row(["Prompt", "Brand", "Mentioned?"])
        for row in results:
            sheet.append_row(row)

        st.success("Audit complete! ✅")
        st.dataframe(results, use_container_width=True)

# ----------------------
# PAGE 2: GENERATE PROMPTS
elif st.session_state.selected_page == "Generate Prompts":
    st.title("✨ Generate Prompts for Your Business")

    if "generate_clicked" not in st.session_state:
        st.session_state.generate_clicked = True  # Keep expander open by default

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
