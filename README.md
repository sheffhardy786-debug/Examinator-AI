# Examinator AI — Adaptive Viva Prototype

A Streamlit prototype for an adaptive AI-powered learning and viva examination system.

## Features
- Student, subject, topic and starting difficulty setup
- Viva question generation
- Answer submission and scoring
- Feedback, strengths, improvements and suggested answers
- Adaptive difficulty: 8–10 increases, 5–7 maintains, 0–4 decreases
- Final performance report and JSON export
- Built-in demo mode so the app can run without an API key

## Run locally

1. Install Python 3.10 or newer.
2. Extract this folder and open a terminal inside it.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the app:

   ```bash
   streamlit run app.py
   ```

5. Open the local URL shown in the terminal (usually http://localhost:8501).

## Enable Gemini AI

Set an API key in your environment before starting Streamlit.

**Windows PowerShell**
```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
streamlit run app.py
```

**macOS/Linux**
```bash
export GEMINI_API_KEY="YOUR_API_KEY"
streamlit run app.py
```

Optional model override:
```bash
export GEMINI_MODEL="gemini-2.5-flash"
```

For Streamlit Community Cloud, add `GEMINI_API_KEY` under App settings → Secrets:

```toml
GEMINI_API_KEY = "YOUR_API_KEY"
```

Never commit API keys or passwords to GitHub. Add `.streamlit/secrets.toml` to `.gitignore` if you use it locally.

## Important evaluation note
Without a Gemini key, the app uses a built-in question bank and a simple keyword-overlap scoring heuristic. This is a usable demonstration fallback, but it is not semantic AI evaluation. For your report, distinguish actual Gemini runs from demo-mode runs and record genuine test outputs.

## Suggested demo test cases
1. Correct, detailed answer
2. Partially correct answer
3. Very short answer
4. "I don't know"
5. Empty answer (must be blocked)
6. Strong answer followed by harder question
7. Weak answer followed by easier question
8. Different subject and topic
9. Three-question short viva
10. Full five-question viva and report export
