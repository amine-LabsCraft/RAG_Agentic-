-- Module 3 — Record Manager: content hashing for dedup / incremental ingestion.

ALTER TABLE public.documents
    ADD COLUMN IF NOT EXISTS content_hash TEXT;

CREATE INDEX IF NOT EXISTS idx_documents_content_hash
    ON public.documents (user_id, content_hash);

-- Backfill hashes for existing rows where possible is not feasible from SQL
-- (bytes live in Storage); NULL hashes simply skip dedup until reprocessed.
