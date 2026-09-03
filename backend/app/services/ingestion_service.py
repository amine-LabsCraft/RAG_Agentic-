"""Ingestion orchestration: download -> extract -> chunk -> embed -> store."""
import hashlib
import logging
from app.db.supabase import get_supabase_client
from app.services.chunking_service import chunk_text
from app.services.embedding_service import get_embeddings

logger = logging.getLogger(__name__)

BATCH_SIZE = 50  # embeddings per batch


async def process_document(document_id: str, user_id: str) -> None:
    """
    Process an uploaded document: extract text, chunk, embed, and store.

    Updates document status throughout the process.
    """
    supabase = get_supabase_client()

    try:
        # Update status to processing (scoped to owner to avoid cross-user writes)
        supabase.table("documents").update({
            "status": "processing"
        }).eq("id", document_id).eq("user_id", user_id).execute()

        # Get document record (ownership enforced)
        try:
            doc_result = supabase.table("documents").select("*").eq(
                "id", document_id).eq("user_id", user_id).maybe_single().execute()
        except Exception:
            raise ValueError(f"Document {document_id} not found")
        doc = doc_result.data if doc_result else None

        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # Download file from storage
        storage_path = doc["storage_path"]
        file_bytes = supabase.storage.from_("documents").download(storage_path)
        # supabase-py may return bytes or a response object
        if not isinstance(file_bytes, (bytes, bytearray)):
            file_bytes = getattr(file_bytes, "data", file_bytes) or getattr(file_bytes, "content", b"")

        # Record Manager: hash bytes for change detection / incremental skip
        content_hash = hashlib.sha256(bytes(file_bytes)).hexdigest()
        try:
            supabase.table("documents").update({
                "content_hash": content_hash,
            }).eq("id", document_id).execute()
        except Exception:
            pass  # column missing until migration applied

        # Incremental shortcut: same hash already has chunks (e.g. reprocess
        # of unchanged content) — skip embed + insert.
        try:
            existing_chunks = supabase.table("chunks").select(
                "id", count="exact").eq("document_id", document_id).limit(1).execute()
            if (existing_chunks.count or 0) > 0 and doc.get("content_hash") == content_hash:
                supabase.table("documents").update({
                    "status": "completed",
                }).eq("id", document_id).execute()
                logger.info(f"Document {document_id} unchanged (hash {content_hash[:8]}...), skipped re-embedding")
                return
        except Exception:
            pass

        # Extract text based on file type
        text = extract_text(file_bytes, doc["file_type"])

        if not text.strip():
            raise ValueError("No text content extracted from document")

        # Chunk the text
        chunks = chunk_text(text)

        if not chunks:
            raise ValueError("No chunks generated from document")

        # Batch embed and store chunks
        total_chunks = 0
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            embeddings = await get_embeddings(batch, user_id=user_id)

            # Insert chunks with embeddings
            chunk_records = []
            for j, (chunk_content, embedding) in enumerate(zip(batch, embeddings)):
                chunk_records.append({
                    "document_id": document_id,
                    "user_id": user_id,
                    "content": chunk_content,
                    "chunk_index": i + j,
                    "embedding": embedding,
                    "metadata": {
                        "filename": doc["filename"],
                        "chunk_index": i + j,
                    },
                })

            supabase.table("chunks").insert(chunk_records).execute()
            total_chunks += len(batch)

        # Update document status to completed
        supabase.table("documents").update({
            "status": "completed",
            "chunk_count": total_chunks,
        }).eq("id", document_id).execute()

        logger.info(f"Document {document_id} processed: {total_chunks} chunks created")

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        supabase.table("documents").update({
            "status": "failed",
            "error_message": str(e),
        }).eq("id", document_id).execute()


def extract_text(file_bytes: bytes, file_type: str) -> str:
    """Extract text from file bytes based on file type."""
    # Module 2: only .txt and .md supported
    if file_type in ("text/plain", "text/markdown"):
        return file_bytes.decode("utf-8")

    # Try to decode as text for common extensions
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError(f"Unsupported file type: {file_type}. Only .txt and .md files are supported.")
