-- Full-text search indexes for Phase 7 advanced workloads
-- Add tsvector columns for full-text search on posts and users

SET search_path TO benchmark, public;

-- Add search vectors to tb_post if not exists
ALTER TABLE tb_post ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Add search vectors to tb_user if not exists
ALTER TABLE tb_user ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Populate search vectors for existing data
UPDATE tb_post SET search_vector =
    setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(content, '')), 'B')
WHERE search_vector IS NULL;

UPDATE tb_user SET search_vector =
    setweight(to_tsvector('english', COALESCE(username, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(full_name, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(bio, '')), 'C')
WHERE search_vector IS NULL;

-- Create GIN indexes for fast full-text search
CREATE INDEX IF NOT EXISTS idx_tb_post_search ON tb_post USING GIN (search_vector);
CREATE INDEX IF NOT EXISTS idx_tb_user_search ON tb_user USING GIN (search_vector);

-- Trigger function to maintain search vectors on tb_post
CREATE OR REPLACE FUNCTION benchmark.update_tb_post_search_vector()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger function to maintain search vectors on tb_user
CREATE OR REPLACE FUNCTION benchmark.update_tb_user_search_vector()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.username, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.full_name, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.bio, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing triggers if they exist
DROP TRIGGER IF EXISTS trigger_tb_post_search_vector ON tb_post;
DROP TRIGGER IF EXISTS trigger_tb_user_search_vector ON tb_user;

-- Create triggers to automatically update search vectors
CREATE TRIGGER trigger_tb_post_search_vector
    BEFORE INSERT OR UPDATE ON tb_post
    FOR EACH ROW EXECUTE FUNCTION benchmark.update_tb_post_search_vector();

CREATE TRIGGER trigger_tb_user_search_vector
    BEFORE INSERT OR UPDATE ON tb_user
    FOR EACH ROW EXECUTE FUNCTION benchmark.update_tb_user_search_vector();

-- Helper function for searching posts with ranking
CREATE OR REPLACE FUNCTION benchmark.search_posts(p_query text, p_limit integer DEFAULT 10)
RETURNS TABLE (
    id UUID,
    title VARCHAR,
    content TEXT,
    author_id UUID,
    rank real
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.title,
        p.content,
        p.author_id,
        ts_rank(p.search_vector, plainto_tsquery('english', p_query))::real as rank
    FROM benchmark.tb_post p
    WHERE p.search_vector @@ plainto_tsquery('english', p_query)
      AND p.status = 'published'
    ORDER BY rank DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Helper function for searching users with ranking
CREATE OR REPLACE FUNCTION benchmark.search_users(p_query text, p_limit integer DEFAULT 10)
RETURNS TABLE (
    id UUID,
    username VARCHAR,
    first_name VARCHAR,
    last_name VARCHAR,
    bio TEXT,
    rank real
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id,
        u.username,
        u.first_name,
        u.last_name,
        u.bio,
        ts_rank(u.search_vector, plainto_tsquery('english', p_query))::real as rank
    FROM benchmark.tb_user u
    WHERE u.search_vector @@ plainto_tsquery('english', p_query)
      AND u.is_active = true
    ORDER BY rank DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Additional index for aggregation queries on comment counts
CREATE INDEX IF NOT EXISTS idx_tb_comment_post_author ON tb_comment(fk_post, fk_author);

-- Index for user stats queries
CREATE INDEX IF NOT EXISTS idx_tb_post_author_published ON tb_post(fk_author, published);

COMMENT ON COLUMN tb_post.search_vector IS 'Full-text search vector for posts (weighted A=title, B=content)';
COMMENT ON COLUMN tb_user.search_vector IS 'Full-text search vector for users (weighted A=username, B=name, C=bio)';
COMMENT ON FUNCTION benchmark.search_posts(text, integer) IS 'Search posts with full-text search and ranking';
COMMENT ON FUNCTION benchmark.search_users(text, integer) IS 'Search users with full-text search and ranking';
