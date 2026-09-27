"""Chat With CSV - Streamlit UI.

Ask natural-language questions about a CSV file; Gemini writes and runs
pandas code and the app returns the answer.

Extended/maintained by Muhammad Huzaifa Aqeel (HuzaifaAqeel).
Original project: https://github.com/Victormartinsilva/Chat_Bot_Consulta_Dados
(MIT License).
"""
import streamlit as st
import pandas as pd
import os

from chatbot import gerar_resposta, GEMINI_MODEL

# --- Page config ---
st.set_page_config(page_title="Chat With CSV (Gemini + Pandas)", layout="wide")

# --- Title and description ---
st.title("📊 Chat With CSV")
st.markdown(
    """
    Ask natural-language questions about your CSV data (`data.csv`).

    Powered by **Google Gemini** (`gemini-2.5-flash`) and **Pandas**:
    the model writes Python code for your question, executes it against the
    dataset, and explains the result.
    """
)


# Secrets helper (supports Streamlit Cloud secrets and local .env)
def get_secret(key, default=None):
    """Reads a secret from Streamlit Cloud or a local environment variable."""
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)


st.info(f"🔧 LLM provider: **Google Gemini** (`{GEMINI_MODEL}`)")

if not get_secret("GOOGLE_API_KEY"):
    st.warning(
        "⚠️ `GOOGLE_API_KEY` was not found. Set it in Streamlit secrets "
        "or in a local `.env` file. Get one for free at: "
        "https://makersuite.google.com/app/apikey"
    )
    st.stop()

# --- CSV loading and preview ---
CSV_FILE_PATH = "data.csv"
CSV_URL = get_secret("CSV_URL", None)  # optional: load CSV from a URL (e.g. Streamlit Cloud)

try:
    if CSV_URL:
        df = pd.read_csv(CSV_URL)
        st.success(f"✅ CSV loaded from URL: {CSV_URL}")
    else:
        df = pd.read_csv(CSV_FILE_PATH)
        st.success(f"✅ CSV loaded from local file: {CSV_FILE_PATH}")
    st.subheader("Loaded DataFrame preview")
    st.dataframe(df.head())
    st.info(f"DataFrame loaded: {df.shape[0]} rows and {df.shape[1]} columns.")
except FileNotFoundError:
    st.error(
        f"Error: CSV file not found at {CSV_FILE_PATH}. "
        "Make sure 'data.csv' is in the app directory."
    )
    st.stop()
except Exception as e:
    st.error(f"Error loading the DataFrame: {e}")
    st.stop()

# --- Chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": "Hi! I'm your data assistant. Ask me anything about the DataFrame above!",
        }
    )

if "raciocinios" not in st.session_state:
    st.session_state.raciocinios = {}

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["content"].startswith(("⚠️", "🔑", "❌")):
            st.error(message["content"])
        else:
            st.markdown(message["content"])

    # Show the generated Python code below the message (kept outside the chat bubble)
    if message["role"] == "assistant" and i in st.session_state.raciocinios:
        raciocinio = st.session_state.raciocinios[i]
        if raciocinio and raciocinio.strip():
            with st.expander("🔍 Generated Python code", expanded=False):
                st.code(raciocinio, language="python")

# --- Example questions ---
st.sidebar.header("Example questions")
for example in [
    "What is the average of each numeric column?",
    "Which row has the highest value in the price column?",
    "Are there any missing values?",
    "Summarize this dataset.",
]:
    if st.sidebar.button(example):
        st.session_state.messages.append({"role": "user", "content": example})
        st.rerun()

# --- User input ---
if prompt := st.chat_input("Ask a question about your data..."):
    # 1. Record the user's message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Render it immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    # 3. Generate the answer
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resposta_final, raciocinio = gerar_resposta(prompt, df=df)
            except Exception as e:
                resposta_final = f"❌ **Unexpected error:** {str(e)}"
                raciocinio = ""

        if resposta_final.startswith(("⚠️", "🔑", "❌")):
            st.error(resposta_final)
        else:
            st.markdown(resposta_final)

        if raciocinio and raciocinio.strip():
            with st.expander("🔍 Generated Python code", expanded=False):
                st.code(raciocinio, language="python")

    # 4. Store the assistant's reply
    indice_resposta = len(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": resposta_final})

    # 5. Store the generated code
    if raciocinio and raciocinio.strip():
        st.session_state.raciocinios[indice_resposta] = raciocinio
