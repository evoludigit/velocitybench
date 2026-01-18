-- PostGraphile Framework Extensions
-- These are PostGraphile-specific smart tags and configurations
-- Applied ONLY to the postgraphile_test database
-- The Trinity Pattern tables are already created by schema-template.sql

SET search_path TO benchmark, public;

-- ============================================================================
-- POSTGRAPHILE SMART TAGS
-- ============================================================================
-- Smart tags control how PostGraphile exposes the schema to GraphQL
-- @omit all          = Hide field from GraphQL completely
-- @omit create,update = Hide from mutations but allow in queries
-- @type              = Override GraphQL type name

-- ============================================================================
-- tb_user Smart Tags
-- ============================================================================

-- Rename table from TbUser to User in GraphQL
COMMENT ON TABLE benchmark.tb_user IS E'@name User\nUser account';

-- Hide internal primary key from GraphQL API
COMMENT ON COLUMN benchmark.tb_user.pk_user IS E'@omit all\nInternal primary key, use id instead';

-- Expose id (UUID) to GraphQL API as the identifier
COMMENT ON COLUMN benchmark.tb_user.id IS 'Public identifier (UUID)';

-- ============================================================================
-- tb_post Smart Tags
-- ============================================================================

-- Rename table from TbPost to Post in GraphQL
COMMENT ON TABLE benchmark.tb_post IS E'@name Post\nBlog post';

-- Hide internal primary key
COMMENT ON COLUMN benchmark.tb_post.pk_post IS E'@omit all\nInternal primary key, use id instead';

-- Hide internal foreign key to author (expose through relation instead)
COMMENT ON COLUMN benchmark.tb_post.fk_author IS E'@omit all\nUse author relation instead';

-- Expose id as the public identifier
COMMENT ON COLUMN benchmark.tb_post.id IS 'Public identifier (UUID)';

-- ============================================================================
-- tb_comment Smart Tags
-- ============================================================================

-- Rename table from TbComment to Comment in GraphQL
COMMENT ON TABLE benchmark.tb_comment IS E'@name Comment\nPost comment';

-- Hide internal primary key
COMMENT ON COLUMN benchmark.tb_comment.pk_comment IS E'@omit all\nInternal primary key, use id instead';

-- Hide internal foreign keys (expose through relations instead)
COMMENT ON COLUMN benchmark.tb_comment.fk_post IS E'@omit all\nUse post relation instead';
COMMENT ON COLUMN benchmark.tb_comment.fk_author IS E'@omit all\nUse author relation instead';
COMMENT ON COLUMN benchmark.tb_comment.fk_parent IS E'@omit all\nUse parentComment relation instead';

-- Expose id as the public identifier
COMMENT ON COLUMN benchmark.tb_comment.id IS 'Public identifier (UUID)';

-- ============================================================================
-- PostGraphile Computed Columns (Optional Enhancement)
-- ============================================================================
-- These are examples of computed columns that PostGraphile can expose
-- Enable these if testing computed field performance

-- Computed column: User follower count
-- CREATE OR REPLACE FUNCTION benchmark.tb_user_follower_count(user benchmark.tb_user)
-- RETURNS INTEGER AS $$
--   SELECT COUNT(*) FROM user_follows WHERE following_id = user.id;
-- $$ LANGUAGE SQL STABLE;

-- Computed column: Post like count
-- CREATE OR REPLACE FUNCTION benchmark.tb_post_like_count(post benchmark.tb_post)
-- RETURNS INTEGER AS $$
--   SELECT COUNT(*) FROM post_likes WHERE post_id = post.id;
-- $$ LANGUAGE SQL STABLE;

-- Computed column: Post comment count (approved only)
-- CREATE OR REPLACE FUNCTION benchmark.tb_post_comment_count(post benchmark.tb_post)
-- RETURNS INTEGER AS $$
--   SELECT COUNT(*) FROM tb_comment WHERE fk_post = post.pk_post AND is_approved = true;
-- $$ LANGUAGE SQL STABLE;

-- ============================================================================
-- PostGraphile Relations (Named for GraphQL)
-- ============================================================================
-- PostGraphile automatically creates relations based on foreign keys
-- These naming conventions help with GraphQL naming clarity

-- No additional configuration needed here - PostGraphile handles relation naming
-- based on the foreign key structure and smart tags above

-- The relations automatically created will be:
-- tb_user.author -> references author of posts/comments
-- tb_post.author -> references the author (via fk_author)
-- tb_comment.author -> references the author
-- tb_comment.post -> references the post
-- tb_comment.parentComment -> references parent comment (via fk_parent)

-- ============================================================================
-- NOTES
-- ============================================================================
-- PostGraphile will:
-- 1. Expose only the fields NOT marked with @omit
-- 2. Create relations based on foreign keys
-- 3. Allow queries on all exposed tables
-- 4. Create mutations for all tables (create, update, delete)
-- 5. Expose computed columns (if any are defined above)
--
-- The Trinity Pattern is maintained:
-- - pk_* fields are hidden (@omit all)
-- - fk_* fields are hidden (@omit all), relations replace them
-- - id (UUID) fields are the public API identifiers
--
-- Framework-specific features (views, functions) are NOT exposed by default
-- unless explicitly tagged with PostGraphile directives.
