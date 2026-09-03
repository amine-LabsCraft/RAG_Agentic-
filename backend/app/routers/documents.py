"""Document upload, list, and delete endpoints."""
import hashlib
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query, status

from app.dependencies import get_current_user, User
from app.db.supabase import get_supabase_client
from app.services.ingestion_service import process_document

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_TYPES = {
    "text/plain": ".txt",
    "text/markdown": ".md",
    "application/octet-stream": None,  # fallback, check extension
}
ALLOWED_EXTENSIONS = {".txt", ".md"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a document for ingestion."""
    # Validate file extension + sanitize filename (prevent path traversal)
    raw_filename = file.filename or "unknown"
    filename = raw_filename.split("/")[-1].split("\\")[-1].strip()[:255] or "unknown"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10 MB."
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty."
        )

    # Determine content type
    content_type = file.content_type or "text/plain"
    if ext == ".md":
        content_type = "text/markdown"
    elif ext == ".txt":
        content_type = "text/plain"

    supabase = get_supabase_client()

    # Module 3 — Record Manager: content hash for dedup / change detection.
    content_hash = hashlib.sha256(content).hexdigest()
    try:
        existing = supabase.table("documents").select("id, filename, status, chunk_count, created_at").eq(
            "user_id", current_user.id
        ).eq("content_hash", content_hash).limit(1).maybe_single().execute()
    except Exception:
        existing = None  # column may not exist yet (migration pending)
    if existing and existing.data:
        # Same bytes already ingested — return it instead of duplicating
        # storage, chunks and embeddings.
        return {**existing.data, "deduplicated": True}

    # Upload to Supabase Storage
    file_id = str(uuid.uuid4())
    storage_path = f"{current_user.id}/{file_id}{ext}"

    try:
        supabase.storage.from_("documents").upload(
            path=storage_path,
            file=content,
            file_options={"content-type": content_type},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage upload failed: {e}"
        )

    # Create document record (cleanup Storage object if DB insert fails)
    doc_record = {
        "user_id": current_user.id,
        "filename": filename,
        "file_type": content_type,
        "file_size": len(content),
        "storage_path": storage_path,
        "status": "pending",
        "content_hash": content_hash,
    }

    try:
        result = supabase.table("documents").insert(doc_record).execute()
    except Exception as e:
        # Fallback for DBs where the content_hash migration hasn't applied yet
        if "content_hash" in str(e).lower():
            doc_record.pop("content_hash", None)
            try:
                result = supabase.table("documents").insert(doc_record).execute()
            except Exception as e2:
                try:
                    supabase.storage.from_("documents").remove([storage_path])
                except Exception:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create document record: {e2}"
                )
        else:
            try:
                supabase.storage.from_("documents").remove([storage_path])
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create document record: {e}"
            )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create document record"
        )

    document = result.data[0]

    # Trigger background processing
    background_tasks.add_task(process_document, document["id"], current_user.id)

    return document


@router.get("")
async def list_documents(
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List all documents for the current user (paginated, newest first)."""
    supabase = get_supabase_client()
    result = supabase.table("documents").select("*").eq(
        "user_id", current_user.id
    ).order("created_at", desc=True).range(offset, offset + limit - 1).execute()

    return result.data


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Re-run ingestion for a document (e.g. after failure or provider change)."""
    supabase = get_supabase_client()
    try:
        result = supabase.table("documents").select("id, status").eq(
            "id", document_id
        ).eq("user_id", current_user.id).maybe_single().execute()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    if not result or not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    # Reset chunks + status, then re-queue (incremental: same content_hash
    # skips re-embedding if chunks already exist — see process_document).
    supabase.table("chunks").delete().eq("document_id", document_id).execute()
    supabase.table("documents").update({
        "status": "pending",
        "error_message": None,
        "chunk_count": 0,
    }).eq("id", document_id).execute()
    background_tasks.add_task(process_document, document_id, current_user.id)
    return {"status": "requeued", "document_id": document_id}


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a document and its storage file (chunks cascade via FK)."""
    supabase = get_supabase_client()

    # Get document (never raises on 0 rows; ownership enforced by user_id filter)
    try:
        result = supabase.table("documents").select("*").eq(
            "id", document_id
        ).eq("user_id", current_user.id).maybe_single().execute()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    doc = result.data

    # Delete from storage
    try:
        supabase.storage.from_("documents").remove([doc["storage_path"]])
    except Exception:
        pass  # Storage file may already be gone

    # Delete document record (chunks cascade)
    supabase.table("documents").delete().eq("id", document_id).execute()

    return {"status": "deleted"}
