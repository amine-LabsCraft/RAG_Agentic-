# Progress

Track your progress through the masterclass. Update this file as you complete modules - Claude Code reads this to understand where you are in the project.

## Convention
- `[ ]` = Not started
- `[-]` = In progress
- `[x]` = Completed

## Modules

### Module 1: App Shell + Observability
- [x] Backend Setup - FastAPI skeleton with health endpoint
- [x] Supabase Client - Backend Supabase client wrapper
- [x] Database Schema - threads and messages tables with RLS
- [x] Auth Middleware - JWT verification and /auth/me endpoint
- [x] Frontend Setup - Vite + React + Tailwind + shadcn/ui
- [x] Frontend Supabase Client
- [x] Auth UI - Sign in/sign up forms
- [x] OpenAI Assistant Service - Responses API integration
- [x] Thread API - CRUD endpoints
- [x] Chat API with SSE - Streaming messages
- [x] Thread List UI
- [x] Chat View UI
- [x] Main App Assembly
- [x] LangSmith Tracing

**Status: COMPLETE ✓**

### Module 2: BYO Retrieval + Provider Abstraction
- [x] Phase 1: Provider Abstraction - ChatCompletions API with configurable base_url/api_key
- [x] Phase 2: Database Schema - pgvector extension, documents/chunks tables, RLS, match_chunks function, storage bucket
- [x] Phase 3: Ingestion Pipeline - embedding_service, chunking_service, ingestion_service, documents router
- [x] Phase 4: Retrieval Tool - retrieval_service, tool_executor, RAG_TOOLS definition, tool-calling loop in chat
- [x] Phase 5: Ingestion UI + Realtime - DocumentsPage, DocumentUpload, DocumentList, useRealtimeDocuments hook

**Status: COMPLETE ✓**

## Validation Summary
- [x] Supabase project linked via CLI (project ref: dkbbhbpluvtimzzyavyg)
- [x] SQL migration applied via `supabase db push`
- [x] Backend venv created and dependencies installed
- [x] Backend server running (health endpoint validated)
- [x] Frontend .env file created
- [x] Frontend npm install completed
- [x] Frontend dev server verified working
- [x] Service startup scripts created (`scripts/start-*.ps1`)
- [x] Playwright MCP configured for browser testing
- [x] Auth flow tested - Sign in/sign up working
- [x] Thread creation and chat tested - Messages streaming correctly
- [x] LangSmith tracing configured (verify traces in LangSmith dashboard)

## Module 2 Validation
- [x] Database migrations applied (pgvector, documents, chunks tables, storage bucket)
- [x] Backend starts with new LLM service (ChatCompletions API)
- [x] Documents page accessible with upload zone and document list
- [x] File upload works (.txt/.md), status updates in real-time via Supabase Realtime
- [x] Ingestion pipeline: upload → chunk → embed → store in pgvector
- [x] RAG retrieval: chat calls search_documents tool, retrieves relevant chunks, cites sources
- [x] Tool-calling loop with max 3 rounds works correctly

### Validation Suite
- [x] Test fixture files created (.agent/validation/fixtures/)
- [x] Full validation suite written (.agent/validation/full-suite.md)
- [x] 45 API tests (curl-based) covering health, auth, threads, chat, documents, settings, errors, pagination, dedup, reprocess
- [x] 30 E2E browser tests (Playwright MCP) covering auth, chat, navigation, documents, RAG, isolation, dedup, mobile layout
- [x] Cleanup section to reset state after test runs
- [x] CLAUDE.md updated with test suite maintenance instructions for future agents

**Status: COMPLETE**

### Hardening + Module 3: Record Manager (done, pending `supabase db push`)
- [x] Backend P0: langsmith key fix, CORS parsing, traceback leak, utcnow, finish_reason, .single()->404, settings upsert, embedding dimensions fallback, tool guards, chunking bounds
- [x] Security: GET /settings admin-only, Fernet validation at startup, filename sanitization, orphan Storage cleanup, ingestion user_id scoping
- [x] Frontend: SSE parser (CRLF/[DONE]), ChatView reconcile + no scroll-hijack, useRealtimeDocuments fix, App 404, useAuth race, Settings dimensions guard
- [x] Layout: shared AppLayout (desktop sidebar + mobile hamburger), Chat/Documents/Settings refactored
- [x] Pagination: threads/documents/messages limit+offset (backend range + frontend Load more)
- [x] Record Manager: content_hash column + migration, upload dedup (returns existing + notice), ingestion incremental skip, POST /documents/{id}/reprocess, Reprocess button in UI
- [ ] Apply migrations: `supabase db push` (hardening_repair + record_manager_hash), then restart backend

**Status: COMPLETE (code) / PENDING (db push + manual validation)**

## Notes
- Test user created: test@test.com (see CLAUDE.md for credentials)
- Migration updated to use `gen_random_uuid()` instead of `uuid_generate_v4()`
- All core Module 1 functionality validated and working

## Service URLs
- **Frontend:** http://localhost:5173
- **Backend:** http://localhost:8000
- **Backend Health:** http://localhost:8000/health

## Windows/MINGW Notes
- npm commands produce no output in MINGW/Git Bash
- Always use PowerShell for npm and service commands
- See `scripts/` folder for ready-to-use startup scripts
- CLAUDE.md has been updated with service startup instructions
