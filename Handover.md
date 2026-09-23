# Handover — Component C (Web Application)

**Project:** Emotion-Aware Conversational AI Using Facial Recognition
**Component:** C — Web application (front-end + back-end), owned by Hanspreet Jassi
**Status as of this handover:** M1 skeleton loop complete — full conversational loop working end-to-end against mocks for A, B and D
**Last verified:** Docker Compose stack up, guest session flow debugged and fixed (see "Known issues" below)

---

## 1. What this project is

A hands-free, emotion-aware conversational web app. The user speaks into a webcam-equipped browser; the system transcribes speech, detects facial emotion, feeds both into a local LLM whose reply is tonally conditioned on the detected emotion, then speaks the reply back. Four components, four owners, one contract:

| ID | Component | Owner | Port |
| --- | --- | --- | --- |
| A | Facial recognition & emotion profiling | Abhinav Nara | 8101 |
| B | Speech interface (STT + TTS) | Sahib Singh Edhen | 8102 |
| **C** | **Web application (this component)** | **Hanspreet Jassi** | **8000 / 5173** |
| D | Language model integration | Anant Srivastava | 8103 |

Component C is the **only orchestrator**. A, B and D are stateless, never call each other, never touch the database, and are fully swappable behind mocks — which is what let C be built to completion before any of the ML components exist.

Full context lives in two source documents (not reproduced here): the **Synopsis** (project rationale, scope, requirements) and the **Component Design Document** (the frozen technical contract — Sections 4–5 define the data types and APIs everyone else's code depends on).

---

## 2. Repo layout

```
emotion-ai/
  contracts/            Frozen shared types (Section 4) — Pydantic models every service imports
  mocks/                 Stub servers for A (8101), B (8102), D (8103)
  app/
    backend/             Component C backend — FastAPI, port 8000
    frontend/             Component C frontend — React + Vite + TS, port 5173
  tests/contract/         Contract tests for A, B, C, D
  docker-compose.yml      Brings up everything: mysql, redis, mock-a/b/d, backend, frontend
  .env.example
  README.md               Full run instructions (see also Section 6 below)
```

Everything crosses an HTTP or WebSocket boundary — nothing imports another component's Python code directly, even running on one machine. `contracts/` is the only thing all four services share.

---

## 3. What's implemented in Component C

**Backend (`app/backend/`)**

- `main.py` — FastAPI app. Verifies `CONTRACT_VERSION` against A/B/D on startup and **refuses to boot on a mismatch**. Populates `model_registry` from A and D's `/v1/model/info`. Seeds the `role` table.
- `ws.py` — the `/api/converse` WebSocket: the one place all four components meet. Per turn: accepts audio/video, dispatches to A and B concurrently, pushes `emotion_update` live, calls D with the current `EmotionState` + history window on final transcript, streams the reply, sends it to B for synthesis, persists the turn — all skipped for guest principals.
- `auth.py` — JWT access/refresh tokens, bcrypt password hashing, guest tokens (no DB row), role-gated dependency injection for admin routes.
- `models.py` — the 8-table schema from the ER diagram (`role`, `user`, `chat_session`, `message`, `emotion_record`, `emotion_class`, `model_registry`, `feedback`), with FK-based emotion storage and model-version provenance on every row that needs it.
- `downstream.py` — single pooled `httpx.AsyncClient` for all calls to A/B/D.
- `routers/` — `auth_router.py` (register/login/refresh/guest), `sessions_router.py` (history, timeline, deletion — cascades correctly), `admin_router.py` (user management, live service health, analytics, instruction-map viewer).
- `alembic/` — scaffolded but not yet generating real migrations; the app currently uses `Base.metadata.create_all()` on startup for local dev speed. **See open items.**

**Frontend (`app/frontend/`)**

- `pages/ConversationView.tsx` — the primary screen: connect, enable camera, start speaking, live emotion badge, streaming chat.
- `pages/SessionHistory.tsx` — session list + Chart.js emotion timeline + transcript + delete.
- `pages/AdminDashboard.tsx` — service health (flags `mock: true`), gating rate, user list, session browser, instruction map.
- `pages/LoginPage.tsx` — register/login/guest, with error surfacing on the guest flow.
- `hooks/useConverseSocket.ts` — owns the WS connection, media capture (canvas-drawn JPEG frames, PCM16 audio), and all client-side state derived from it.
- `api/types.ts` — hand-mirrored TS counterparts of `contracts/types.py`. **Should eventually be generated from the backend's OpenAPI schema** (`npm run gen:types`) rather than hand-maintained.

**Mocks (`mocks/`)** — one FastAPI stub per component (A/B/D), each sleeping for its real latency budget and reporting `mock: true` on `/healthz`, per Section 11 of the design doc. These are what let C be built without waiting on anyone.

**Tests (`tests/contract/`)** — validate every component's responses against `contracts/types.py`, including a test that confidence gating correctly falls back to neutral when `EmotionState.fallback` is true or confidence is below threshold.

---

## 4. Known issues hit during setup, and their fixes

These were all found and fixed while getting the Docker stack running end-to-end — worth reading before you hit them again on a fresh machine.

| Issue | Symptom | Fix |
| --- | --- | --- |
| MySQL 8 auth plugin | Backend crash-loops with `RuntimeError: 'cryptography' package is required for sha256_password or caching_sha2_password auth methods` | Added `cryptography==43.0.1` to `requirements.txt` (`pymysql` needs it for MySQL 8's default `caching_sha2_password` auth) |
| passlib/bcrypt version mismatch | Would surface as a crash on first password hash (register/login) — `passlib` 1.7.4's backend version-detection breaks on `bcrypt` ≥ 4.1 | Pinned `bcrypt==4.0.1` alongside `passlib[bcrypt]==1.7.4` in `requirements.txt` |
| **Vite proxy target hardcoded to `localhost`** | Guest session (and any `/api/*` call) silently fails from inside Docker — request never reaches the backend, nothing appears in backend logs at all | `vite.config.ts` now reads `process.env.VITE_BACKEND_URL`, falling back to `localhost:8000` for non-Docker dev. `docker-compose.yml`'s `frontend` service now sets `VITE_BACKEND_URL: http://backend:8000` (Docker service name, not `localhost` — `localhost` inside a container means the container itself) |
| Guest button had no error handling | Failures were invisible / generic | `LoginPage.tsx`'s guest handler now catches and distinguishes a network-level failure ("can't reach the backend") from a backend-returned error |

**Diagnostic method that found the Vite bug**, worth reusing for future "something's silently not working" bugs: check `docker compose logs backend` right after triggering the action. If the relevant request **never appears in the backend's access log at all**, the request isn't reaching the backend — look at the network path (proxy config, container networking, CORS), not the backend code.

**Rebuild discipline:** `docker compose up --build` rebuilds everything, but if you only need to pick up a change to one service, `docker compose build <service> && docker compose up` is faster and avoids confusion about which container is running which code. The Vite bug above took an extra round because the backend was rebuilt (for the bcrypt fix) but not the frontend (which actually had the proxy fix).

---

## 5. Deliberately left open — next steps

- **Alembic migrations.** Scaffold exists in `app/backend/alembic/`; no revision has been generated yet. Run `alembic revision --autogenerate -m "initial schema"` once MySQL is reachable, then `alembic upgrade head`, and switch `main.py` off `Base.metadata.create_all()`.
- **Per-turn latency persistence.** `/api/admin/analytics` currently returns a placeholder for `turn_latency_ms` (p50/p95). The WS loop already emits a `turn_timing` event per turn — it needs a table to land in so the admin view can compute real percentiles (Section 10 of the design doc says C owns this measurement).
- **D's WebSocket streaming.** The current loop calls D's REST `/v1/generate` and fakes token-by-token deltas by splitting the full response client-side. Functionally correct, not latency-optimal. Swap to D's `/v1/generate/stream` WS once D exists for real token streaming.
- **Proper audio resampling.** `useConverseSocket.ts` uses `AudioContext({ sampleRate: 16000 })` as a shortcut instead of the `AudioWorklet`-based 48→16kHz resampler specified in Section 8.1. Works for the mock loop; revisit before relying on it for real STT accuracy.
- **Generated TS types.** `src/api/types.ts` is hand-mirrored from `contracts/types.py`. Run `npm run gen:types` (wired to `openapi-typescript`) once the backend's OpenAPI schema stabilizes, and delete the hand-maintained version — hand-maintained duplicate types drift.
- **Admin UI polish.** Model-registry table view and session-browser filtering are stubbed but minimal.

---

## 6. Running it

**Docker (recommended):**
```bash
cp .env.example .env        # set a real JWT_SECRET
docker compose up --build
```
Frontend: `http://localhost:5173` · Backend health: `http://localhost:8000/healthz` · Mocks: `:8101` / `:8102` / `:8103`

**Rebuilding a single service after a code change:**
```bash
docker compose build <backend|frontend|mock-a|mock-b|mock-d>
docker compose up
```

**Without Docker:** see `README.md` at the repo root — backend + three mocks run via `uvicorn`, frontend via `npm run dev`, with an option to point `DATABASE_URL` at SQLite for a quick spike without standing up MySQL.

**Swapping in a real A, B or D** once built: edit `USE_MOCKS` in `.env` (e.g. `USE_MOCKS=b,d` once A is real) and point the corresponding `*_SERVICE_URL` at wherever it runs. C refuses to boot on a `CONTRACT_VERSION` mismatch — that's intentional, not a bug.

---

## 7. Integration milestones (from the design doc, Section 12)

| Milestone | Status |
| --- | --- |
| M0 — contracts frozen | ✅ `contracts/types.py` in place |
| **M1 — skeleton loop (C vs. three mocks)** | **✅ Done — this handover's deliverable** |
| M2 — real A | ⏳ waiting on Abhinav |
| M3 — real B | ⏳ waiting on Sahib |
| M4 — real D | ⏳ waiting on Anant |
| M5 — all real | ⏳ |
| M6 — tuned | ⏳ |

At each swap: run the contract tests against the real service before wiring it in, swap via `USE_MOCKS` (never by editing code), record per-stage timings, and tag the commit (`m2-real-a`, etc.) so there's always a working build to fall back to.

---

## 8. Contacts / ownership

Questions about `contracts/types.py` or the WebSocket protocol require agreement from all four owners before changing (see the design doc's change protocol, Section 1) — never change a contract silently. Everything else under `app/` and `mocks/` for A, B, D belongs to its respective owner; everything under `app/` for C is this component's territory.