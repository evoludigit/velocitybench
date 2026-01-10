-- PostGraphile-specific schema for benchmark testing
-- Extends the shared benchmark schema with PostGraphile-specific smart tags
-- This schema is designed for PostGraphile's zero-code GraphQL generation
--
-- Architecture:
-- - Uses the Trinity Pattern: pk_* (internal INT PKs), id (UUID for API), fk_* (internal INT FKs)
-- - Smart tags (@omit) control what's exposed in the GraphQL API
-- - Internal keys (pk_*, fk_*) are hidden from GraphQL clients
-- - Timestamps are read-only (hidden from mutations)

-- Ensure we're working in the right schema
SET search_path TO benchmark, public;

-- ============================================================================
-- SMART TAGS: Configure PostGraphile column visibility
-- ============================================================================

-- tb_user table smart tags
COMMENT ON COLUMN tb_user.pk_user IS E'@omit all\nInternal primary key for database performance.';
COMMENT ON COLUMN tb_user.created_at IS E'@omit create,update\nTimestamp when user was created (read-only, server-managed).';
COMMENT ON COLUMN tb_user.updated_at IS E'@omit create,update\nTimestamp when user was last updated (read-only, server-managed).';

-- tb_post table smart tags
COMMENT ON COLUMN tb_post.pk_post IS E'@omit all\nInternal primary key for database performance.';
COMMENT ON COLUMN tb_post.fk_user IS E'@omit all\nInternal foreign key - use "author" relation instead.';
COMMENT ON COLUMN tb_post.created_at IS E'@omit create,update\nTimestamp when post was created (read-only, server-managed).';
COMMENT ON COLUMN tb_post.updated_at IS E'@omit create,update\nTimestamp when post was last updated (read-only, server-managed).';

-- tb_comment table smart tags
COMMENT ON COLUMN tb_comment.pk_comment IS E'@omit all\nInternal primary key for database performance.';
COMMENT ON COLUMN tb_comment.fk_post IS E'@omit all\nInternal foreign key - use "post" relation instead.';
COMMENT ON COLUMN tb_comment.fk_user IS E'@omit all\nInternal foreign key - use "author" relation instead.';
COMMENT ON COLUMN tb_comment.fk_parent IS E'@omit all\nInternal foreign key - use "parentComment" relation instead.';
COMMENT ON COLUMN tb_comment.created_at IS E'@omit create,update\nTimestamp when comment was created (read-only, server-managed).';
COMMENT ON COLUMN tb_comment.updated_at IS E'@omit create,update\nTimestamp when comment was last updated (read-only, server-managed).';

-- ============================================================================
-- TABLE DESCRIPTIONS: Populate in schema introspection
-- ============================================================================

COMMENT ON TABLE tb_user IS 'User accounts - core entity. Exposed through UUID "id" field.';
COMMENT ON TABLE tb_post IS 'Posts/articles created by users. Exposed through UUID "id" field. Author accessible via "author" relation.';
COMMENT ON TABLE tb_comment IS 'Comments on posts with reply threads. Exposed through UUID "id" field. Relations: post, author, parentComment.';

-- ============================================================================
-- COLUMN DESCRIPTIONS: Public API documentation
-- ============================================================================

-- tb_user descriptions
COMMENT ON COLUMN tb_user.id IS 'Unique public identifier (UUID) - use for API queries.';
COMMENT ON COLUMN tb_user.username IS 'Unique username for authentication and display.';
COMMENT ON COLUMN tb_user.email IS 'Unique email address - must be valid format.';
COMMENT ON COLUMN tb_user.first_name IS 'User first name (optional).';
COMMENT ON COLUMN tb_user.last_name IS 'User last name (optional).';
COMMENT ON COLUMN tb_user.bio IS 'User biography or description (optional).';
COMMENT ON COLUMN tb_user.avatar_url IS 'URL to user avatar image (optional).';
COMMENT ON COLUMN tb_user.is_active IS 'Whether the user account is active and can log in.';

-- tb_post descriptions
COMMENT ON COLUMN tb_post.id IS 'Unique public identifier (UUID) - use for API queries.';
COMMENT ON COLUMN tb_post.title IS 'Post title - required for creation.';
COMMENT ON COLUMN tb_post.content IS 'Post body content (markdown or plain text).';
COMMENT ON COLUMN tb_post.excerpt IS 'Short excerpt or summary of post (optional).';
COMMENT ON COLUMN tb_post.status IS 'Publication status: draft, published, or archived.';
COMMENT ON COLUMN tb_post.published_at IS 'Timestamp when post was published (optional).';

-- tb_comment descriptions
COMMENT ON COLUMN tb_comment.id IS 'Unique public identifier (UUID) - use for API queries.';
COMMENT ON COLUMN tb_comment.content IS 'Comment text - required for creation.';
COMMENT ON COLUMN tb_comment.is_approved IS 'Whether comment is approved and visible (moderation flag).';

-- ============================================================================
-- INDEXES: Optimized for both internal and API access patterns
-- ============================================================================

-- Indexes on internal integer PKs (for fast database joins)
-- These are already created in the base schema, but documented here for reference

-- Indexes on public UUID identifiers (for API lookups)
-- These are already created in the base schema, but documented here for reference

-- Additional indexes for GraphQL query patterns
CREATE INDEX IF NOT EXISTS idx_tb_post_status_published ON tb_post(status, published_at DESC)
  WHERE status = 'published';

CREATE INDEX IF NOT EXISTS idx_tb_comment_approved_created ON tb_comment(is_approved, created_at DESC)
  WHERE is_approved = true;

-- ============================================================================
-- NOTES FOR POSTGRAPHILE INTEGRATION
-- ============================================================================
--
-- Trinity Pattern Implementation:
-- ============================================================================
--
-- DATABASE LAYER:
-- - pk_user, pk_post, pk_comment: SERIAL INTEGER primary keys
--   → Fast for joins and indexes
--   → Hidden from GraphQL schema via @omit all
--
-- - fk_user, fk_post, fk_parent: INTEGER foreign keys
--   → Fast for relationships and constraints
--   → Hidden from GraphQL schema via @omit all
--   → PostGraphile infers Relations from FK constraints
--
-- - id: UUID UNIQUE columns
--   → Public identifiers for distributed systems
--   → Exposed in GraphQL as the primary identifier
--   → Used in API query parameters: userById(id: "...")
--
-- GRAPHQL LAYER (PostGraphile Generated):
-- ============================================================================
--
-- Exposed fields (visible in GraphQL schema):
--   User: id, username, email, firstName, lastName, bio, avatarUrl, isActive
--   Post: id, title, content, excerpt, status, publishedAt, author (relation)
--   Comment: id, content, isApproved, post (relation), author (relation), parentComment (relation)
--
-- Hidden fields (NOT visible in GraphQL schema):
--   - pk_* columns (internal primary keys) - @omit all
--   - fk_* columns (internal foreign keys) - @omit all
--   - created_at, updated_at - @omit create,update (read-only in mutations)
--
-- Relations (inferred from FK constraints):
--   Post.author → User (via hidden fk_user → tb_user.pk_user)
--   Comment.post → Post (via hidden fk_post → tb_post.pk_post)
--   Comment.author → User (via hidden fk_user → tb_user.pk_user)
--   Comment.parentComment → Comment (via hidden fk_parent → tb_comment.pk_comment)
--
-- API Usage:
-- ============================================================================
--
-- Correct (UUID identifiers):
--   query { userById(id: "550e8400-e29b-41d4-a716-446655440000") { id username } }
--
-- Not available (integer identifiers hidden):
--   query { userById(id: 1) { id username } }  ← Would fail: pk_user is @omit all
--
-- To access author's data through a post:
--   query { postById(id: "...") { author { username email } } }  ← Via relation
--   NOT: query { postById(id: "...") { fkUser } }  ← fkUser is @omit all
--
-- ============================================================================
