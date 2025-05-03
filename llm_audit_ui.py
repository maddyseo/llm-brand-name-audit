import openai
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import random

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client_gs = gspread.authorize(creds)
sheet = client_gs.open("LLM Brand Mention Audit").sheet1

# Streamlit UI
st.title("LLM Brand Mention Audit - A Tool by Maddy")
st.markdown("Enter prompts to check if your brand appears in ChatGPT's responses.")

# Default prompts
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

# --------------------------
# NEW: Prompt Generator (Phase 1) with new fields

st.markdown("---")
st.header("✨ Want us to generate prompts for you?")

# Session state to keep expander open
if "generate_clicked" not in st.session_state:
    st.session_state.generate_clicked = False

if st.button("Generate Prompts for You"):
    st.session_state.generate_clicked = True

if st.session_state.generate_clicked:
    with st.expander("Fill in your business details to generate prompts", expanded=True):
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
                # Parse services into list
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
