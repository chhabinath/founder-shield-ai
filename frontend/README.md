# FounderShield AI — Frontend (React + Vite + TypeScript)

Phase 01 foundation: responsive app shell, landing screen with a
**Start Interview** action, reusable loading / error / empty states, and a
typed API client. No secrets live in browser code.

## Setup

```bash
cd frontend
npm install
```

Create `.env` with the public API base URL (see repo-root `.env.example`):

```
VITE_API_BASE_URL=http://localhost:8000
```

## Run

```bash
npm run dev        # http://localhost:5173
```

## Quality gates

```bash
npm run typecheck  # tsc --noEmit
npm run test       # vitest
npm run build      # production build
```
