-- FraiseQL CQRS Schema Extensions
-- Additional tables for social features (follows, likes) and data generation

SET search_path TO benchmark, public;

-- ============================================================================
-- USER FOLLOWS TABLE (command side)
-- ============================================================================

CREATE TABLE benchmark.tb_user_follows (
    fk_follower INT NOT NULL REFERENCES benchmark.tb_user(pk_user) ON DELETE CASCADE,
    fk_following INT NOT NULL REFERENCES benchmark.tb_user(pk_user) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (fk_follower, fk_following),
    CHECK (fk_follower != fk_following)
);

CREATE INDEX idx_tb_user_follows_follower ON benchmark.tb_user_follows(fk_follower);
CREATE INDEX idx_tb_user_follows_following ON benchmark.tb_user_follows(fk_following);
CREATE INDEX idx_tb_user_follows_created ON benchmark.tb_user_follows(created_at DESC);

COMMENT ON TABLE benchmark.tb_user_follows IS 'Command side: User follow relationships';

-- ============================================================================
-- POST LIKE TABLE (command side)
-- ============================================================================

CREATE TABLE benchmark.tb_post_like (
    fk_user INT NOT NULL REFERENCES benchmark.tb_user(pk_user) ON DELETE CASCADE,
    fk_post INT NOT NULL REFERENCES benchmark.tb_post(pk_post) ON DELETE CASCADE,
    reaction_type VARCHAR(20) DEFAULT 'like' CHECK (reaction_type IN ('like', 'love', 'laugh', 'angry')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (fk_user, fk_post)
);

CREATE INDEX idx_tb_post_like_user ON benchmark.tb_post_like(fk_user);
CREATE INDEX idx_tb_post_like_post ON benchmark.tb_post_like(fk_post);
CREATE INDEX idx_tb_post_like_created ON benchmark.tb_post_like(created_at DESC);
CREATE INDEX idx_tb_post_like_reaction ON benchmark.tb_post_like(reaction_type);

COMMENT ON TABLE benchmark.tb_post_like IS 'Command side: Post reactions/likes';
