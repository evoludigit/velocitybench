-- VelocityBench Schema Template
-- Universal Trinity Pattern schema for all frameworks
--
-- Trinity Pattern:
--   pk_*     = SERIAL PRIMARY KEY (internal, write-optimized)
--   id       = UUID UNIQUE (public API identifier)
--   fk_*     = INTEGER FOREIGN KEY (efficient relationships)
--
-- This is the foundation schema. Framework-specific features are added via extensions.sql
-- Database: {framework}_test (created per framework)
-- Schema: benchmark (common across all frameworks)

SET search_path TO benchmark, public;

-- ============================================================================
-- CORE TABLES (Trinity Pattern)
-- ============================================================================

-- tb_user: User accounts and authentication
-- UUID id for public APIs, SERIAL pk_user for internal use
CREATE TABLE IF NOT EXISTS tb_user (
    pk_user SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    bio TEXT,
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- tb_post: Blog posts or content
-- fk_author references tb_user(pk_user) for efficient FK relationships
CREATE TABLE IF NOT EXISTS tb_post (
    pk_post SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    fk_author INTEGER NOT NULL REFERENCES tb_user(pk_user) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    excerpt VARCHAR(500),
    status VARCHAR(20) DEFAULT 'published' CHECK (status IN ('draft', 'published', 'archived')),
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- tb_comment: Comments on posts
-- Supports nested comments via fk_parent self-reference
CREATE TABLE IF NOT EXISTS tb_comment (
    pk_comment SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    fk_post INTEGER NOT NULL REFERENCES tb_post(pk_post) ON DELETE CASCADE,
    fk_author INTEGER NOT NULL REFERENCES tb_user(pk_user) ON DELETE CASCADE,
    fk_parent INTEGER REFERENCES tb_comment(pk_comment) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_approved BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- SUPPORTING TABLES (Many-to-many and Extended Data)
-- ============================================================================

-- categories: Content categories/tags
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- post_categories: Junction table for posts -> categories (many-to-many)
-- Uses UUID for consistency with API identifiers
CREATE TABLE IF NOT EXISTS post_categories (
    post_id UUID NOT NULL REFERENCES tb_post(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, category_id)
);

-- user_follows: Social graph (followers/following relationships)
CREATE TABLE IF NOT EXISTS user_follows (
    follower_id UUID NOT NULL REFERENCES tb_user(id) ON DELETE CASCADE,
    following_id UUID NOT NULL REFERENCES tb_user(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (follower_id, following_id),
    CHECK (follower_id != following_id)
);

-- post_likes: Likes/reactions on posts
CREATE TABLE IF NOT EXISTS post_likes (
    user_id UUID NOT NULL REFERENCES tb_user(id) ON DELETE CASCADE,
    post_id UUID NOT NULL REFERENCES tb_post(id) ON DELETE CASCADE,
    reaction_type VARCHAR(20) DEFAULT 'like' CHECK (reaction_type IN ('like', 'love', 'laugh', 'angry')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, post_id)
);

-- user_profiles: Extended user profile data with JSONB
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id UUID PRIMARY KEY REFERENCES tb_user(id) ON DELETE CASCADE,
    profile_data JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Indexes on foreign keys (critical for join performance)
CREATE INDEX IF NOT EXISTS idx_tb_post_fk_author ON tb_post(fk_author);
CREATE INDEX IF NOT EXISTS idx_tb_comment_fk_post ON tb_comment(fk_post);
CREATE INDEX IF NOT EXISTS idx_tb_comment_fk_author ON tb_comment(fk_author);
CREATE INDEX IF NOT EXISTS idx_tb_comment_fk_parent ON tb_comment(fk_parent);

-- Indexes on UUID columns (for API lookups)
CREATE INDEX IF NOT EXISTS idx_tb_user_id ON tb_user(id);
CREATE INDEX IF NOT EXISTS idx_tb_post_id ON tb_post(id);
CREATE INDEX IF NOT EXISTS idx_tb_comment_id ON tb_comment(id);

-- Indexes on common filter columns
CREATE INDEX IF NOT EXISTS idx_tb_post_status ON tb_post(status);
CREATE INDEX IF NOT EXISTS idx_tb_post_published_at ON tb_post(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_tb_user_username ON tb_user(username);
CREATE INDEX IF NOT EXISTS idx_tb_user_email ON tb_user(email);

-- Indexes for social features
CREATE INDEX IF NOT EXISTS idx_user_follows_follower ON user_follows(follower_id);
CREATE INDEX IF NOT EXISTS idx_user_follows_following ON user_follows(following_id);
CREATE INDEX IF NOT EXISTS idx_post_likes_post ON post_likes(post_id);
CREATE INDEX IF NOT EXISTS idx_post_likes_user ON post_likes(user_id);
CREATE INDEX IF NOT EXISTS idx_post_categories_category ON post_categories(category_id);

-- JSONB indexes for advanced queries
CREATE INDEX IF NOT EXISTS idx_user_profiles_data ON user_profiles USING GIN (profile_data);
CREATE INDEX IF NOT EXISTS idx_user_profiles_settings ON user_profiles USING GIN (settings);

-- ============================================================================
-- VIEWS AND HELPER FUNCTIONS (Shared across all frameworks)
-- ============================================================================

-- View: Basic user statistics
-- This is a non-materialized view that works consistently across all frameworks
CREATE OR REPLACE VIEW v_user_stats AS
SELECT
    u.id,
    u.pk_user,
    u.username,
    COUNT(DISTINCT p.pk_post) as post_count,
    COUNT(DISTINCT c.pk_comment) as comment_count,
    COUNT(DISTINCT uf.follower_id) as follower_count
FROM tb_user u
LEFT JOIN tb_post p ON u.pk_user = p.fk_author AND p.status = 'published'
LEFT JOIN tb_comment c ON u.pk_user = c.fk_author AND c.is_approved = true
LEFT JOIN user_follows uf ON u.id = uf.following_id
GROUP BY u.id, u.pk_user, u.username;

-- Materialized view: Post popularity (with counts)
-- Useful for benchmarking aggregation queries
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_post_popularity AS
SELECT
    p.id,
    p.pk_post,
    p.title,
    u.id as author_id,
    u.username as author_name,
    COUNT(DISTINCT pl.user_id) as like_count,
    COUNT(DISTINCT c.pk_comment) as comment_count,
    p.published_at,
    p.created_at
FROM tb_post p
JOIN tb_user u ON p.fk_author = u.pk_user
LEFT JOIN post_likes pl ON p.id = pl.post_id
LEFT JOIN tb_comment c ON p.pk_post = c.fk_post AND c.is_approved = true
WHERE p.status = 'published'
GROUP BY p.id, p.pk_post, p.title, u.id, u.username, p.published_at, p.created_at;

-- Unique index on materialized view (required for concurrent refresh)
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_post_popularity_id ON mv_post_popularity(id);

-- Function: Refresh materialized view
CREATE OR REPLACE FUNCTION refresh_post_popularity()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_post_popularity;
EXCEPTION
    WHEN OTHERS THEN
        -- In case of concurrent refresh conflicts, try without CONCURRENTLY
        REFRESH MATERIALIZED VIEW mv_post_popularity;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- NOTES FOR FRAMEWORK-SPECIFIC EXTENSIONS
-- ============================================================================
--
-- Each framework adds its own extensions via: frameworks/{framework}/database/extensions.sql
--
-- PostGraphile example:
--   - Smart tags (@omit all, @omit create,update)
--   - Custom naming for GraphQL types
--   - Field exposure control
--
-- FraiseQL example:
--   - v_* projection views (read-only representations)
--   - tv_* composition views (JSON-based representations)
--   - Sync functions (fn_sync_*)
--
-- Rails example:
--   - ActiveRecord configuration (handled via migrations)
--   - STI (single-table inheritance) if needed
--
-- Other frameworks:
--   - Custom views, functions, or configurations as needed
--
-- Framework extensions do NOT modify the Trinity Pattern tables.
-- They only ADD new views, functions, or metadata comments.
