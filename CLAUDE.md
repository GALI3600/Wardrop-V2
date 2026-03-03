# Wardrop V2 — Development Rules

## Git Workflow

- Branch `main` is production. Never push directly to main.
- All development happens on `dev` or feature branches off `dev`.
- For each change, create a feature branch off `dev` (e.g., `fix/ml-url-normalizer`, `feat/dark-mode`). Push the branch, open a PR to `dev`, and merge it.
- Commit and push after every meaningful change that adds value (new feature, bug fix, refactor, etc.). Don't accumulate large uncommitted diffs.
- Write concise commit messages in English describing the "why", not the "what".
- Never amend or force-push commits that are already pushed.

## Project Structure

- `backend/` — FastAPI + SQLAlchemy + Alembic (Python 3.12)
- `web/` — Next.js frontend (TypeScript)
- `extension/` — Chrome extension (vanilla JS)
- `docker-compose.yml` — PostgreSQL, backend, and web services

## Backend

- Run via `docker compose up -d` or `make backend` for local dev.
- Database migrations via Alembic: `make migrate`
- Tests: `make test`
- LLM provider is configurable (Groq by default). Config in `backend/app/config.py`, keys in `backend/.env`.
- Never commit `.env` files.

## Extension

- After code changes, reload in `chrome://extensions`.
- Extension works in hybrid mode: local storage (offline) + backend API (when logged in).
- Content scripts: `extractor.js` (detects products), `ui.js` (track button).

## Language

- Code, comments, and commits in English.
- User-facing strings (extension, web) in Portuguese (pt-BR).
