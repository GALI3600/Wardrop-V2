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

## Docker & Ports

**CRITICAL RULES:**
1. **ALWAYS use `docker-compose.prod.yml`** — never use the default `docker-compose.yml` on this server
2. **NEVER change the port mappings** — they are configured in Cloudflare Tunnel and must stay as-is

**Reserved ports for Wardrop (DO NOT CHANGE):**
| Service | External Port | Internal Port | Domain |
|---------|---------------|---------------|--------|
| web | 3001 | 3000 | wardrop.serverapp.com.br |
| backend | 8002 | 8000 | wardrop-api.serverapp.com.br |
| db | 5434 | 5432 | — |

**Environment variables (DO NOT CHANGE):**
- `NEXT_PUBLIC_API_URL`: Must be `https://wardrop-api.serverapp.com.br/api` (public domain, NOT localhost)

**Rebuild commands (always use -f docker-compose.prod.yml):**
```bash
# Rebuild and restart only web (after frontend changes)
docker compose -f docker-compose.prod.yml up -d --no-deps --build web

# Rebuild and restart only backend (after backend changes)
docker compose -f docker-compose.prod.yml up -d --no-deps --build backend

# Rebuild both web and backend
docker compose -f docker-compose.prod.yml up -d --no-deps --build web backend

# Start all services (no rebuild)
docker compose -f docker-compose.prod.yml up -d
```

**Important rules:**
- NEVER drop, reset, or clean the database (`wardrop-v2-db-1`). It contains production tracking data.
- NEVER use `docker compose down -v` (the `-v` flag deletes volumes/data).
- After ANY code change to `web/` or `backend/`, always rebuild the respective container before testing.

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
