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
