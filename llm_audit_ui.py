import openai
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        .main {
            background-color: white;
            color: black;
        }
        .stTextInput>div>div>input, .stTextArea>div>textarea {
            background-color: white;
            color: black;
        }
        .stButton>button {
            background-color: black;
            color: white;
            border-radius: 8px;
            padding: 8px 16px;
        }
        .sidebar .active-tab {
            background: rgba(255, 255, 255, 0.2);
            border-left: 4px solid white;
            padding-left: 8px;
            font-weight: bold;
        }
        .sidebar .inactive-tab {
            opacity: 0.7;
        }
        .st-emotion-cache-1v0mbdj {
            background: linear-gradient(to bottom, #6a11cb, #2575fc) !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAV ---
st.sidebar.title("Navigation")

tabs = ["Run Audit", "Generate Prompts"]
active_tab = st.sidebar.radio("",
                              tabs,
                              label_visibility="collapsed",
                              index=0)

# --- Highlight active tab ---
for i, tab in enumerate(tabs):
    if tab == active_tab:
        st.sidebar.markdown(f"<div class='active-tab'>{tab}</div>", unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"<div class='inactive-tab'>{tab}</div>", unsafe_allow_html=True)

# --- GOOGLE SHEETS SETUP ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client_gs = gspread.authorize(creds)
sheet = client_gs.open("LLM Brand Mention Audit").sheet1

# --- OPENAI CLIENT ---
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- TAB LOGIC ---
if active_tab == "Run Audit":
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

        sheet.clear()
        sheet.append_row(["Prompt", "Brand", "Mentioned?"])
        for row in results:
            sheet.append_row(row)

        st.success("Audit complete! ✅")
        st.dataframe(results, use_container_width=True)

elif active_tab == "Generate Prompts":
    st.title("✨ Generate Prompts for Your Business")
    with st.expander("Fill in your business details to generate prompts"):
        business_name = st.text_input("Business Name (e.g., Aspen Services):")
        services = st.text_area("Services you offer (one per line):")
        business_nature = st.text_area("Tell us more about your business:")
        location = st.text_input("Location (e.g., Brisbane, Gold Coast):")
        target_audience = st.text_input("Target audience (optional):")

    if st.button("Generate Prompts"):
        generated_prompts = []
        for service in services.split("\n"):
            service = service.strip()
            if service:
                generated_prompts.extend([
                    f"Best {service} companies in {location}",
                    f"Affordable {service} services near me",
                    f"Top-rated {service} providers in {location}",
                    f"Popular {service} businesses in {location}",
                    f"Where to find trusted {service} experts in {location}"
                ])
        st.markdown("#### Generated Prompts:")
        for i, prompt in enumerate(generated_prompts, start=1):
            st.write(f"{i}. {prompt}")
