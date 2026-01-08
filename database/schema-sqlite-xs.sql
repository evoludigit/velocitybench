-- XS Test Database Schema for SQLite
-- Mirrors PostgreSQL structure for testing generation pipeline
-- Optimized SQLite pragmas for fast bulk inserts

-- Performance tuning pragmas
PRAGMA journal_mode = MEMORY;
PRAGMA synchronous = OFF;
PRAGMA cache_size = 100000;
PRAGMA temp_store = MEMORY;

-- Users table
CREATE TABLE users (
    pk_user INTEGER PRIMARY KEY,
    id TEXT UNIQUE NOT NULL,
    identifier TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    bio TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_users_id ON users(id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- Posts table
CREATE TABLE posts (
    pk_post INTEGER PRIMARY KEY,
    id TEXT UNIQUE NOT NULL,
    identifier TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    fk_author INTEGER NOT NULL,
    published INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (fk_author) REFERENCES users(pk_user) ON DELETE CASCADE
);

CREATE INDEX idx_posts_id ON posts(id);
CREATE INDEX idx_posts_author ON posts(fk_author);
CREATE INDEX idx_posts_published ON posts(published);

-- Comments table
CREATE TABLE comments (
    pk_comment INTEGER PRIMARY KEY,
    id TEXT UNIQUE NOT NULL,
    identifier TEXT,
    content TEXT NOT NULL,
    fk_post INTEGER NOT NULL,
    fk_author INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (fk_post) REFERENCES posts(pk_post) ON DELETE CASCADE,
    FOREIGN KEY (fk_author) REFERENCES users(pk_user) ON DELETE CASCADE
);

CREATE INDEX idx_comments_id ON comments(id);
CREATE INDEX idx_comments_post ON comments(fk_post);
CREATE INDEX idx_comments_author ON comments(fk_author);
CREATE INDEX idx_comments_post_author ON comments(fk_post, fk_author);

-- User follows table (many-to-many)
CREATE TABLE user_follows (
    fk_follower INTEGER NOT NULL,
    fk_following INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (fk_follower, fk_following),
    FOREIGN KEY (fk_follower) REFERENCES users(pk_user) ON DELETE CASCADE,
    FOREIGN KEY (fk_following) REFERENCES users(pk_user) ON DELETE CASCADE,
    CHECK (fk_follower != fk_following)
);

CREATE INDEX idx_follows_follower ON user_follows(fk_follower);
CREATE INDEX idx_follows_following ON user_follows(fk_following);

-- Post likes/reactions table
CREATE TABLE post_likes (
    fk_user INTEGER NOT NULL,
    fk_post INTEGER NOT NULL,
    reaction_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (fk_user, fk_post),
    FOREIGN KEY (fk_user) REFERENCES users(pk_user) ON DELETE CASCADE,
    FOREIGN KEY (fk_post) REFERENCES posts(pk_post) ON DELETE CASCADE,
    CHECK (reaction_type IN ('like', 'love', 'laugh', 'angry', 'sad'))
);

CREATE INDEX idx_likes_user ON post_likes(fk_user);
CREATE INDEX idx_likes_post ON post_likes(fk_post);
CREATE INDEX idx_likes_reaction ON post_likes(reaction_type);
