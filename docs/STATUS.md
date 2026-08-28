# Rune — Implementation Status

This document tracks what is **actually built** versus what the README describes as product intent.

## sqlite-vec bundling (Phase 3)

`sqlite-vec` is loaded into every Python SQLite connection before application
SQL or Alembic migrations run. Release packaging must pin and bundle the
platform-specific `sqlite-vec` wheel (Windows, macOS, or Linux) with Rune's
backend runtime; no system extension path is required.

Last updated: Phase 5B — Study Persistence (Sessions, Flashcards, Quizzes, Attempts with Workspace Isolation & Persistence)

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
| Workspace indexing & sync | Done |
| RAG chat | Done |
| Persistent memory | Not started |
| Local LLM (Ollama) | Done |
| Study Generation (Summaries, Flashcards, Quizzes, Explanations) | Done |
| Study Persistence | Done | Phase 5B |
| Concept mastery tracking | Not started (Phase 5C) |
| Practice generation | Not started |

## Phase 3 — Embeddings & Vector Retrieval

| Component | Status | Notes |
|---|---|---|
| Embedding provider | Done | Generates embeddings for processed chunks using the configured local embedding model. |
| Embedding persistence | Done | Chunk embedding metadata is persisted and linked to the corresponding vector representation. |
| sqlite-vec integration | Done | Vector extension is loaded before application SQL/migrations and bundled for supported platforms. |
| Vector indexing | Done | Processed chunks are embedded and indexed incrementally. |
| Similarity search | Done | Query embeddings are compared against workspace-scoped chunk vectors. |
| Incremental embedding | Done | Unchanged chunks are not unnecessarily re-embedded; processing state/version changes trigger required updates. |
| Retrieval metadata | Done | Retrieved vectors map back to chunks and workspace files for RAG citations. |
| Workspace isolation | Done | Retrieval is scoped to the active workspace. |

## Phase 4 — RAG + AI Chat

| Component | Status | Notes |
|---|---|---|
| Conversation persistence | Done | Conversations, messages, and message-to-chunk citations are stored separately from workspace knowledge. |
| Local LLM provider | Done | Ollama provider with a `llama3.2:3b` default, availability check, timeout/error handling, and streaming interface. |
| Chat API and SSE transport | Done | Conversation CRUD, streamed `POST` messages, incremental assistant persistence, source endpoint, cancellation on disconnect, and startup reconciliation. |
| RAG prompt boundary | Done | RAG service builds history/context prompts with explicit untrusted-reference delimiters, similarity threshold, de-duplication, per-document cap, and configurable budgets. |
| Chat UI | Done | Conversation list, streamed messages, source chips, stop/error states, and an Ollama-unavailable banner. |
| Live vector-store adapter | Done | Phase 3 includes a sqlite-vec-backed chunk vector store with workspace-scoped similarity search, query embedding via the embedding provider, and retrieval metadata mapping back to chunk/workspace file rows. |

## Phase 5A — Study Generation

| Component | Status | Notes |
|---|---|---|
| Grounded Study Schemas | Done | Pydantic schemas for `SummaryResponse`, `FlashcardSetResponse`, `QuizResponse`, `ExplanationResponse`, and `StudyCitation`. |
| Study Generation Service | Done | `StudyGenerationService` orchestrates prompt assembly with untrusted delimiters, JSON parsing/validation, prompt-injection defense, and citation ID mapping. |
| Targeted Retrieval | Done | `RetrievalService` and `SQLiteChunkVectorStore` support both semantic query search and document-scoped chunk retrieval. |
| Study API Endpoints | Done | `POST /api/v1/study/summary`, `POST /api/v1/study/flashcards`, `POST /api/v1/study/quiz`, and `POST /api/v1/study/explain`. |
| Interactive Study UI | Done | `LearningPage` supports Summarize, Flashcard 3D flip deck, interactive Quiz runner with answer feedback & scoring, and Explain modes with source citation cards. |

## Phase 5B — Study Persistence

| Component | Status | Notes |
|---|---|---|
| Study Session Models | Done | `StudySession` (summary, flashcards, quiz, explanation), `StudyFlashcard`, `StudyQuizQuestion`, `StudyQuizAttempt` with proper relationships and cascade behavior. |
| Citation Models | Done | `StudySessionCitation`, `StudyFlashcardCitation`, `StudyQuizQuestionCitation` link generated material back to source chunks and workspace files. |
| Database Migration | Done | Migration `20260828_0007_study_persistence` creates all study persistence tables with proper indices and foreign keys. |
| Study Persistence Service | Done | `StudyPersistenceService` implements full CRUD for study sessions, flashcard review state tracking, quiz attempt recording, and retrieval with eager-loaded relationships. |
| Study Persistence API | Done | `POST /sessions`, `GET /sessions`, `GET /sessions/{id}`, `DELETE /sessions/{id}`, `POST /sessions/{id}/flashcards/{id}/review`, `POST /sessions/{id}/quiz/attempt`, `GET /sessions/{id}/quiz/attempts`. |
| Frontend Session Management | Done | LearningPage integrates session save/load/delete, flashcard review state updates, quiz attempt recording, and "Saved Sessions" history tab with filtering. |
| Workspace Isolation | Done | Study sessions are properly scoped to workspace_id; cross-workspace access is rejected. |
| Data Persistence | Done | Study data persists across application restart; verified via test `test_study_persistence_across_sessions`. |
| Comprehensive Tests | Done | 13 tests covering all persistence operations, workspace isolation, schema migrations, and critical restart scenarios. |

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

### Phase 5B Verification

To verify study persistence works across application restart:

1. Start the backend and frontend (see above)
2. Select a workspace and ensure documents are indexed
3. Generate a summary, flashcards, or quiz
4. Click "Save Session to Library" to persist to database
5. Navigate to "Saved Sessions" tab to see the saved session
6. **Restart the backend and frontend**
7. Navigate back to "Saved Sessions" tab
8. **Verify the previously saved session is still there** (persisted across restart)
9. Load the session and verify all content is intact

Backend validation was verified with `pytest` (55 tests passed) and `ruff check`; frontend validation with `tsc --noEmit` and `vite build`.
