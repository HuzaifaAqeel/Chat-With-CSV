# 📊 Chat With CSV

Ask natural-language questions about a CSV file and get real answers computed from the data.

Instead of guessing, the app uses **Google Gemini** (`gemini-2.5-flash`) to write **pandas code** for your question, executes that code against the dataset, and explains the result in plain English. The generated Python code is shown alongside every answer so you can see exactly how it was computed.

## ✨ Features

- Upload-style chat over any CSV file (`data.csv`)
- Gemini writes real pandas code that gets executed — answers are computed, not hallucinated
- Every answer includes the generated Python code (expandable in the UI)
- DataFrame preview with shape, columns, and missing-value info
- Example questions in the sidebar to get started quickly
- Free to run — uses a free Google Gemini API key, no paid APIs required

## 🧠 How it works

1. The CSV is loaded into a pandas DataFrame.
2. Gemini receives the dataset schema plus your question and writes a `print()`-based pandas snippet.
3. The snippet runs in a sandboxed namespace (`df` + `pd` only; dangerous imports blocked). If it fails, Gemini gets one automatic retry with the error message.
4. Gemini turns the raw computation output into a short, human-readable answer.

## 🛠️ Tech stack

- **Streamlit** — chat UI
- **Google Gemini 2.5 Flash** (`langchain-google-genai`) — code generation + answer formatting
- **Pandas** — data loading and computation
- **Python 3.10+**

## 🚀 Run it locally

```bash
pip install -r requirements.txt
```

Get a free Gemini API key at https://makersuite.google.com/app/apikey and set it:

```bash
export GOOGLE_API_KEY="your-key-here"
# or create a .env file containing: GOOGLE_API_KEY=your-key-here
```

Optionally override the model:

```bash
export GEMINI_MODEL="gemini-2.5-flash"
```

Then launch:

```bash
streamlit run app.py
```

The app ships with a sample `data.csv`. Replace it with your own CSV (or set a `CSV_URL` secret to load one remotely) and start asking questions.

## 💬 Example Q&A

**Q:** What is the average of the `valor` column?

**Generated code (excerpt):**

```python
print(df["valor"].mean())
```

**A:** The average value of the `valor` column is **12.0** across the dataset.

**More to try:**

- "How many rows and columns does the dataset have?"
- "Which 5 rows have the highest value in the price column?"
- "Are there any missing values in this file?"

## 📜 Credits & license

Extended and maintained by **Muhammad Huzaifa Aqeel** ([HuzaifaAqeel](https://github.com/HuzaifaAqeel)).

Original project: [Victormartinsilva/Chat_Bot_Consulta_Dados](https://github.com/Victormartinsilva/Chat_Bot_Consulta_Dados)
(Copyright © 2025 Chat Governança). Licensed under the **MIT License** — see the `LICENSE` file.
This project was extended, not built from scratch.
