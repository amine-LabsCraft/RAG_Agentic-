-- Hardening / idempotency repair (safe to apply on fresh or existing DBs).
-- Does NOT edit historic migrations (they may already be applied remotely).

-- 1. pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Storage bucket (idempotent)
INSERT INTO storage.buckets (id, name, public)
VALUES ('documents', 'documents', false)
ON CONFLICT (id) DO NOTHING;

-- 3. Storage policies (re-create idempotently)
DROP POLICY IF EXISTS "users_upload_own_documents" ON storage.objects;
CREATE POLICY "users_upload_own_documents" ON storage.objects FOR INSERT
    WITH CHECK (bucket_id = 'documents' AND (storage.foldername(name))[1] = auth.uid()::text);

DROP POLICY IF EXISTS "users_read_own_documents" ON storage.objects FOR SELECT;
CREATE POLICY "users_read_own_documents" ON storage.objects FOR SELECT
    USING (bucket_id = 'documents' AND (storage.foldername(name))[1] = auth.uid()::text);

DROP POLICY IF EXISTS "users_delete_own_documents" ON storage.objects FOR DELETE;
CREATE POLICY "users_delete_own_documents" ON storage.objects FOR DELETE
    USING (bucket_id = 'documents' AND (storage.foldername(name))[1] = auth.uid()::text);

-- Allow users to update their own files (was missing)
DROP POLICY IF EXISTS "users_update_own_documents" ON storage.objects;
CREATE POLICY "users_update_own_documents" ON storage.objects FOR UPDATE
    USING (bucket_id = 'documents' AND (storage.foldername(name))[1] = auth.uid()::text);

-- 4. Realtime publication (guard against duplicate add)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_publication_tables
        WHERE pubname = 'supabase_realtime'
          AND schemaname = 'public'
          AND tablename = 'documents'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.documents;
    END IF;
END $$;

ALTER TABLE public.documents REPLICA IDENTITY FULL;

-- 5. Ensure a global_settings row exists (PUT /settings upserts in code too)
INSERT INTO public.global_settings (id)
SELECT gen_random_uuid()
WHERE NOT EXISTS (SELECT 1 FROM public.global_settings);

-- 6. Harden match_chunks: force RLS-safe execution context.
-- Filtering is by p_user_id arg; SECURITY DEFINER + fixed search_path
-- prevents search_path hijacking while service_role calls it.
CREATE OR REPLACE FUNCTION public.match_chunks(
    query_embedding vector,
    match_threshold float,
    match_count int,
    p_user_id uuid
) RETURNS TABLE (
    id uuid, document_id uuid, content text,
    chunk_index int, metadata jsonb, similarity float
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.document_id, c.content, c.chunk_index, c.metadata,
           1 - (c.embedding <=> query_embedding) AS similarity
    FROM public.chunks c
    WHERE c.user_id = p_user_id
      AND 1 - (c.embedding <=> query_embedding) > match_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
