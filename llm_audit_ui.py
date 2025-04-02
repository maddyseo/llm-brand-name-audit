import openai
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# Set OpenAI API key from env
openai.api_key = os.getenv("OPENAI_API_KEY")

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
import json
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)
sheet = client.open("LLM Brand Mention Audit").sheet1

# Streamlit UI
st.title("🔍 LLM Brand Mention Audit")
st.markdown("Enter prompts to check if your brand appears in ChatGPT's responses.")

# Default prompts
default_prompts = [
    "What’s the best live Q&A tool?",
    "What software do teachers use for polls?",
    "Which event tools help with employee engagement?",
    "Best polling tool for university lectures",
    "Top interactive Q&A platforms for webinars"
]

prompts = st.text_area("Enter one prompt per line:", value="\n".join(default_prompts))
brand = st.text_input("Brand name to track (e.g., Pigeonhole Live):", value="Pigeonhole Live")

if st.button("Run Audit"):
    prompt_list = prompts.split("\n")
    st.write("Running audits...")

    results = []

    for prompt in prompt_list:
        if not prompt.strip():
            continue
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            reply = response['choices'][0]['message']['content']
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
