"""Chat With CSV - natural-language questions over a CSV dataset.

Pipeline: Gemini writes pandas code -> the code is executed against `df` ->
Gemini turns the raw result into a human-readable answer.

Extended/maintained by Muhammad Huzaifa Aqeel (HuzaifaAqeel).
Original project: https://github.com/Victormartinsilva/Chat_Bot_Consulta_Dados
(MIT License).
"""
import os
import re
import io
import contextlib
import traceback

import pandas as pd
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Default CSV filename (relative to the app's working directory)
CSV_FILE_PATH = "data.csv"

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

CODE_PROMPT_TEMPLATE = """You are an expert pandas programmer. Given a CSV dataset
already loaded in a pandas DataFrame called `df`, write Python code that
answers the user's question.

Rules:
- The dataframe `df` is already loaded. `pd` (pandas) is already imported.
- Your ONLY output must be a single ```python code block, nothing else.
- Always print() the final result you want observed (e.g. print(df.head())).
- Do not import any modules. Do not use os, sys, subprocess, socket or shutil.
- Answer the question about the data; do not explain the code.

Dataset schema:
{schema}

User question:
{question}
"""

ANSWER_PROMPT_TEMPLATE = """You are a friendly data analyst. Turn the result of a pandas
computation into a short, human-readable answer in flowing prose.

The user asked:
{question}

The computed result was:
{result}

Reply in a couple of sentences. Do not mention Python code or the raw
result format unless the user asked for it.
"""


def get_secret(key, default=None):
    """Reads a secret from the environment (Streamlit secrets supported by the app)."""
    return os.getenv(key, default)


def get_llm():
    """Builds the Gemini chat model used by the whole pipeline."""
    api_key = get_secret("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found. Set it as an environment variable or in .env"
        )
    return ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0)


def load_df(path=CSV_FILE_PATH):
    """Loads the CSV into a DataFrame (utf-8 with latin-1 fallback)."""
    try:
        return pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin-1")


def describe_df(df):
    """Builds a compact text schema of the DataFrame for the LLM."""
    info = [
        f"Shape: {df.shape[0]} rows, {df.shape[1]} columns",
        "Columns and dtypes:",
    ]
    for col, dtype in df.dtypes.items():
        info.append(f"  - {col}: {dtype}")
    info.append("First 3 rows:")
    info.append(df.head(3).to_string())
    return "\n".join(info)


def extract_code(text):
    """Extracts the python code block from an LLM response."""
    match = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    code = match.group(1).strip() if match else text.strip()
    if code.startswith("python"):
        code = code[len("python"):].strip()
    return code


def run_python_code(code, df):
    """Executes pandas code against `df` and returns stdout."""
    dangerous = ["os", "sys", "subprocess", "socket", "shutil"]
    for d in dangerous:
        if f"import {d}" in code or f"from {d}" in code:
            return f"Error: importing '{d}' is not allowed for security reasons."

    namespace = {"df": df, "pd": pd}
    output_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(output_buffer):
            exec(code, namespace)
        output = output_buffer.getvalue()
        if not output.strip():
            return "Code executed successfully but produced no print output."
        if len(output) > 4000:
            output = output[:4000] + "\n... (output truncated)"
        return output
    except Exception:
        return f"Error executing code:\n{traceback.format_exc()}"


def gerar_resposta(pergunta, df=None, csv_path=CSV_FILE_PATH):
    """Answers a natural-language question about the CSV.

    Returns a tuple (resposta, raciocinio): the human-readable answer and
    the Python code the model generated/executed.
    """
    if df is None:
        try:
            df = load_df(csv_path)
        except FileNotFoundError:
            return (
                f"CSV file not found at {csv_path}. "
                "Make sure 'data.csv' is in the app directory.",
                "",
            )

    llm = get_llm()
    schema = describe_df(df)

    # 1. Ask Gemini to write pandas code for the question
    code_response = llm.invoke(
        CODE_PROMPT_TEMPLATE.format(schema=schema, question=pergunta)
    ).content
    code = extract_code(code_response)

    # 2. Execute it; if it fails, let the model fix it once
    result = run_python_code(code, df)
    if result.startswith("Error executing code:"):
        fix_prompt = (
            "The following pandas code failed:\n```python\n" + code + "\n```\n\n"
            "Error:\n" + result + "\n\n"
            "Write corrected python code that answers the original question, "
            "outputting ONLY a ```python code block. DataFrame is `df`, pandas is `pd`."
        )
        fixed_code = extract_code(llm.invoke(fix_prompt).content)
        if fixed_code and fixed_code != code:
            code = fixed_code
        result = run_python_code(code, df)

    if result.startswith("Error"):
        return f"Could not compute an answer. {result}", code

    # 3. Turn the raw computation result into a human-readable answer
    resposta = llm.invoke(
        ANSWER_PROMPT_TEMPLATE.format(question=pergunta, result=result)
    ).content

    return resposta.strip(), code


# Quick non-interactive test entry point
if __name__ == "__main__":
    print("Testing the CSV chat pipeline...")
    if os.path.exists(CSV_FILE_PATH):
        resposta, raciocinio = gerar_resposta("How many rows and columns does the dataset have?")
        print("\n--- Answer ---")
        print(resposta)
        print("\n--- Generated Python code ---")
        print(raciocinio)
    else:
        print(f"The file {CSV_FILE_PATH} was not found. Cannot test.")
