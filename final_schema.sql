-- ============================================
-- FINAL SUPABASE DATABASE SCHEMA
-- Complete Interactive Book Generation System
-- Run this in your Supabase SQL Editor
-- ============================================

-- Drop existing tables if you want to start fresh (OPTIONAL - COMMENT OUT if you want to keep existing data)
-- DROP TABLE IF EXISTS final_state CASCADE;
-- DROP TABLE IF EXISTS chapters CASCADE;
-- DROP TABLE IF EXISTS outlines CASCADE;
-- DROP TABLE IF EXISTS books CASCADE;

-- ============================================
-- 1. BOOKS TABLE
-- Stores book metadata
-- ============================================
CREATE TABLE IF NOT EXISTS books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- 2. OUTLINES TABLE
-- Stores book outlines with user feedback and ratings
-- ============================================
CREATE TABLE IF NOT EXISTS outlines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    outline TEXT,
    notes_before TEXT,
    notes_after TEXT,
    status TEXT DEFAULT 'pending',
    user_rating INTEGER CHECK (user_rating >= 0 AND user_rating <= 10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- 3. CHAPTERS TABLE
-- Stores individual chapters with approval workflow
-- ============================================
CREATE TABLE IF NOT EXISTS chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    chapter_number INTEGER NOT NULL,
    title TEXT,
    content TEXT,
    summary TEXT,
    user_feedback TEXT,
    status TEXT DEFAULT 'pending',
    user_rating INTEGER CHECK (user_rating >= 0 AND user_rating <= 10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(book_id, chapter_number)
);

-- ============================================
-- 4. FINAL_STATE TABLE
-- Tracks final compilation status and overall rating
-- ============================================
CREATE TABLE IF NOT EXISTS final_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    final_review_status TEXT,
    output_status TEXT DEFAULT 'pending',
    user_rating INTEGER CHECK (user_rating >= 0 AND user_rating <= 10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(book_id)
);

-- ============================================
-- ADD MISSING COLUMNS TO EXISTING TABLES
-- (Safe to run even if columns already exist)
-- ============================================

-- Add columns to chapters if they don't exist
DO $$ 
BEGIN
    -- Add status column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='chapters' AND column_name='status') THEN
        ALTER TABLE chapters ADD COLUMN status TEXT DEFAULT 'pending';
    END IF;
    
    -- Add user_feedback column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='chapters' AND column_name='user_feedback') THEN
        ALTER TABLE chapters ADD COLUMN user_feedback TEXT;
    END IF;
    
    -- Add user_rating column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='chapters' AND column_name='user_rating') THEN
        ALTER TABLE chapters ADD COLUMN user_rating INTEGER CHECK (user_rating >= 0 AND user_rating <= 10);
    END IF;
END $$;

-- Add columns to outlines if they don't exist
DO $$ 
BEGIN
    -- Add status column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='outlines' AND column_name='status') THEN
        ALTER TABLE outlines ADD COLUMN status TEXT DEFAULT 'pending';
    END IF;
    
    -- Add user_rating column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='outlines' AND column_name='user_rating') THEN
        ALTER TABLE outlines ADD COLUMN user_rating INTEGER CHECK (user_rating >= 0 AND user_rating <= 10);
    END IF;
END $$;

-- Add columns to final_state if they don't exist
DO $$ 
BEGIN
    -- Add user_rating column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='final_state' AND column_name='user_rating') THEN
        ALTER TABLE final_state ADD COLUMN user_rating INTEGER CHECK (user_rating >= 0 AND user_rating <= 10);
    END IF;
END $$;

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_outlines_book_id ON outlines(book_id);
CREATE INDEX IF NOT EXISTS idx_chapters_book_id ON chapters(book_id);
CREATE INDEX IF NOT EXISTS idx_chapters_book_chapter ON chapters(book_id, chapter_number);
CREATE INDEX IF NOT EXISTS idx_chapters_status ON chapters(status);
CREATE INDEX IF NOT EXISTS idx_final_state_book_id ON final_state(book_id);

-- ============================================
-- UPDATE EXISTING DATA
-- Set default values for any null status fields
-- ============================================
UPDATE chapters SET status = 'pending' WHERE status IS NULL;
UPDATE outlines SET status = 'pending' WHERE status IS NULL;
UPDATE final_state SET output_status = 'pending' WHERE output_status IS NULL;

-- ============================================
-- ENABLE ROW LEVEL SECURITY (RLS) - Optional
-- Uncomment if you want to enable RLS
-- ============================================
-- ALTER TABLE books ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE outlines ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE chapters ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE final_state ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Enable read access for all users" ON books FOR SELECT USING (true);
-- CREATE POLICY "Enable insert for all users" ON books FOR INSERT WITH CHECK (true);
-- CREATE POLICY "Enable update for all users" ON books FOR UPDATE USING (true);
-- CREATE POLICY "Enable delete for all users" ON books FOR DELETE USING (true);

-- (Repeat for other tables if needed)

-- ============================================
-- TABLE COMMENTS (Documentation)
-- ============================================
COMMENT ON TABLE books IS 'Main books table - stores book metadata and title';
COMMENT ON TABLE outlines IS 'Book outlines with user feedback and quality ratings';
COMMENT ON TABLE chapters IS 'Individual chapters with approval workflow and ratings';
COMMENT ON TABLE final_state IS 'Final compilation status and overall book rating';

COMMENT ON COLUMN books.id IS 'Unique book identifier (UUID)';
COMMENT ON COLUMN books.title IS 'Book title as specified by user';

COMMENT ON COLUMN outlines.status IS 'Workflow status: pending, pending_approval, approved, needs_revision';
COMMENT ON COLUMN outlines.notes_before IS 'Initial requirements and notes from user';
COMMENT ON COLUMN outlines.notes_after IS 'User feedback for revision';
COMMENT ON COLUMN outlines.user_rating IS 'Optional user rating 0-10 for outline quality';

COMMENT ON COLUMN chapters.status IS 'Workflow status: pending, generating, pending_approval, approved, needs_revision';
COMMENT ON COLUMN chapters.chapter_number IS 'Sequential chapter number (1, 2, 3...)';
COMMENT ON COLUMN chapters.summary IS 'AI-generated summary for context in subsequent chapters';
COMMENT ON COLUMN chapters.user_feedback IS 'User comments for revision requests';
COMMENT ON COLUMN chapters.user_rating IS 'Optional user rating 0-10 for chapter quality';

COMMENT ON COLUMN final_state.output_status IS 'Compilation status: pending, in_progress, completed, failed';
COMMENT ON COLUMN final_state.user_rating IS 'Overall book quality rating 0-10';

-- ============================================
-- VERIFICATION QUERIES
-- Run these to verify your schema is correct
-- ============================================

-- Count tables
SELECT 'Tables created:' as info, COUNT(*) as count 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('books', 'outlines', 'chapters', 'final_state');

-- Show all columns for each table
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name IN ('books', 'outlines', 'chapters', 'final_state')
ORDER BY table_name, ordinal_position;

-- Show indexes
SELECT tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public'
AND tablename IN ('books', 'outlines', 'chapters', 'final_state')
ORDER BY tablename;

-- Show foreign keys
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' 
AND tc.table_schema='public'
AND tc.table_name IN ('books', 'outlines', 'chapters', 'final_state');

-- ============================================
-- SUCCESS MESSAGE
-- ============================================
SELECT '✅ Database schema setup complete!' as message,
       'All tables, columns, indexes, and constraints are ready.' as details,
       'You can now run your Book Generation system!' as status;
