-- Sample data for GraphQL framework benchmarking
-- Creates a realistic dataset with relationships for comprehensive testing

SET search_path TO benchmark, public;

-- Insert test users (100 users for good distribution)
INSERT INTO tb_user (id, email, username, first_name, last_name, bio, is_active) VALUES
    ('11111111-1111-1111-1111-111111111111', 'alice@example.com', 'alice', 'Alice', 'Johnson', 'Software engineer passionate about GraphQL', true),
    ('22222222-2222-2222-2222-222222222222', 'bob@example.com', 'bob', 'Bob', 'Smith', 'Database administrator and PostgreSQL enthusiast', true),
    ('33333333-3333-3333-3333-333333333333', 'charlie@example.com', 'charlie', 'Charlie', 'Brown', 'Full-stack developer', true),
    ('44444444-4444-4444-4444-444444444444', 'diana@example.com', 'diana', 'Diana', 'Prince', 'API designer and architect', true),
    ('55555555-5555-5555-5555-555555555555', 'eve@example.com', 'eve', 'Eve', 'Adams', 'DevOps engineer', true);

-- Generate more users programmatically (95 more for total of 100)
INSERT INTO tb_user (email, username, first_name, last_name, bio, is_active)
SELECT
    'user' || i || '@example.com',
    'user' || i,
    'First' || i,
    'Last' || i,
    'Bio for user ' || i,
    true
FROM generate_series(6, 100) AS i;

-- Insert categories
INSERT INTO categories (name, slug, description) VALUES
    ('Technology', 'technology', 'Posts about technology and programming'),
    ('GraphQL', 'graphql', 'GraphQL related content'),
    ('Databases', 'databases', 'Database technologies and best practices'),
    ('Performance', 'performance', 'Performance optimization and benchmarking'),
    ('Architecture', 'architecture', 'System design and architecture patterns');

-- Insert posts (500 posts total)
INSERT INTO tb_post (author_id, title, content, excerpt, status, published_at)
SELECT
    (SELECT id FROM tb_user ORDER BY random() LIMIT 1),
    'Post Title ' || i,
    'This is the content of post ' || i || '. It contains some sample text for benchmarking GraphQL queries and testing different access patterns.',
    'Excerpt for post ' || i,
    'published',
    NOW() - (random() * INTERVAL '365 days')
FROM generate_series(1, 500) AS i;

-- Insert comments (2000 comments total, some nested)
INSERT INTO tb_comment (post_id, author_id, parent_id, content, is_approved)
SELECT
    (SELECT id FROM tb_post ORDER BY random() LIMIT 1),
    (SELECT id FROM tb_user ORDER BY random() LIMIT 1),
    CASE WHEN random() < 0.1 THEN (SELECT id FROM tb_comment ORDER BY random() LIMIT 1) ELSE NULL END,
    'This is comment ' || i || ' with some content for testing nested relationships.',
    true
FROM generate_series(1, 2000) AS i;

-- Assign categories to posts (many-to-many relationships)
INSERT INTO post_categories (post_id, category_id)
SELECT DISTINCT
    p.id,
    c.id
FROM tb_post p
CROSS JOIN categories c
WHERE random() < 0.3; -- 30% chance of category assignment

-- Create follower relationships (social graph)
INSERT INTO user_follows (follower_id, following_id)
SELECT DISTINCT
    u1.id,
    u2.id
FROM tb_user u1
CROSS JOIN tb_user u2
WHERE u1.id != u2.id AND random() < 0.1; -- 10% chance of following

-- Add likes to posts
INSERT INTO post_likes (user_id, post_id, reaction_type)
SELECT DISTINCT
    u.id,
    p.id,
    CASE
        WHEN random() < 0.7 THEN 'like'
        WHEN random() < 0.9 THEN 'love'
        ELSE 'laugh'
    END
FROM tb_user u
CROSS JOIN tb_post p
WHERE random() < 0.2; -- 20% chance of liking

-- Add user profiles with JSONB data
INSERT INTO user_profiles (user_id, profile_data, settings, metadata)
SELECT
    id,
    jsonb_build_object(
        'website', 'https://' || username || '.com',
        'location', 'City ' || (random() * 100)::int,
        'interests', jsonb_build_array('GraphQL', 'PostgreSQL', 'Performance')
    ),
    jsonb_build_object(
        'theme', CASE WHEN random() < 0.5 THEN 'dark' ELSE 'light' END,
        'notifications', jsonb_build_object('email', true, 'push', false),
        'privacy', jsonb_build_object('profile_visible', true, 'posts_public', true)
    ),
    jsonb_build_object(
        'last_login', NOW() - (random() * INTERVAL '30 days'),
        'login_count', (random() * 100)::int,
        'account_status', 'active'
    )
FROM tb_user;

-- Refresh materialized view to ensure data consistency
SELECT refresh_post_popularity();

-- Create some specific test data for predictable benchmarking
-- "Popular user" with many posts and followers
UPDATE tb_user SET bio = 'Popular blogger with extensive content' WHERE id = '11111111-1111-1111-1111-111111111111';

-- Add many posts for the popular user
INSERT INTO tb_post (author_id, title, content, status, published_at)
SELECT
    '11111111-1111-1111-1111-111111111111',
    'Popular Post ' || i,
    'Content for popular post ' || i,
    'published',
    NOW() - (i * INTERVAL '1 day')
FROM generate_series(1, 50) AS i;

-- Make many users follow the popular user
INSERT INTO user_follows (follower_id, following_id)
SELECT
    u.id,
    '11111111-1111-1111-1111-111111111111'
FROM tb_user u
WHERE u.id != '11111111-1111-1111-1111-111111111111'
AND NOT EXISTS (
    SELECT 1 FROM user_follows uf
    WHERE uf.follower_id = u.id AND uf.following_id = '11111111-1111-1111-1111-111111111111'
)
ORDER BY random()
LIMIT 30;

-- Add many likes to popular posts
INSERT INTO post_likes (user_id, post_id)
SELECT DISTINCT
    u.id,
    p.id
FROM tb_user u
CROSS JOIN tb_post p
WHERE p.author_id = '11111111-1111-1111-1111-111111111111'
ORDER BY u.id, p.id
LIMIT 200;

-- Final refresh of materialized view
SELECT refresh_post_popularity();

-- Populate denormalized tv_ tables for FraiseQL performance testing
-- These will be automatically populated by triggers, but we do an initial sync

-- Sync all users to tv_user first (tv_post depends on tv_user)
SELECT sync_tv_user(id) FROM tb_user;

-- Sync all posts to tv_post (now that tv_user data is available)
SELECT sync_tv_post(id) FROM tb_post;