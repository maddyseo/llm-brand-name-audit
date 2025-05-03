import openai
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

# --- Initialize OpenAI client ---
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Google Sheets setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client_gs = gspread.authorize(creds)
sheet = client_gs.open("LLM Brand Mention Audit").sheet1

# --- Sidebar navigation ---
st.markdown("""
    <style>
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #7b2ff7, #3b8dff);
        color: white;
    }
    .sidebar .sidebar-content a {
        color: white;
        font-weight: bold;
        text-decoration: none;
        display: block;
        padding: 8px 16px;
        margin: 4px 0;
        border-radius: 8px;
    }
    .sidebar .sidebar-content a.active {
        background-color: rgba(255,255,255,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# --- Navigation ---
page = st.sidebar.radio("Navigation", ["Run Audit", "Generate Prompts"], index=0)

# --- Set active tab styling ---
st.sidebar.markdown(
    f"""
    <a href="#" class="{ 'active' if page == 'Run Audit' else '' }">🏃‍♂️ Run Audit</a>
    <a href="#" class="{ 'active' if page == 'Generate Prompts' else '' }">✨ Generate Prompts</a>
    """,
    unsafe_allow_html=True
)

# --- Main page background white ---
st.markdown("""
    <style>
    .main {
        background-color: white;
        color: black;
        padding: 2rem;
    }
    .stTextInput > div > input, .stTextArea > div > textarea {
        background-color: white;
        color: black;
    }
    </style>
""", unsafe_allow_html=True)

# --- Run Audit Page ---
if page == "Run Audit":
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

# --- Generate Prompts Page ---
elif page == "Generate Prompts":
    st.title("✨ Generate Prompts for Your Business")
    with st.expander("Fill in your business details to generate prompts"):
        business_name = st.text_input("Business Name (e.g., Aspen Services):")
        services = st.text_area("Services you offer (one per line):")
        description = st.text_area("Tell us more about your business:")
        location = st.text_input("Location (e.g., Brisbane, Gold Coast):")
        audience = st.text_input("Target audience (optional):")

    if st.button("Generate Prompts"):
        st.write("Generating prompts...")
        prompts_list = []
        if services:
            for svc in services.split("\n"):
                if svc.strip():
                    prompts_list.append(f"Best {svc.strip()} services in {location}")
                    prompts_list.append(f"{svc.strip()} companies in {location}")
                    prompts_list.append(f"Top-rated {svc.strip()} providers near me")
                    prompts_list.append(f"Affordable {svc.strip()} solutions in {location}")
        else:
            prompts_list.append(f"Best services in {location}")

        st.write("Here are your prompts:")
        for i, prompt in enumerate(prompts_list, 1):
            st.write(f"{i}. {prompt}")
