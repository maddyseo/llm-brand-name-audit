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

# -----------------------------------
# NEW: Prompt Generator Section (Phase 1)

st.markdown("---")
st.header("✨ Want us to generate prompts for you?")

# Use session state to persist button click
if "generate_clicked" not in st.session_state:
    st.session_state.generate_clicked = False

if st.button("Generate Prompts for You"):
    st.session_state.generate_clicked = True

if st.session_state.generate_clicked:
    with st.expander("Fill in your business details to generate prompts", expanded=True):
        business = st.text_input("Business nature (e.g., event tech, shoe brand):")
        location = st.text_input("Location (e.g., USA, Europe):")
        audience = st.text_input("Target audience (optional):")

        def generate_prompts(business, location, audience):
            base_prompts = [
                f"What’s the best {business} in {location}?",
                f"Top-rated {business} companies in {location}",
                f"Best alternatives to popular {business} solutions",
                f"How does {business} help {audience} in {location}?",
                f"What’s the future of {business} in {location}?",
                f"Affordable {business} providers in {location}",
                f"Top features to look for in {business} tools",
                f"How to choose the right {business} for {audience}",
                f"Reviews of {business} solutions in {location}",
                f"Case studies of successful {business} implementations",
            ]
            prompts = []
            for _ in range(100):
                prompts.append(random.choice(base_prompts))
            return prompts

        if st.button("Generate Prompts"):
            if not business or not location:
                st.warning("Please provide at least Business nature and Location.")
            else:
                generated_prompts = generate_prompts(business, location, audience)
                st.success(f"Generated {len(generated_prompts)} prompts!")

                for idx, prompt in enumerate(generated_prompts, 1):
                    st.write(f"{idx}. {prompt}")

                prompts_text = "\n".join(generated_prompts)
                st.download_button("📥 Download Prompts (.txt)", prompts_text, file_name="generated_prompts.txt")
                st.text_area("📋 Copy Prompts", prompts_text, height=300)
