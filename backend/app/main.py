from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import get_settings
from app.routers import auth, threads, chat, documents
from app.routers import settings as settings_router

logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="RAG Masterclass API",
    description="Backend API for the RAG Masterclass application",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions. Log full details, return generic message."""
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Include routers
app.include_router(auth.router)
app.include_router(threads.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(settings_router.router)


@app.on_event("startup")
async def validate_startup_config():
    """Fail fast on invalid crypto config; reset stuck ingestion jobs."""
    if not settings.settings_encryption_key:
        logger.warning(
            "SETTINGS_ENCRYPTION_KEY is not set - provider API keys will be "
            "stored in plaintext. Set it in backend/.env for production."
        )
    else:
        # Validate the key format early instead of crashing on first use.
        try:
            from cryptography.fernet import Fernet
            Fernet(settings.settings_encryption_key.encode())
        except Exception as e:
            logger.error(f"Invalid SETTINGS_ENCRYPTION_KEY: {e}")
            raise RuntimeError(f"Invalid SETTINGS_ENCRYPTION_KEY: {e}")

    # Reconcile documents stuck in pending/processing (e.g. server restarted
    # while BackgroundTasks were running). Re-queue them via the API client.
    try:
        from app.db.supabase import get_supabase_client
        from app.services import ingestion_service
        import asyncio
        supabase = get_supabase_client()
        stuck = supabase.table("documents").select("id, user_id").in_(
            "status", ["pending", "processing"]).execute()
        rows = stuck.data or []
        if rows:
            logger.warning(f"Found {len(rows)} stuck document(s), re-queueing for processing")
            for row in rows:
                asyncio.create_task(
                    ingestion_service.process_document(row["id"], row["user_id"])
                )
    except Exception as e:
        logger.warning(f"Ingestion reconciliation skipped: {e}")
