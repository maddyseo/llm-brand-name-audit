import openai
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import random
import pandas as pd
from datetime import datetime

# CSS STYLING (UPDATED)
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
    [data-testid="stSidebar"] .stButton > button {
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
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255,255,255,0.3);
    }
    .stButton > button {
        display: block;
        width: 100%;
        padding: 10px 20px;
        margin: 5px 0;
        font-weight: bold;
        border-radius: 8px;
        color: white;
        background-color: #ff7f50;
        border: none;
        transition: background-color 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #6a11cb;
    }
    .zebra tr:nth-child(even) {
        background-color: rgba(255,255,255,0.03);
    }
    </style>
""", unsafe_allow_html=True)

# Session state
if "page" not in st.session_state:
    st.session_state.page = "Run Audit"
if "audit_results" not in st.session_state:
    st.session_state.audit_results = []
if "saved_prompts" not in st.session_state:
    st.session_state.saved_prompts = []
if "saved_indices" not in st.session_state:
    st.session_state.saved_indices = set()

# Navigation
with st.sidebar:
    st.markdown("### Navigation")
    if st.button("🏃 Run Audit"):
        st.session_state.page = "Run Audit"
    if st.button("✨ Generate Prompts"):
        st.session_state.page = "Generate Prompts"
    if st.button("🖫 Saved Prompts"):
        st.session_state.page = "Saved Prompts"

# OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client_gs = gspread.authorize(creds)
sheet = client_gs.open("LLM Brand Mention Audit").sheet1

# -------- RUN AUDIT --------
if st.session_state.page == "Run Audit":
    st.title("Maddy")
    st.markdown("Enter prompts to check if your brand appears in ChatGPT's responses.")

    prompts_text = st.text_area("Enter one prompt per line:", value="What's the best shoe brand in USA\nWhat's most comfortable shoe you can recommend\nBest Addidas alternative\nShoes suitable for running\nTop 3 shoe brands in USA")
    brand = st.text_input("Brand name to track (e.g., Nike):", value="Nike")

    if st.button("Run Audit"):
        st.session_state.audit_results = []
        st.session_state.saved_indices = set()
        prompt_list = prompts_text.strip().split("\n")
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
                st.session_state.audit_results.append({
                    "Prompt": prompt,
                    "Brand": brand,
                    "Mentioned": "Yes" if mentioned else "No"
                })
            except Exception as e:
                st.session_state.audit_results.append({
                    "Prompt": prompt,
                    "Brand": brand,
                    "Mentioned": f"Error: {str(e)}"
                })

    if st.session_state.audit_results:
        st.subheader("Audit Results")
        st.markdown("**Prompt | Brand | Mentioned | Save**")
        df = pd.DataFrame(st.session_state.audit_results)
        for i, row in df.iterrows():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            col1.write(row["Prompt"])
            col2.write(row["Brand"])
            col3.write(row["Mentioned"])
            if i in st.session_state.saved_indices:
                col4.button("✅", key=f"saved_{i}", disabled=True)
            else:
                if col4.button("➕", key=f"save_{i}"):
                    if len(st.session_state.saved_prompts) < 100:
                        st.session_state.saved_prompts.append({
                            "Prompt": row["Prompt"],
                            "Result": row["Mentioned"],
                            "Date Saved": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        st.session_state.saved_indices.add(i)
                        st.rerun()

        if st.button("💾 Save All Prompts"):
            for i, row in df.iterrows():
                if i not in st.session_state.saved_indices and len(st.session_state.saved_prompts) < 100:
                    st.session_state.saved_prompts.append({
                        "Prompt": row["Prompt"],
                        "Result": row["Mentioned"],
                        "Date Saved": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    st.session_state.saved_indices.add(i)
            st.rerun()

        csv = pd.DataFrame(st.session_state.audit_results).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Audit Results (.csv)", csv, file_name="audit_results.csv")

# -------- SAVED PROMPTS --------
elif st.session_state.page == "Saved Prompts":
    st.title("💾 Saved Prompts")
    st.write(f"{len(st.session_state.saved_prompts)}/100 prompts saved")

    if len(st.session_state.saved_prompts) == 0:
        st.info("🚫 You haven’t saved any prompts yet. Run an audit and click ➕ to add prompts here.")
    else:
        saved_df = pd.DataFrame(st.session_state.saved_prompts)
        for idx, row in saved_df.iterrows():
            cols = st.columns([3, 1, 2, 1])
            cols[0].write(row["Prompt"])
            cols[1].write(row["Result"])
            cols[2].write(row["Date Saved"])
            if cols[3].button("❌", key=f"delete_{idx}"):
                del st.session_state.saved_prompts[idx]
                st.session_state.saved_indices.discard(idx)
                st.rerun()

# -------- GENERATE PROMPTS --------
# Add this inside your "Generate Prompts" section in the final `elif` block
elif st.session_state.page == "Generate Prompts":
    st.title("✨ Generate Prompts for Your Business")
    with st.expander("Fill in your business details to generate prompts", expanded=True):
        business_name = st.text_input("Business Name (e.g., Aspen Services):")
        services_input = st.text_area("Services you offer (one per line):")
        business_description = st.text_area("Tell us more about your business:")
        location = st.text_input("Location (e.g., Brisbane, Gold Coast):")
        audience = st.text_input("Target audience (optional):")
        seo_keywords_input = st.text_area("SEO Keywords (one per line):")
        is_global = st.checkbox("🌍 My business serves globally or in multiple countries")
        num_prompts = st.number_input("How many prompts to generate? (1–100)", min_value=1, max_value=100, value=50)

        def generate_prompts_v2(business_name, services, business_description, location, audience, seo_keywords, is_global, count):
            import openai
            base_instruction = (
                "You are an expert in AI brand visibility and prompt generation."
                "Your task is to generate natural prompts that a potential customer would enter into AI tools like ChatGPT when actively looking for a product or service related to the business provided."
                "Each prompt must reflect clear commercial or transactional intent — for example: a person looking to discover, compare, or evaluate businesses, services, or providers."
                "You must use the provided business services, business description, location, and SEO keywords to influence your prompt generation. DO NOT make the prompts sound like ads or educational questions."
                "Only include prompts that would naturally result in the LLM mentioning brands or business names in its response. You can ignore any keyword that includes “near me”."
                "The prompts should be phrased in the way someone would actually search in ChatGPT or Google when trying to find a business like the one described."
                "Respond with only the list of prompts. No extra commentary. Dont include bullets or numbers just list down prompts one after the other"
            )

            prompt_data = (
                f"\nBusiness Name: {business_name}\n"
                f"Business Services: {services}\n"
                f"Business Description: {business_description}\n"
                f"Location: {'Global' if is_global else location}\n"
                f"Target Audience: {audience}\n"
                f"SEO Keywords: {seo_keywords}"
            )

            full_prompt = (
                f"{base_instruction}\n{prompt_data}\n\n"
                f"Generate {count} natural language prompts:"
            )

            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful AI marketing assistant."},
                        {"role": "user", "content": full_prompt}
                    ]
                )
                reply = response.choices[0].message.content
                generated = [line.strip("- ").strip() for line in reply.split("\n") if line.strip()]
                return generated
            except Exception as e:
                st.error(f"❌ Failed to generate prompts: {e}")
                return []

        if st.button("Generate Prompts"):
            if not business_name or not services_input or not location:
                st.warning("⚠️ Please fill in Business Name, Services, and Location.")
            else:
                services = [s.strip() for s in services_input.split("\n") if s.strip()]
                seo_keywords = [k.strip() for k in seo_keywords_input.split("\n") if k.strip()]
                prompts = generate_prompts_v2(
                    business_name=business_name,
                    services=services,
                    business_description=business_description,
                    location=location,
                    audience=audience,
                    seo_keywords=seo_keywords,
                    is_global=is_global,
                    count=num_prompts
                )
                if prompts:
                    st.success(f"✅ Generated {len(prompts)} prompts!")
                    full_text = "\n".join(prompts)
                    st.download_button("📥 Download Prompts (.txt)", full_text, file_name="generated_prompts.txt")
                    st.text_area("📋 Copy Prompts", full_text, height=300)
