# Rune — Implementation Status

This document tracks what is **actually built** versus what the README describes as product intent.

## sqlite-vec bundling (Phase 3)

`sqlite-vec` is loaded into every Python SQLite connection before application
SQL or Alembic migrations run. Release packaging must pin and bundle the
platform-specific `sqlite-vec` wheel (Windows, macOS, or Linux) with Rune's
backend runtime; no system extension path is required.

Last updated: Phase 2 — Document ingestion backend scaffold and auto-enqueue handoff

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

## Phase 2 — Document Ingestion Backend

| Component | Status | Notes |
|---|---|---|
| Dual-stage document processing model | Done | `document_processing` now tracks extraction and chunking independently with per-stage versions, hashes, error counts, and timestamps. |
| Segment and chunk tables | Done | `document_segments` stores format-specific segments; `chunks` stores segment-local offsets and hashes with no token-count or embedding columns. |
| Automatic scan-to-ingestion handoff | Done | `ScanManager` now enqueues supported new/changed files after a scan completes. |
| Startup crash reconciliation | Done | Orphaned `extracting`/`chunking` rows are reset to retryable states on worker startup. |
| Slim ingestion job marker table | Done | `document_processing_jobs` is marker-only (`id`, `workspace_id`, `status`, `started_at`, `finished_at`). |
| Error-message sanitization | Done | Persisted extraction/chunking error messages are truncated and sanitized before storage. |
| Document API surface | Partial | Backend processing exists; a dedicated document-status/retry API is still not exposed. |
| Document UI | Partial | `Documents` still shows the workspace file list, not the four-state user-facing ingestion view. |

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

Backend validation was last verified with `pytest` and `ruff check`; frontend validation with `npm run lint` and `npm run build`.
