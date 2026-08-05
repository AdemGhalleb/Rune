# Rune — Implementation Status

This document tracks what is **actually built** versus what the README describes as product intent.

Last updated: Phase 0, Step 1 (Foundation scaffold)

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
| Database + migrations | Not started | Phase 0 Step 2 |
| Provider abstraction (Ollama) | Not started | Phase 0 Step 2 |
| Tauri backend lifecycle (spawn/kill) | Not started | Phase 0 Step 2 |

## MVP Features (from README roadmap)

| Feature | Status |
|---|---|
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
