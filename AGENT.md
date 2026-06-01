# AGENT.md

## Core Tech Stack & Expected Package Manager

- This is an AI-powered SAT tutoring and SAT practice tool, not a generic chatbot.
- Frontend: React 19 + Vite 7, JavaScript/JSX, MUI, Supabase client auth, KaTeX/Markdown rendering.
- Backend: FastAPI modular monolith in `PythonBackend/app`, PostgreSQL, pgvector, Supabase auth verification, OpenAI-powered SAT tutor agents, WolframAlpha math tooling.
- Package manager: use `npm` in `AI Tutor/`; `package-lock.json` is authoritative. Do not introduce Yarn, pnpm, or Bun.
- Python deps are pinned in `PythonBackend/requirements.txt`; use a virtualenv and `pip install -r requirements.txt`.

## Build, Test, and Lint Commands

- Frontend dev: `cd "AI Tutor" && npm run dev`
- Frontend build: `cd "AI Tutor" && npm run build`
- Frontend lint: `cd "AI Tutor" && npm run lint`
- Frontend preview: `cd "AI Tutor" && npm run preview`
- Backend install: `cd PythonBackend && pip install -r requirements.txt`
- Backend dev: `cd PythonBackend && uvicorn app.main:app --reload`
- Backend tests: no formal test runner is configured; do not invent one without adding config intentionally.

## Strict Coding Conventions

- Keep SAT domain logic, scoring, adaptive exam behavior, tutor reasoning, prompt engineering, and persistence rules in the backend.
- Keep React components presentation-focused: rendering, navigation, local interaction state, loading/error states, and API calls through `src/services`.
- Use `src/services/apiClient.js` and service modules for frontend HTTP calls; do not scatter raw `fetch` calls through pages/components.
- Prefer explicit, readable service functions over clever abstractions. Split large React components and deeply nested backend functions before adding framework-level complexity.
- Backend route modules should validate/route only; business logic belongs in services/tutor/SAT modules, not route handlers.
- Preserve Supabase token verification on the backend and local Postgres user synchronization.

## Specific Landmines / Anti-Patterns

- Do not convert this project into microservices; the intended architecture is a modular monolith.
- Do not move grading, adaptive module selection, survival mode validation, tutor orchestration, or prompt logic into the frontend.
- Do not bypass `apiRequest`, duplicate auth header handling, or hardcode backend URLs outside the existing env-based client.
- Do not replace PostgreSQL/pgvector with NoSQL or a separate vector store unless explicitly requested.
- Do not remove backend auth verification because Supabase auth also exists in the frontend.
- Do not introduce broad global frontend state for page-local UI behavior.
- Do not add unnecessary frameworks, event buses, queues, or enterprise patterns for straightforward SAT tutoring workflows.
