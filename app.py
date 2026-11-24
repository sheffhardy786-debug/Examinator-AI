import os
import json
import re
import random
import requests
import streamlit as st

st.set_page_config(page_title="Examinator AI | Adaptive Viva", page_icon="🎓", layout="wide")

# -------------------- AI provider --------------------
def gemini_generate(prompt: str):
    """Call Gemini REST API when an API key is configured; otherwise return None."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    # No API key configured: use demo mode
    if not api_key:
        return None, "No Gemini API key configured. Using built-in demo mode."
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}],
               "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1200}}
    try:
        response = requests.post(url, json=payload, timeout=35)
        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text, "Gemini API connected."
    except Exception as exc:
        return None, f"Gemini request failed; using demo mode. Details: {exc}"

def extract_json(text):
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None

# -------------------- Demo-mode question bank --------------------
BANK = {
    "computer science": {
        "easy": [
            ("What is an algorithm? Give one simple example.", ["step", "instruction", "procedure", "solve"]),
            ("What is the difference between RAM and ROM?", ["volatile", "temporary", "permanent", "memory"]),
            ("What is a variable in programming?", ["store", "value", "data", "memory"]),
        ],
        "medium": [
            ("Explain the difference between a stack and a queue.", ["lifo", "fifo", "last in", "first in", "order"]),
            ("What is time complexity, and why is Big-O notation useful?", ["input", "growth", "upper bound", "complexity", "performance"]),
            ("What is the purpose of normalization in a database?", ["redundancy", "duplicate", "dependency", "table"]),
        ],
        "hard": [
            ("Compare process-level and thread-level concurrency, including one synchronization risk.", ["process", "thread", "shared", "race", "synchronization"]),
            ("Explain how an index can improve database queries and identify one trade-off.", ["search", "lookup", "write", "storage", "overhead"]),
            ("How would you diagnose and reduce latency in a distributed application?", ["measure", "network", "bottleneck", "cache", "profil"]),
        ],
    },
    "artificial intelligence": {
        "easy": [
            ("What is artificial intelligence? Give one everyday example.", ["machine", "intelligent", "task", "learn", "decision"]),
            ("What is the difference between AI and machine learning?", ["subset", "learn", "data", "artificial intelligence"]),
            ("What is a dataset in machine learning?", ["data", "example", "training", "record"]),
        ],
        "medium": [
            ("Explain overfitting and give two ways to reduce it.", ["training", "general", "unseen", "regularization", "validation", "dropout"]),
            ("What is the difference between supervised and unsupervised learning?", ["label", "unlabel", "target", "cluster"]),
            ("Why do we split data into training and testing sets?", ["unseen", "evaluate", "generalization", "train", "test"]),
        ],
        "hard": [
            ("Explain the precision-recall trade-off and when recall matters more.", ["false negative", "precision", "recall", "threshold", "positive"]),
            ("How can data leakage produce misleading model evaluation results?", ["training", "test", "information", "leak", "evaluation"]),
            ("Compare a transformer attention mechanism with a recurrent sequence model.", ["attention", "context", "sequence", "parallel", "recurrent"]),
        ],
    },
    "general": {
        "easy": [
            ("Explain the main idea of this topic in your own words.", ["explain", "concept", "idea"]),
            ("Can you define the key term and give an example?", ["define", "example", "meaning"]),
            ("Why is this topic useful in practice?", ["use", "application", "practical", "benefit"]),
        ],
        "medium": [
            ("Compare two important concepts from this topic.", ["compare", "difference", "similar", "whereas"]),
            ("Explain how this concept works step by step.", ["step", "process", "because", "works"]),
            ("Give a real-world application and explain why it is suitable.", ["application", "example", "reason", "suitable"]),
        ],
        "hard": [
            ("Evaluate a limitation of this approach and propose an improvement.", ["limitation", "weakness", "improve", "trade-off"]),
            ("What would happen if one key assumption were changed? Justify your answer.", ["assumption", "impact", "because", "therefore"]),
            ("Design a solution to a practical problem using this concept and defend your choices.", ["design", "solution", "choice", "justify"]),
        ],
    }
}

def local_question(subject, topic, level, asked):
    key = subject.lower()
    category = "computer science" if any(x in key for x in ["computer", "cse", "program"]) else \
               "artificial intelligence" if any(x in key for x in ["ai", "artificial", "machine learning"]) else "general"
    choices = BANK[category][level]
    available = [q for q in choices if q[0] not in asked]
    if not available:
        available = choices
    q, keywords = random.choice(available)
    if topic.strip():
        q = q.replace("this topic", topic).replace("this concept", topic)
        if category == "general" and topic.lower() not in q.lower():
            q = f"Regarding {topic}: {q}"
    return {"question": q, "expected_points": keywords, "level": level}

def make_question(subject, topic, level, asked):
    prompt = f"""You are a fair university viva examiner. Create ONE clear oral-exam question.
Subject: {subject}
Topic: {topic}
Difficulty: {level}
Questions already asked: {asked}
Return only valid JSON with keys question (string) and expected_points (array of 4-6 short strings).
Avoid repeating previous questions. Keep it appropriate for an undergraduate student."""
    result, status = gemini_generate(prompt)
    parsed = extract_json(result) if result else None
    if parsed and parsed.get("question"):
        return {"question": parsed["question"], "expected_points": parsed.get("expected_points", []), "level": level}, status
    return local_question(subject, topic, level, asked), status

def evaluate_answer(question, answer, expected, level):
    prompt = f"""Act as a fair, constructive university viva examiner.
Question: {question}
Student answer: {answer}
Expected concepts: {expected}
Difficulty: {level}
Evaluate only what the student actually said. Do not invent claims.
Return only valid JSON:
{{"score": integer 0-10, "feedback": "2-4 sentences", "strengths": ["..."], "improvements": ["..."], "ideal_answer": "concise model answer"}}
Award partial credit for relevant understanding. If answer is empty or says only "I don't know", score 0."""
    result, status = gemini_generate(prompt)
    parsed = extract_json(result) if result else None
    if parsed and isinstance(parsed.get("score"), (int, float)):
        parsed["score"] = max(0, min(10, int(parsed["score"])))
        return parsed, status
    # Transparent local fallback: a simple keyword-overlap heuristic, not a semantic AI evaluation.
    words = set(re.findall(r"[a-zA-Z]+", answer.lower()))
    hits = [p for p in expected if any(w in words for w in re.findall(r"[a-zA-Z]+", p.lower()))]
    score = round(10 * len(hits) / max(1, len(expected)))
    if len(answer.strip()) < 8:
        score = 0
    feedback = ("Your answer includes some relevant concepts. Add clearer explanation and an example."
                if score >= 4 else "Your answer needs more relevant concepts and a clearer explanation. Review the topic and try to explain it in your own words.")
    if not answer.strip() or answer.strip().lower() in ["idk", "i don't know", "dont know"]:
        feedback = "No assessable explanation was provided. Review the topic and try again."
    return {"score": score, "feedback": feedback,
            "strengths": hits[:3] or ["Attempted the question"],
            "improvements": [p for p in expected if p not in hits][:4],
            "ideal_answer": "A complete answer should address: " + ", ".join(expected) + "."}, status

# -------------------- Session state --------------------
defaults = {"started": False, "history": [], "current": None, "asked": [], "difficulty": "easy",
            "completed": False, "api_status": "Not checked"}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------- Styling --------------------
st.markdown("""
<style>
.block-container {padding-top: 1.6rem; max-width: 1100px;}
.hero {padding: 1.4rem 1.6rem; border-radius: 18px; background: linear-gradient(120deg,#172554,#312e81); color: white; margin-bottom: 1rem;}
.hero p {color:#dbeafe; margin-bottom:0;}
.metric-card {padding:1rem; border:1px solid #33415533; border-radius:14px;}
.small-muted {color:#64748b; font-size:.9rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🎓 Examinator AI</h1><p>Adaptive AI-powered learning and viva examination system</p></div>', unsafe_allow_html=True)
st.caption("Prototype build • Adaptive question difficulty • Answer evaluation • Feedback and performance report")

with st.sidebar:
    st.header("⚙️ Viva Configuration")
    student = st.text_input("Student name", value="Student")
    subject = st.text_input("Subject", value="Artificial Intelligence")
    topic = st.text_input("Viva topic", value="Machine Learning")
    initial = st.selectbox("Starting difficulty", ["easy", "medium", "hard"], index=0)
    total_questions = st.slider("Number of questions", 3, 10, 5)
    st.divider()
    st.markdown("**AI connection**")
    api_key_present = bool(os.getenv("GEMINI_API_KEY", "").strip())
    st.write("Gemini API: " + ("Configured" if api_key_present else "Demo mode (no API key)"))
    st.caption("For live Gemini evaluation, set GEMINI_API_KEY as an environment variable or Streamlit secret.")
    if st.button("Reset viva", use_container_width=True):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Questions", len(st.session_state.history), f"of {total_questions}")
with col2:
    avg = round(sum(x["score"] for x in st.session_state.history) / len(st.session_state.history), 1) if st.session_state.history else 0
    st.metric("Average score", f"{avg}/10")
with col3:
    st.metric("Current level", st.session_state.difficulty.title())

if not st.session_state.started:
    st.subheader("Start your viva")
    st.write("Configure your subject, topic and difficulty in the sidebar, then begin your examination.")
    st.info("The prototype works immediately in demo mode. Add a Gemini API key to enable AI-generated questions and model-based answer evaluation.")
    if st.button("🚀 Start Viva Examination", type="primary", use_container_width=True):
        st.session_state.difficulty = initial
        q, status = make_question(subject, topic, st.session_state.difficulty, st.session_state.asked)
        st.session_state.api_status = status
        st.session_state.current = q
        st.session_state.asked.append(q["question"])
        st.session_state.started = True
        st.rerun()

elif st.session_state.completed:
    st.success("Viva examination completed!")
    st.subheader(f"Final report — {student}")
    st.metric("Final score", f"{sum(x['score'] for x in st.session_state.history)}/{len(st.session_state.history)*10}")
    st.metric("Average", f"{avg}/10")
    if avg >= 8:
        verdict = "Excellent understanding"
    elif avg >= 6:
        verdict = "Good understanding"
    elif avg >= 4:
        verdict = "Developing understanding"
    else:
        verdict = "Needs more practice"
    st.markdown(f"### Overall assessment: {verdict}")
    for i, item in enumerate(st.session_state.history, 1):
        with st.expander(f"Q{i}. {item['question']} — {item['score']}/10"):
            st.write("**Your answer:**", item["answer"])
            st.write("**Feedback:**", item["feedback"])
            st.write("**Suggested answer:**", item["ideal_answer"])
    st.download_button("Download report (JSON)", json.dumps({
        "student": student, "subject": subject, "topic": topic, "average_score": avg,
        "verdict": verdict, "history": st.session_state.history
    }, indent=2), file_name="examinator_viva_report.json", mime="application/json")
    if st.button("Start a new viva", type="primary"):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()

else:
    progress = len(st.session_state.history) / total_questions
    st.progress(progress, text=f"Question {len(st.session_state.history)+1} of {total_questions}")
    q = st.session_state.current
    st.subheader("Live Viva Examination")
    st.markdown(f"**Subject:** {subject}  ·  **Topic:** {topic}")
    st.markdown(f"**Difficulty:** `{q['level'].title()}`")
    st.markdown(f"### Question {len(st.session_state.history)+1}")
    st.markdown(f"## {q['question']}")
    with st.form("answer_form", clear_on_submit=False):
        answer = st.text_area("Your answer", height=170, placeholder="Type your answer here. Explain the concept in your own words...")
        submitted = st.form_submit_button("Submit Answer", type="primary", use_container_width=True)
    if submitted:
        if not answer.strip():
            st.warning("Please enter an answer before submitting.")
        else:
            evaluation, status = evaluate_answer(q["question"], answer, q["expected_points"], q["level"])
            st.session_state.api_status = status
            record = {"question": q["question"], "level": q["level"], "answer": answer,
                      "score": evaluation["score"], "feedback": evaluation["feedback"],
                      "strengths": evaluation.get("strengths", []),
                      "improvements": evaluation.get("improvements", []),
                      "ideal_answer": evaluation.get("ideal_answer", "")}
            st.session_state.history.append(record)
            st.session_state.last_evaluation = evaluation
            st.session_state.awaiting_next = True
            st.rerun()

    if st.session_state.get("awaiting_next", False):
        result = st.session_state.last_evaluation
        latest = st.session_state.history[-1]
        st.divider()
        st.subheader("Examiner feedback")
        st.metric("Your score", f"{latest['score']}/10")
        st.write(latest["feedback"])
        a, b = st.columns(2)
        with a:
            st.markdown("**What you covered well**")
            for x in latest["strengths"]:
                st.write("• " + str(x))
        with b:
            st.markdown("**Areas to improve**")
            for x in latest["improvements"]:
                st.write("• " + str(x))
        with st.expander("View a suggested answer"):
            st.write(latest["ideal_answer"])
        # Adaptive policy: >=8 moves up, <=4 moves down, otherwise stays.
        levels = ["easy", "medium", "hard"]
        idx = levels.index(st.session_state.difficulty)
        if latest["score"] >= 8:
            new_idx = min(2, idx + 1)
            reason = "Strong answer: increasing difficulty where possible."
        elif latest["score"] <= 4:
            new_idx = max(0, idx - 1)
            reason = "More support needed: reducing difficulty where possible."
        else:
            new_idx = idx
            reason = "Developing answer: keeping the current difficulty."
        st.session_state.next_difficulty = levels[new_idx]
        st.info(f"Adaptive engine: {reason}")
        if st.button("Next Question →", type="primary", use_container_width=True):
            st.session_state.difficulty = st.session_state.next_difficulty
            st.session_state.awaiting_next = False
            if len(st.session_state.history) >= total_questions:
                st.session_state.completed = True
            else:
                next_q, status = make_question(subject, topic, st.session_state.difficulty, st.session_state.asked)
                st.session_state.api_status = status
                st.session_state.current = next_q
                st.session_state.asked.append(next_q["question"])
            st.rerun()

with st.expander("About this prototype / evaluation notes"):
    st.write("This prototype demonstrates the end-to-end viva flow. With a Gemini API key, question generation and evaluation use the configured model. Without a key, a built-in question bank and transparent keyword-overlap scoring keep the demo usable. Demo-mode scoring is a basic heuristic and should not be presented as semantic AI evaluation.")
    st.write("Adaptive rule: score 8–10 → increase difficulty; 5–7 → maintain; 0–4 → decrease difficulty.")
    st.caption("API status: " + st.session_state.api_status)
