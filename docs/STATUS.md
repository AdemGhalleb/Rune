# Rune — Implementation Status

This document tracks what is **actually built** versus what the README describes as product intent.

Last updated: Phase 1 — Workspace Intelligence & Incremental Filesystem Synchronization

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
| SQLite database + Alembic migrations | Done | SQLite WAL mode enabled on connection; database is migrated on backend startup in Rune's app data directory. |
| Persistent workspace selection API | Done | `GET/PUT/PATCH/DELETE /api/v1/workspace`; validates an existing directory and persists only its location. |
| Workspace selection frontend flow | Done | First launch prompts for a folder; later launches load the saved selection. |

## Phase 1 — Workspace Intelligence & Incremental Synchronization

| Component | Status | Notes |
|---|---|---|
| Incremental recursive scanner | Done | Fast initial `stat` traversal, ignores build/vcs dirs (`node_modules`, `.git`, `.venv`, etc.), symlink boundary validation, unreadable file error isolation. |
| Category & Extension Resolver | Done | Maps extensions to `document`, `note`, `presentation`, `spreadsheet`, `code`, `image`, `archive`, `unknown`. |
| Lazy SHA-256 Hasher | Done | Chunked hashing on demand when size/mtime change; avoids reading unchanged files into memory. |
| Incremental Change Detector | Done | Classifies files as `NEW`, `UNCHANGED`, `MODIFIED`, `DELETED`, `IGNORED`, `ERROR`. Detects renames by `(size_bytes, content_hash)` match within single scan. Batched DB commits (200 records). |
| Background Scan Runner | Done | In-process thread-safe manager using `asyncio.to_thread`. Enforces single-flight per workspace. Live progress reporting (`files_discovered`, `files_processed`). Per-file cancellation check. |
| Workspace Scanning & Overview APIs | Done | `POST /scan`, `GET /scan/latest`, `POST /scan/cancel`, `GET /overview`, `GET /files`. |
| Frontend Status Integration | Done | Auto silent background scanning on workspace select/load, human-friendly status indicator in Sidebar, live paginated file list & search in Documents view. |

## MVP Features (from README roadmap)

| Feature | Status |
|---|---|
| Workspace selection & persistence | Done |
| Workspace indexing & sync | Done (Phase 1 metadata scan & incremental sync complete; vector embedding pipeline to follow in Phase 2) |
| RAG chat | Not started |
| Persistent memory | Not started |
| Local LLM (Ollama) | Not started |
| Concept mastery tracking | Not started |
| Practice generation | Not started |

## How to verify this milestone

```bash
# Terminal 1 — backend
npm run dev:backend

# Terminal 2 — frontend
npm run dev

# Or both together
npm run dev:all
```

Run test suite:
```bash
npm run test:backend
npm run lint
```
