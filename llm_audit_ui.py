import streamlit as st
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client_gs = gspread.authorize(creds)
sheet = client_gs.open("LLM Brand Mention Audit").sheet1

# --- Sidebar Styling ---
st.markdown(
    """
    <style>
    .css-1544g2n { background: linear-gradient(to bottom, #7b2ff7, #00c6ff); }
    .stButton > button {
        width: 100%;
        margin-bottom: 10px;
        background-color: white;
        color: black;
        border-radius: 8px;
        border: none;
        padding: 0.5rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #f0f0f0;
    }
    .active-button {
        background-color: #333 !important;
        color: white !important;
    }
    .main { background-color: white; }
    .stTextInput input, .stTextArea textarea {
        background-color: white;
        color: black;
    }
    .stMarkdown { color: black; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Sidebar navigation ---
selected_tab = st.sidebar.radio(
    "Navigation",
    ["Run Audit", "Generate Prompts"],
    index=0,
    format_func=lambda x: f"✨ {x}" if x == "Generate Prompts" else f"🏃 {x}"
)

# Make sidebar buttons styled
if selected_tab == "Run Audit":
    st.sidebar.markdown('<div class="active-button">🏃 Run Audit</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div>✨ Generate Prompts</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<div>🏃 Run Audit</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="active-button">✨ Generate Prompts</div>', unsafe_allow_html=True)

# --- Main content ---
if selected_tab == "Run Audit":
    st.title("LLM Brand Mention Audit - A Tool by Maddy")
    st.write("Enter prompts to check if your brand appears in ChatGPT's responses.")
    
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

elif selected_tab == "Generate Prompts":
    st.title("✨ Generate Prompts for Your Business")
    with st.expander("Fill in your business details to generate prompts"):
        business_name = st.text_input("Business Name (e.g., Aspen Services):")
        services = st.text_area("Services you offer (one per line):")
        business_nature = st.text_area("Tell us more about your business:")
        location = st.text_input("Location (e.g., Brisbane, Gold Coast):")
        audience = st.text_input("Target audience (optional):")

    if st.button("Generate Prompts"):
        st.write("Generated Prompts:")
        prompts = []
        service_lines = services.split("\n")
        for service in service_lines:
            if service.strip():
                prompts.append(f"Best {service.strip()} in {location}")
                prompts.append(f"{service.strip()} companies in {location}")
                prompts.append(f"Affordable {service.strip()} services in {location}")
        for p in prompts:
            st.write(f"- {p}")
