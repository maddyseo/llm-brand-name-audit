from datetime import datetime
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import streamlit as st  # Required to read st.secrets in Streamlit context

# Initialize OpenAI client
client_ai = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Google Sheets setup using secrets.toml
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client_gs = gspread.authorize(creds)
sheet = client_gs.open("LLM Brand Mention Audit").sheet1

# Prompts and keywords
prompts = [
    "What’s the best live Q&A tool?",
    "What software do teachers use for polls?",
    "Which event tools help with employee engagement?",
    "Best polling tool for university lectures",
    "Top interactive Q&A platforms for webinars"
]

brand_keywords = ["Pigeonhole Live", "pigeonholelive"]

def check_brand_mentions(response_text):
    return any(brand.lower() in response_text.lower() for brand in brand_keywords)

# Add headers if empty
if not sheet.row_values(1):
    sheet.append_row(["Timestamp", "Prompt", "Mention Found", "Extracted Response"])

# Run audit
for prompt in prompts:
    try:
        response = client_ai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        reply_text = response.choices[0].message.content.strip()
        mentioned = "Yes" if check_brand_mentions(reply_text) else "No"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, prompt, mentioned, reply_text])
        print(f"✅ Prompt: {prompt} → Mention Found: {mentioned}")
    except Exception as e:
        print(f"❌ Error with prompt '{prompt}': {e}")
