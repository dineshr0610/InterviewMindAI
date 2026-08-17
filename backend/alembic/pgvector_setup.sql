-- Enable pgvector extension in Supabase PostgreSQL
CREATE EXTENSION IF NOT EXISTS vector;

-- Create vector document store table in Supabase
CREATE TABLE IF NOT EXISTS document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for similarity search using IVFFlat index on cosine similarity
CREATE INDEX IF NOT EXISTS document_embeddings_vector_idx 
ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);


CREATE OR REPLACE FUNCTION match_document_embeddings(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.0,
    match_count INT DEFAULT 2
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE SQL
STABLE
AS $$
    SELECT
        de.id,
        de.content,
        de.metadata,
        1 - (de.embedding <=> query_embedding) AS similarity
    FROM document_embeddings de
    WHERE de.embedding IS NOT NULL
      AND 1 - (de.embedding <=> query_embedding) >= match_threshold
    ORDER BY de.embedding <=> query_embedding
    LIMIT match_count;
$$;