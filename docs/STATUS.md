# Rune — Implementation Status

This document tracks what is **actually built** versus what the README describes as product intent.

Last updated: Phase 0, Step 2 (Persistent workspace)

## Phase 0 — Foundation

| Component | Status | Notes |
|---|---|---|
| Monorepo scaffold (`apps/desktop`, `apps/backend`) | Done | npm workspaces |
| FastAPI skeleton + `/api/v1/health` | Done | |
| Config + structured logging | Done | |
| Module directory placeholders | Done | `ai/`, `db/`, `workspace/`, `workers/`, `services/` |
| Tauri + React shell | Done | Vite dev server; Tauri requires Rust toolchain |
| Local HTTP client (frontend → backend) | Done | Home page health check |
| Dev scripts | Done | `npm run dev:all`, `scripts/setup.ps1` |
| CI (lint + test) | Done | GitHub Actions |
| SQLite database + Alembic migrations | Done | Database is migrated on backend startup in Rune's local application-data directory. |
| Persistent workspace selection API | Done | `GET/PUT/PATCH/DELETE /api/v1/workspace`; validates an existing directory and persists only its location. |
| Workspace selection frontend flow | Done | First launch prompts for a folder; later launches load the saved selection. No scanning or indexing occurs. |
| Provider abstraction (Ollama) | Not started | Phase 0 Step 2 |
| Tauri backend lifecycle (spawn/kill) | Not started | Phase 0 Step 2 |

## MVP Features (from README roadmap)

| Feature | Status |
|---|---|
| Workspace selection & persistence | Done — location only; no file scanning, indexing, or watching |
| Workspace indexing & sync | Not started |
| RAG chat | Not started |
| Persistent memory | Not started |
| Local LLM (Ollama) | Not started |
| Concept mastery tracking | Not started |
| Practice generation | Not started |

## How to verify this milestone

```bash
# Setup (once)
./scripts/setup.ps1        # Windows
# ./scripts/setup.sh       # macOS/Linux

# Terminal 1 — backend
npm run dev:backend

# Terminal 2 — frontend
npm run dev

# Or both together
npm run dev:all
```

Open http://localhost:1420 — the Home page should show backend status `ok`.

```bash
npm run test:backend
```

## Persistent workspace developer note

Rune stores its SQLite database at `%LOCALAPPDATA%\\Rune\\rune.db` on Windows (or
`~/.local/Rune/rune.db` when `LOCALAPPDATA` is unavailable). Set `DATA_DIR` to use a
different location for local development or tests. SQLite runs in WAL mode for the
single-user desktop workload.

The backend upgrades the database to the latest Alembic revision during startup. To
run migrations manually from `apps/backend`, use:

```bash
alembic upgrade head
```

The `workspaces` table deliberately contains only the currently selected academic
folder's path, display name, and timestamps. Selecting a folder validates and saves
that location; Rune does not scan, index, copy, or watch its contents in this phase.
