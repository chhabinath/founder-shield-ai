# FounderShield AI — Backend (FastAPI)

Phase 01 foundation: validated config, health endpoint, redacting
structured logging, explicit CORS allowlist, and a consistent error
envelope. No external AI/voice integration yet.

## Setup

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -e ".[dev]"
```

Copy the environment template (placeholders only) from the repo root:

```bash
cp ../.env.example .env   # Windows: copy ..\.env.example .env
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
# Health check:
curl http://localhost:8000/health
```

## Quality gates

```bash
pytest -q          # tests
ruff check .       # lint
mypy app           # type check
```

## Layout

```
app/
  main.py        # app factory + CORS + routers + error handlers
  config.py      # validated pydantic-settings
  logging.py     # JSON logging + redaction filter
  errors.py      # consistent error envelope
  api/           # routers (health; more in later phases)
  schemas/       # pydantic response models
  services/      # interview/privacy/reasoning/voice (later phases)
tests/           # pytest suite
```
