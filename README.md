# FounderShield AI

Privacy-first voice interviewer that turns vague operational problems into
structured, evidence-backed, build-ready problem briefs.

See `docs/` for the product requirements, architecture, API contracts,
security model, and phased implementation plan.

## Monorepo layout

```
backend/    FastAPI service (Python)
frontend/   React + Vite + TypeScript app
docs/       Phase 00 planning documents
.env.example  Environment template (placeholders only)
```

## Quick start

```bash
# Backend
cd backend && python -m venv .venv
#   Windows: .venv\Scripts\activate   |  Unix: source .venv/bin/activate
pip install -e ".[dev]" && uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

Phase 01 provides a runnable foundation only. External AI/voice
integrations arrive in later phases and default to mock mode.
