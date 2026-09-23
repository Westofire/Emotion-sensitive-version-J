# Emotion-Aware Conversational AI — Component C (Web Application)

This is the monorepo skeleton from the Component Design Document (Section 3),
with **Component C fully implemented** against **mocks for A, B and D**.
Components A, B and D themselves are stubbed under `mocks/` per Section 11
and are not implemented here — that's Abhinav's, Sahib's, and Anant's work.

## What's here

```
contracts/          Frozen shared types (Section 4) — do not edit without the change protocol
mocks/               Stub servers for A (8101), B (8102), D (8103) — Section 11
app/backend/         Component C backend — FastAPI, port 8000
app/frontend/        Component C frontend — React + Vite + TS, port 5173
tests/contract/      Contract tests for A, B, C, D — run against mocks or the real services
docker-compose.yml   Brings up everything: mysql, redis, mock-a/b/d, backend, frontend
```

## Quickest path: run everything with Docker

```bash
cp .env.example .env      # edit JWT_SECRET at minimum
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend:  http://localhost:8000/healthz
- Mocks:    :8101 (A), :8102 (B), :8103 (D) — each reports `mock: true` on /healthz

## Running locally without Docker

Backend + mocks (from the repo root, one venv):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# start MySQL + Redis yourself, or point DATABASE_URL at SQLite for a quick spike

# three mock services
uvicorn mocks.emotion_mock:app --port 8101 --reload &
uvicorn mocks.speech_mock:app --port 8102 --reload &
uvicorn mocks.llm_mock:app --port 8103 --reload &

# Component C backend
uvicorn app.backend.main:app --port 8000 --reload
```

Frontend:

```bash
cd app/frontend
npm install
npm run dev
```

## Database migrations

The backend auto-creates tables on startup for local development
(`Base.metadata.create_all`) so you can start hacking immediately. Before
anything resembling a real deployment, switch to Alembic, which is already
scaffolded:

```bash
cd app/backend
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

Never hand-edit a live schema (Section 8.4) — always go through a migration.

## Swapping in a real A, B or D

Don't edit code — flip `USE_MOCKS` in `.env` (Section 11):

```
USE_MOCKS=b,d   # A is now real; B and D still mocked
```

and point `EMOTION_SERVICE_URL` at wherever the real service runs. C refuses
to boot if any downstream service reports a different `CONTRACT_VERSION`
(Section 3) — that's a deliberate loud failure, not a bug.

## What's implemented vs. still open

Implemented (M1 skeleton loop + most of Section 8's acceptance criteria):

- [x] Full conversational loop end-to-end against all three mocks (`/api/converse`)
- [x] Registration, login, refresh, guest tokens, role-gated admin routes
- [x] Guest sessions write nothing to the database (enforced in `ws.py` and `sessions_router.py`, tested in `test_c.py`)
- [x] Camera/mic permission denial degrades to text-only rather than breaking
- [x] Emotion timeline renders from persisted `emotion_record` rows
- [x] Contract tests for A, B, C, D against the mocks

Deliberately left for you to extend next:

- [ ] Alembic migration files (scaffold is in place; generate the first `revision --autogenerate` once MySQL is reachable)
- [ ] Per-turn latency persisted to a table so `/api/admin/analytics` reports real p50/p95 instead of a placeholder (Section 10 says C owns this measurement)
- [ ] Swap the REST call to D for its `/v1/generate/stream` WebSocket for real token-level streaming (the current loop fakes deltas by splitting D's REST response — functionally correct, not latency-optimal)
- [ ] Replace the `AudioContext({ sampleRate: 16000 })` shortcut in `useConverseSocket.ts` with a proper `AudioWorklet` resampler per Section 8.1
- [ ] Generate `src/api/generated.ts` from the backend's OpenAPI schema (`npm run gen:types`) once the schema stabilises, and retire the hand-mirrored `src/api/types.ts`
- [ ] Admin UI polish: model-registry table view, session browser filters

Ask me for any of these next and I'll build it against this same skeleton.
