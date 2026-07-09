# Personalized Networking Assistant

## 📌 Description
An AI-powered web app that generates tailored conversation starters for
networking events, fact-checks talking points against Wikipedia, and lets
you review your history of past suggestions.

## 🌟 Key Highlights
- AI-powered conversation generation using GPT-2
- Theme extraction using DistilBERT
- Real-time fact-checking with Wikipedia API
- Interactive web interface using Streamlit
- Scalable backend built with FastAPI
- Stores user interaction history using SQLite

**Stack:** FastAPI (backend) · Streamlit (frontend) · DistilBERT (theme
extraction) · GPT-2 (starter generation) · SQLite (storage) · pytest (tests)

This matches the architecture diagram: Streamlit UI → FastAPI orchestration
layer → local Transformers (DistilBERT + GPT-2) → Wikipedia fact-check → SQLite
storage of profiles and interaction logs.

---

## 1. Project structure

```
personalized-networking-assistant/
├── backend/
│   ├── main.py                  # FastAPI app + routes
│   ├── database.py               # SQLAlchemy models (SQLite)
│   ├── models/
│   │   └── schemas.py            # Pydantic request/response models
│   ├── services/
│   │   ├── nlp_service.py        # DistilBERT + GPT-2 logic
│   │   └── factcheck_service.py  # Wikipedia API integration
│   └── tests/
│       └── test_main.py          # pytest suite
├── frontend/
│   └── app.py                    # Streamlit UI
├── data/                         # SQLite DB file lives here (auto-created)
├── requirements.txt
├── pytest.ini
├── .env.example
└── README.md
```

---

## 2. Prerequisites

- Python 3.10+
- Git
- VS Code (recommended extensions: Python, Pylance)
- ~5 GB free disk space (for the transformer model downloads on first run)
- Internet connection (model downloads + Wikipedia API calls)

Check your Python version:
```bash
python3 --version
```

---

## 3. Step-by-step setup (VS Code)

### Step 1 — Open the project
Unzip the project folder and open it in VS Code:
```bash
cd personalized-networking-assistant
code .
```

### Step 2 — Create and activate a virtual environment

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

In VS Code, select this interpreter: `Cmd/Ctrl+Shift+P` → "Python: Select
Interpreter" → choose the one inside `venv`.

### Step 3 — Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
This installs FastAPI, Streamlit, Transformers, PyTorch, SQLAlchemy, etc.
PyTorch + Transformers are the largest downloads — this step can take several
minutes.

### Step 4 — Configure environment variables
```bash
cp .env.example .env
```
The defaults (SQLite, localhost backend) work out of the box — no keys are
required to run the core app, since DistilBERT/GPT-2 run locally and
Wikipedia's API is free and keyless.

### Step 5 — Run the backend (FastAPI)
Open a terminal in VS Code (`` Ctrl+` ``) from the project root:
```bash
uvicorn backend.main:app --reload --port 8000
```
- The first request that hits `/api/v1/generate` will download DistilBERT
  and GPT-2 from Hugging Face (one-time, a few hundred MB). Subsequent runs
  use the local cache.
- Verify it's running: open http://localhost:8000 — you should see
  `{"status": "ok", ...}`.
- Interactive API docs: http://localhost:8000/docs

### Step 6 — Run the frontend (Streamlit)
Open a **second** terminal (keep the backend running in the first one):
```bash
source venv/bin/activate   # or venv\Scripts\Activate.ps1 on Windows
streamlit run frontend/app.py
```
This opens the app in your browser at http://localhost:8501.

### Step 7 — Use the app
1. **✨ Generate Starters** — enter an event description (e.g. *"AI for
   Sustainable Cities"*) and your interests (e.g. *"climate change, urban
   planning"*), click **Generate Starters**.
2. **🔍 Fact Check** — search a topic (e.g. *"blockchain in healthcare"*) for
   a quick Wikipedia-sourced summary.
3. **🕓 History** — review past interactions and the 👍/👎 feedback you gave.

---

## 4. Running tests
```bash
pytest backend/tests -v
```
To skip the slower model-loading tests during quick iteration:
```bash
pytest backend/tests -v -m "not slow"
```

---

## 5. Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: backend` | Run `uvicorn` / `pytest` from the project **root**, not from inside `backend/` |
| First `/generate` call is slow / times out | Normal on first run — models are downloading. Increase timeout or just wait; subsequent calls are fast |
| `torch` install fails | Make sure you're on Python 3.10–3.12 and have the latest pip; on Apple Silicon, `pip install torch` pulls the correct build automatically |
| Streamlit can't reach backend | Confirm `uvicorn` is running on port 8000 and `API_BASE_URL` in `.env` matches |
| Port already in use | Change ports: `uvicorn backend.main:app --port 8001` and update `API_BASE_URL` accordingly |

---

## 6. Extending the project

- **Swap SQLite → PostgreSQL**: set `DATABASE_URL` in `.env` to a Postgres
  connection string; no code changes needed (SQLAlchemy handles both).
- **Swap GPT-2 for Google Gemini**: replace the body of
  `generate_conversation_starters` in `backend/services/nlp_service.py` with
  a call to the Gemini API using `GOOGLE_GEMINI_API_KEY` from `.env`.
- **Deploy**: containerize `backend/` and `frontend/` separately (two
  Dockerfiles + docker-compose), or deploy the backend to a service like
  Render/Railway and the Streamlit app to Streamlit Community Cloud.

---

## 7. Mapping back to the architecture diagram

| Diagram component | Implementation |
|---|---|
| Streamlit Web Application | `frontend/app.py` |
| FastAPI Backend Service (API Endpoints + Orchestration) | `backend/main.py` |
| DistilBERT Zero-Shot Classification | `nlp_service.extract_themes` |
| GPT-2 Text Generation | `nlp_service.generate_conversation_starters` |
| Fact Verification Module + Wikipedia Search API | `factcheck_service.fact_check` |
| Local Data Store (User Profiles, Interaction Logs) | `database.py` (SQLite) |

## 👤 Author

**Latha**  
GitHub: https://github.com/Latha-44  

Passionate about building AI-driven applications and exploring modern web technologies.Focused on developing scalable solutions using Python, FastAPI, and machine learning models.