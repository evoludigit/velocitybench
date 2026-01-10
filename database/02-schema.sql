-- Benchmark database schema for GraphQL framework comparison
-- This schema provides a realistic dataset for testing various GraphQL patterns

SET search_path TO benchmark, public;

-- tb_user: Users table (core entity, write-side)
-- Trinity Pattern: pk_user (integer PK) + id (UUID for API) + fk_* (integer FKs)
CREATE TABLE tb_user (
    pk_user SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    bio TEXT,
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- tb_post: Posts table (content with relationships, write-side)
-- Trinity Pattern: pk_post (integer PK) + id (UUID for API) + fk_author (integer FK to author)
CREATE TABLE tb_post (
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

-- tb_comment: Comments table (nested relationships, write-side)
-- Trinity Pattern: pk_comment (integer PK) + id (UUID for API) + fk_post/fk_author (integer FKs)
CREATE TABLE tb_comment (
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

-- Categories/Tags (many-to-many relationships)
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE post_categories (
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, category_id)
);

-- Followers/Following (social features)
CREATE TABLE user_follows (
    follower_id UUID REFERENCES users(id) ON DELETE CASCADE,
    following_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (follower_id, following_id),
    CHECK (follower_id != following_id) -- can't follow yourself
);

-- Likes/Reactions
CREATE TABLE post_likes (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    reaction_type VARCHAR(20) DEFAULT 'like' CHECK (reaction_type IN ('like', 'love', 'laugh', 'angry')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, post_id)
);

-- Profiles/Extended user data (JSONB for flexibility)
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    profile_data JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance (critical for benchmarking)
-- Trinity Pattern indexes: use integer FKs for better performance than UUID
CREATE INDEX idx_tb_post_fk_user ON tb_post(fk_user);
CREATE INDEX idx_tb_post_status ON tb_post(status);
CREATE INDEX idx_tb_post_published_at ON tb_post(published_at);
CREATE INDEX idx_tb_comment_fk_post ON tb_comment(fk_post);
CREATE INDEX idx_tb_comment_fk_user ON tb_comment(fk_user);
CREATE INDEX idx_tb_comment_fk_parent ON tb_comment(fk_parent);
-- API UUID indexes for lookups by id
CREATE INDEX idx_tb_user_id ON tb_user(id);
CREATE INDEX idx_tb_post_id ON tb_post(id);
CREATE INDEX idx_tb_comment_id ON tb_comment(id);
CREATE INDEX idx_user_follows_follower ON user_follows(follower_id);
CREATE INDEX idx_user_follows_following ON user_follows(following_id);
CREATE INDEX idx_post_likes_post ON post_likes(post_id);
CREATE INDEX idx_post_categories_category ON post_categories(category_id);

-- JSONB indexes for advanced queries
CREATE INDEX idx_user_profiles_data ON user_profiles USING GIN (profile_data);

-- Denormalized Table Views (tv_*) for FraiseQL performance testing
-- These follow the printoptim_backend pattern of denormalized JSON data

-- tv_post: Denormalized posts with embedded author data
CREATE TABLE tv_post (
    id UUID PRIMARY KEY,
    identifier TEXT,
    author_id UUID,
    title TEXT,
    content TEXT,
    status TEXT,
    published BOOLEAN,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    data JSONB
);

-- Populate tv_post with denormalized data
INSERT INTO tv_post (id, identifier, author_id, title, content, status, published, created_at, updated_at, data)
SELECT
    p.id,
    'post-' || p.id::text as identifier,
    p.author_id,
    p.title,
    p.content,
    p.status,
    CASE WHEN p.status = 'published' THEN true ELSE false END as published,
    p.created_at,
    p.updated_at,
    jsonb_build_object(
        'id', p.id,
        'title', p.title,
        'content', p.content,
        'published', CASE WHEN p.status = 'published' THEN true ELSE false END,
        'createdAt', p.created_at,
        'updatedAt', p.updated_at,
        'author', tu.data
    ) as data
FROM tb_post p
JOIN tv_user tu ON p.author_id = tu.id;

-- Indexes for tv_post
CREATE INDEX idx_tv_post_id ON tv_post(id);
CREATE INDEX idx_tv_post_data ON tv_post USING GIN (data);
CREATE INDEX idx_tv_post_published ON tv_post(published);

COMMENT ON TABLE tv_post IS 'Denormalized table view for posts with embedded author data, following printoptim_backend patterns';

-- Sync function for tv_post: posts → tv_post
CREATE OR REPLACE FUNCTION sync_tv_post(p_id UUID)
RETURNS void AS $$
BEGIN
    -- Delete existing record
    DELETE FROM tv_post WHERE id = p_id;

    -- Insert updated record
    INSERT INTO tv_post (id, identifier, author_id, title, content, status, published, created_at, updated_at, data)
    SELECT
        p.id,
        'post-' || p.id::text as identifier,
        p.author_id,
        p.title,
        p.content,
        p.status,
        CASE WHEN p.status = 'published' THEN true ELSE false END as published,
        p.created_at,
        p.updated_at,
        jsonb_build_object(
            'id', p.id,
            'title', p.title,
            'content', p.content,
            'published', CASE WHEN p.status = 'published' THEN true ELSE false END,
            'createdAt', p.created_at,
            'updatedAt', p.updated_at,
            'author', tu.data
        ) as data
    FROM tb_post p
    JOIN tv_user tu ON p.author_id = tu.id
    WHERE p.id = p_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sync_tv_post(UUID) IS 'Sync function: posts → tv_post (call after INSERT/UPDATE/DELETE on posts)';

-- Triggers to keep tv_post synchronized
CREATE OR REPLACE FUNCTION trigger_sync_tv_post()
RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        DELETE FROM tv_post WHERE id = OLD.id;
        RETURN OLD;
    ELSE
        PERFORM sync_tv_post(NEW.id);
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to sync all posts for a user when user data changes
CREATE OR REPLACE FUNCTION sync_tv_posts_for_user(p_user_id UUID)
RETURNS void AS $$
BEGIN
    -- Update all posts for this user
    UPDATE tv_post
    SET data = jsonb_set(data, '{author}', (SELECT data FROM tv_user WHERE id = p_user_id))
    WHERE author_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Function to handle both posts and tv_user changes
CREATE OR REPLACE FUNCTION trigger_sync_tv_post_comprehensive()
RETURNS trigger AS $$
BEGIN
    -- Handle posts table changes
    IF TG_TABLE_NAME = 'posts' THEN
        IF TG_OP = 'DELETE' THEN
            DELETE FROM tv_post WHERE id = OLD.id;
            RETURN OLD;
        ELSE
            PERFORM sync_tv_post(NEW.id);
            RETURN NEW;
        END IF;
    -- Handle tv_user changes (author data updates)
    ELSIF TG_TABLE_NAME = 'tv_user' THEN
        PERFORM sync_tv_posts_for_user(NEW.id);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER trg_sync_tv_post_posts
AFTER INSERT OR UPDATE OR DELETE ON tb_post
FOR EACH ROW
EXECUTE FUNCTION trigger_sync_tv_post_comprehensive();

CREATE TRIGGER trg_sync_tv_post_users
AFTER UPDATE ON tv_user
FOR EACH ROW
EXECUTE FUNCTION trigger_sync_tv_post_comprehensive();

COMMENT ON TRIGGER trg_sync_tv_post_posts ON tb_post IS 'Automatically sync tv_post when tb_post table changes';
COMMENT ON TRIGGER trg_sync_tv_post_users ON tv_user IS 'Automatically sync tv_post author data when tv_user changes';

-- tv_user: Denormalized users table
CREATE TABLE tv_user (
    id UUID PRIMARY KEY,
    identifier TEXT,
    username TEXT,
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    bio TEXT,
    is_active BOOLEAN,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    data JSONB
);

-- Populate tv_user with denormalized data
INSERT INTO tv_user (id, identifier, username, email, first_name, last_name, bio, is_active, created_at, updated_at, data)
SELECT
    u.id,
    'user-' || u.id::text as identifier,
    u.username,
    u.email,
    u.first_name,
    u.last_name,
    u.bio,
    u.is_active,
    u.created_at,
    u.updated_at,
    jsonb_build_object(
        'id', u.id,
        'username', u.username,
        'email', u.email,
        'first_name', u.first_name,
        'last_name', u.last_name,
        'bio', u.bio,
        'is_active', u.is_active,
        'created_at', u.created_at,
        'updated_at', u.updated_at
    ) as data
FROM tb_user u;

-- Indexes for tv_user
CREATE INDEX idx_tv_user_id ON tv_user(id);
CREATE INDEX idx_tv_user_data ON tv_user USING GIN (data);

COMMENT ON TABLE tv_user IS 'Denormalized table view for users, following printoptim_backend patterns';

-- Sync function for tv_user: users → tv_user
CREATE OR REPLACE FUNCTION sync_tv_user(p_id UUID)
RETURNS void AS $$
BEGIN
    -- Delete existing record
    DELETE FROM tv_user WHERE id = p_id;

    -- Insert updated record
    INSERT INTO tv_user (id, identifier, username, email, first_name, last_name, bio, is_active, created_at, updated_at, data)
    SELECT
        u.id,
        'user-' || u.id::text as identifier,
        u.username,
        u.email,
        u.first_name,
        u.last_name,
        u.bio,
        u.is_active,
        u.created_at,
        u.updated_at,
        jsonb_build_object(
            'id', u.id,
            'username', u.username,
            'email', u.email,
            'first_name', u.first_name,
            'last_name', u.last_name,
            'bio', u.bio,
            'is_active', u.is_active,
            'created_at', u.created_at,
            'updated_at', u.updated_at
        ) as data
    FROM tb_user u
    WHERE u.id = p_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sync_tv_user(UUID) IS 'Sync function: users → tv_user (call after INSERT/UPDATE/DELETE on users)';

-- Triggers to keep tv_user synchronized
CREATE OR REPLACE FUNCTION trigger_sync_tv_user()
RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        DELETE FROM tv_user WHERE id = OLD.id;
        RETURN OLD;
    ELSE
        PERFORM sync_tv_user(NEW.id);
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tb_user table
CREATE TRIGGER trg_sync_tv_user
AFTER INSERT OR UPDATE OR DELETE ON tb_user
FOR EACH ROW
EXECUTE FUNCTION trigger_sync_tv_user();

COMMENT ON TRIGGER trg_sync_tv_user ON tb_user IS 'Automatically sync tv_user when tb_user table changes';
CREATE INDEX idx_user_profiles_settings ON user_profiles USING GIN (settings);

-- Partial indexes for common queries
CREATE INDEX idx_posts_published ON posts(published_at) WHERE status = 'published';
CREATE INDEX idx_comments_approved ON comments(created_at) WHERE is_approved = true;

-- Views for common query patterns (simulating jsonb_ivm/pg_tview functionality)
CREATE VIEW user_stats AS
SELECT
    u.id,
    u.username,
    COUNT(DISTINCT p.id) as post_count,
    COUNT(DISTINCT c.id) as comment_count,
    COUNT(DISTINCT uf.follower_id) as follower_count,
    COUNT(DISTINCT pl.user_id) as like_count
FROM users u
LEFT JOIN posts p ON u.id = p.author_id AND p.status = 'published'
LEFT JOIN comments c ON u.id = c.author_id AND c.is_approved = true
LEFT JOIN user_follows uf ON u.id = uf.following_id
LEFT JOIN post_likes pl ON u.id = pl.user_id
GROUP BY u.id, u.username;

-- Materialized view for complex aggregations (simulating incremental maintenance)
CREATE MATERIALIZED VIEW post_popularity AS
SELECT
    p.id,
    p.title,
    u.username as author,
    COUNT(DISTINCT pl.user_id) as like_count,
    COUNT(DISTINCT c.id) as comment_count,
    p.published_at
FROM posts p
JOIN users u ON p.author_id = u.id
LEFT JOIN post_likes pl ON p.id = pl.post_id
LEFT JOIN comments c ON p.id = c.post_id AND c.is_approved = true
WHERE p.status = 'published'
GROUP BY p.id, p.title, u.username, p.published_at;

CREATE UNIQUE INDEX idx_post_popularity_id ON post_popularity(id);
CREATE INDEX idx_post_popularity_author ON post_popularity(author);
CREATE INDEX idx_post_popularity_published ON post_popularity(published_at DESC);

-- Function to refresh materialized view (simulating IVM)
CREATE OR REPLACE FUNCTION refresh_post_popularity()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY post_popularity;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic updates (simulating IVM triggers)
CREATE OR REPLACE FUNCTION update_post_popularity()
RETURNS trigger AS $$
BEGIN
    -- In a real IVM system, this would be much more efficient
    -- For now, we'll refresh the entire view (not ideal for benchmarking)
    PERFORM refresh_post_popularity();
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to maintain view freshness
CREATE TRIGGER trigger_post_popularity_posts
    AFTER INSERT OR UPDATE OR DELETE ON posts
    FOR EACH STATEMENT EXECUTE FUNCTION update_post_popularity();

CREATE TRIGGER trigger_post_popularity_likes
    AFTER INSERT OR UPDATE OR DELETE ON post_likes
    FOR EACH STATEMENT EXECUTE FUNCTION update_post_popularity();

CREATE TRIGGER trigger_post_popularity_comments
    AFTER INSERT OR UPDATE OR DELETE ON comments
    FOR EACH STATEMENT EXECUTE FUNCTION update_post_popularity();