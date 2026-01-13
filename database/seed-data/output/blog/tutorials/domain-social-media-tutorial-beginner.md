```markdown
---
title: "Social Media Domain Patterns: Building Scalable Backends for User Networks"
date: 2024-04-15
author: "Alex Chen"
description: "A beginner-friendly guide to implementing common social media patterns like user relationships, feeds, and content moderation. Learn how to model complex interactions while avoiding common pitfalls."
tags: ["backend", "database design", "API design", "social media", "domain patterns"]
---

# Social Media Domain Patterns: Building Scalable Backends for User Networks

Social media platforms are one of the most challenging domains for backend engineers to architect. They require handling complex user relationships, real-time content delivery, and decentralized content moderation at scale—all while ensuring scalability, consistency, and a great user experience.

If you've ever wondered *how* services like Twitter/X, Reddit, or LinkedIn store and manage their core data—like user follow relationships, activity feeds, or content moderation—I’m about to break it down into practical patterns with code examples. Whether you're building a small community platform or optimizing an existing one, these patterns will give you a solid foundation.

By the end of this post, you’ll have a clear understanding of how to:
- Model user relationships efficiently (followers, friends, networks)
- Optimize content delivery with activity feeds
- Implement content moderation and reporting
- Scale these components with database optimizations

Let’s dive in.

---

## The Problem: Why Social Media Backends Are Harder Than They Look

Building a "simple" social media app often starts with just a few tables: `users` and `posts`. But reality hits fast when you add even basic features like:

1. **User Relationships**: How do you model "following" efficiently? A naive `user_follows_another_user` table will bloat your database as users gain followers. At scale, this becomes a performance bottleneck for queries like "Who am I following?" or "Who follows me?"

2. **Activity Feeds**: Generating a personalized feed for every user in real-time is computationally expensive. Should you use a time-based approach? A social graph-based approach? Or a hybrid?

3. **Content Moderation**: How do you tag, report, or hide content that violates community guidelines? Should you modify posts in-place or use a separate "moderation layer"? What if multiple reports come in for the same content?

4. **Real-Time Updates**: Users expect near-instant updates to their feeds. Should you use polling? WebSockets? Server-Sent Events (SSE)? And how do you handle offline users?

5. **Data Growth**: Social media platforms store vast amounts of user-generated content. How do you optimize for "cold" data (e.g., posts from 2019) that is rarely accessed?

Without proper patterns, you’ll end up with:
- Slow queries due to inefficient relationship tables
- Feed generation that takes too long or returns stale data
- Overly complex or hard-to-maintain moderation logic
- Scaling issues as your user base grows

---

## The Solution: Core Social Media Domain Patterns

To tackle these challenges, we’ll explore four key patterns, each with its own tradeoffs:

1. **User Relationships Pattern**: Efficiently model bidirectional follow/friend relationships.
2. **Activity Feed Pattern**: Generate personalized feeds using graph traversal.
3. **Content Moderation Pattern**: Decouple content moderation from the main data model.
4. **Feed Optimization Pattern**: Cache and batch feed updates for scalability.

---

## Pattern 1: User Relationships Pattern

### The Problem
In a typical `users` table, you might have columns like `id`, `username`, `email`, etc. But how do you model "following"? A naive approach is to add a `follows` column to the `users` table:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    follows BOOLEAN DEFAULT FALSE  -- Naive and incorrect!
);
```

This doesn’t work because:
- It’s ambiguous (does it mean "I follow myself"?).
- It doesn’t allow for bidirectional relationships (who follows whom).
- It’s hard to query (e.g., "Who do I follow?" or "Who follows me?").

### The Solution: Bidirectional Relationship Table

Most social media platforms use a dedicated table to store relationships. For example:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL
);

CREATE TABLE follows (
    follower_id INT REFERENCES users(id),
    followee_id INT REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (follower_id, followee_id)
);
```

### Why This Works
- **Explicit**: Clearly represents that `user A` follows `user B`.
- **Bidirectional**: Easy to query both directions (e.g., "Who follows me?" is `SELECT * FROM follows WHERE followee_id = ?`).
- **Scalable**: Indexes on `follower_id` and `followee_id` make queries efficient.

### Tradeoffs
- **Storage**: For 1M users with an average of 100 followers, this table could grow large.
- **Deletion**: Soft deletes (e.g., `deleted_at`) are tricky; a full deletion requires a `DELETE` from the `follows` table.

---

## Pattern 2: Activity Feed Pattern

### The Problem
Generating a personalized feed for each user is tricky. Here are three common approaches:

1. **Time-Based Feed**: Fetch all posts from users you follow, ordered by recency.
   - Pros: Simple to implement.
   - Cons: Inefficient for large networks (e.g., Twitter’s 500M+ users).

2. **Graph-Based Feed**: Traverse the social graph to find posts from followed users and their close connections.
   - Pros: More personalized.
   - Cons: Expensive for large graphs; can include "too much" content.

3. **Hybrid Feed**: Combine time-based and graph-based approaches (e.g., Twitter’s algorithmic feed).

### The Solution: Hybrid Feed Pattern

For most small-to-medium platforms, a hybrid approach works well. Here’s how:

1. **Store Posts**: Each post has a `user_id` and `created_at` timestamp.
   ```sql
   CREATE TABLE posts (
       id SERIAL PRIMARY KEY,
       user_id INT REFERENCES users(id),
       content TEXT,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   ```

2. **Indexed Feeds**: For each user, store a list of post IDs they’ve created, ordered by `created_at`.
   ```sql
   CREATE TABLE user_posts (
       user_id INT REFERENCES users(id),
       post_id INT REFERENCES posts(id),
       created_at TIMESTAMP WITH TIME ZONE,
       PRIMARY KEY (user_id, post_id)
   );
   ```

3. **Feed Generation**: For a user’s feed, query:
   ```sql
   SELECT p.*
   FROM posts p
   JOIN user_posts up ON p.id = up.post_id
   WHERE up.user_id IN (
       -- Posts from users I follow
       SELECT followee_id
       FROM follows
       WHERE follower_id = ? UNION ALL
       -- My own posts
       SELECT id FROM users WHERE id = ?
   )
   ORDER BY p.created_at DESC
   LIMIT 50;
   ```

### Optimization: Cursor-Based Pagination
For social media apps, pagination is critical. Use `LIMIT` with a `post_id` cursor to fetch the next batch of posts:
```sql
SELECT p.*
FROM posts p
JOIN user_posts up ON p.id = up.post_id
WHERE up.user_id IN (
   SELECT followee_id FROM follows WHERE follower_id = ? UNION ALL
   SELECT id FROM users WHERE id = ?
)
AND p.id < ?  -- Last seen post ID
ORDER BY p.created_at DESC
LIMIT 50;
```

### Tradeoffs
- **Query Cost**: Joining `follows` and `posts` can be slow as users gain more followers.
- **Data Duplication**: `user_posts` is redundant but speeds up feed queries.

---

## Pattern 3: Content Moderation Pattern

### The Problem
Moderating content (e.g., flagging posts, hiding them) requires careful design. Common pitfalls:
- **In-Place Updates**: Modifying posts directly violates the principle of least surprise (users may expect posts to persist).
- **No Moderation Context**: Without metadata, it’s hard to track why a post was moderated.

### The Solution: Decoupled Moderation Table

Use a separate `moderation` table to track actions without altering the main `posts` table:

```sql
CREATE TABLE moderation (
    id SERIAL PRIMARY KEY,
    post_id INT REFERENCES posts(id),
    user_id INT REFERENCES users(id),  -- Who reported/moderated it?
    action VARCHAR(50) NOT NULL,       -- e.g., 'flag', 'hide', 'delete'
    status VARCHAR(50) DEFAULT 'pending',  -- e.g., 'pending', 'approved', 'rejected'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT                      -- Why was this moderated?
);
```

### How to Flag a Post
```sql
INSERT INTO moderation (post_id, user_id, action, notes)
VALUES (123, 456, 'flag', 'Contains hate speech');
```

### How to Hide a Post from a User
Instead of deleting or updating the `posts` table, add a `hidden_from` table to track visibility per user:
```sql
CREATE TABLE post_hides (
    post_id INT REFERENCES posts(id),
    user_id INT REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (post_id, user_id)
);
```

Now, when generating a feed, exclude posts hidden from the current user:
```sql
SELECT p.*
FROM posts p
WHERE NOT EXISTS (
    SELECT 1 FROM post_hides ph WHERE ph.post_id = p.id AND ph.user_id = ?
)
-- Rest of the feed query
;
```

### Tradeoffs
- **Complexity**: More tables to maintain.
- **Flexibility**: Easy to add new actions (e.g., 'report', 'mute') without schema changes.

---

## Pattern 4: Feed Optimization Pattern

### The Problem
As your platform grows, generating feeds becomes expensive because:
- `follows` tables grow large.
- Post tables grow large.
- Queries must traverse the social graph in real-time.

### The Solution: Cached and Batch-Fed Feeds

#### 1. Pre-Generated Feeds
For users with small follow counts (e.g., <100 followers), generate feeds on-demand as in the previous pattern. For larger users, **pre-generate feeds** and update them asynchronously.

Example:
```sql
CREATE TABLE user_feeds (
    user_id INT REFERENCES users(id),
    last_updated TIMESTAMP WITH TIME ZONE,
    feed_data JSONB  -- Stores post IDs in reverse chronological order
);
```

#### 2. Batch Updates
When a user posts, update all their followers' feeds in the background:
```python
# Pseudocode for a background task
def update_followers_feeds(post_id: int):
    for follower in get_followers_of_post_user(post_id):
        # Append post_id to follower's feed
        update_user_feed(follower.id, post_id)
```

#### 3. Feed Truncation
Social media feeds are long-tail: most users rarely scroll beyond the first 50 posts. Truncate old feeds to save space:
```sql
-- Truncate feeds older than 30 days
UPDATE user_feeds
SET feed_data = JSONB_AGG(post_id)
WHERE last_updated < NOW() - INTERVAL '30 days'
GROUP BY user_id;
```

### Tradeoffs
- **Staleness**: Feeds may not be 100% up-to-date.
- **Storage**: `feed_data` grows with the number of posts.

---

## Implementation Guide: Putting It All Together

Here’s a step-by-step guide to implementing these patterns in a new social media backend:

### 1. Database Setup
Start with the core tables:
```sql
-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Follows
CREATE TABLE follows (
    follower_id INT REFERENCES users(id),
    followee_id INT REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (follower_id, followee_id)
);

-- Posts
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Moderation
CREATE TABLE moderation (
    id SERIAL PRIMARY KEY,
    post_id INT REFERENCES posts(id),
    action VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Post visibility
CREATE TABLE post_hides (
    post_id INT REFERENCES posts(id),
    user_id INT REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (post_id, user_id)
);
```

### 2. API Endpoints
Here are key endpoints to implement:

#### a. Follow a User
```python
# FastAPI example
@app.post("/follow/{followee_id}")
async def follow_user(follower_id: int, followee_id: int):
    await asyncpg.create_follow(follower_id, followee_id)
    return {"status": "success"}
```

```sql
-- SQL for follow
INSERT INTO follows (follower_id, followee_id)
VALUES ($1, $2);
```

#### b. Get Feed (Simplified)
```python
@app.get("/feed/{user_id}")
async def get_feed(user_id: int, last_post_id: int = None):
    return await asyncpg.get_feed(user_id, last_post_id)
```

```sql
-- SQL for feed (paginated)
SELECT p.*
FROM posts p
JOIN user_posts up ON p.id = up.post_id
WHERE up.user_id IN (
    SELECT followee_id FROM follows WHERE follower_id = $1 UNION ALL
    SELECT id FROM users WHERE id = $1
)
AND p.id < $2  -- last_post_id cursor
ORDER BY p.created_at DESC
LIMIT 50;
```

#### c. Flag a Post
```python
@app.post("/moderation/flag")
async def flag_post(post_id: int, user_id: int, notes: str):
    await asyncpg.flag_post(post_id, user_id, notes)
    return {"status": "success"}
```

```sql
-- SQL for flagging
INSERT INTO moderation (post_id, user_id, action, notes)
VALUES ($1, $2, 'flag', $3);
```

### 3. Background Jobs
Use a task queue (e.g., Celery or AWS Lambda) to:
- Update followers' feeds when a post is created.
- Run scheduled jobs to truncate old feeds.

Example Celery task:
```python
@app.task
def update_followers_feeds(post_id: int):
    followers = get_followers_of_post_user(post_id)
    for follower in followers:
        append_post_to_feed(follower.id, post_id)
```

---

## Common Mistakes to Avoid

1. **Not Indexing Relationships**: Forgetting to index `follows(follower_id)` or `follows(followee_id)` will make queries slow.
   - Fix: Always add indexes for foreign keys.

2. **Overfetching in Feeds**: Joining all possible tables in a feed query can bloat payloads.
   - Fix: Use subqueries or CTEs to limit data early.

3. **Blocking on Feed Generation**: Generating feeds synchronously during API requests causes timeouts.
   - Fix: Use async/background processing.

4. **Ignoring Data Growth**: Assuming your schema will stay small.
   - Fix: Design for scale (e.g., partition large tables).

5. **Hardcoding Moderation Logic**: Embedding moderation rules in the database.
   - Fix: Use a separate moderation service or API.

6. **No Feed Caching**: Regenerating feeds from scratch every time.
   - Fix: Cache feeds and update incrementally.

7. **Poor Error Handling**: Crashing when relationships or feeds are inconsistent.
   - Fix: Always handle edge cases (e.g., circular follows, deleted users).

---

## Key Takeaways

- **User Relationships**: Use a dedicated `follows` table with indexes for `follower_id` and `followee_id`.
- **Activity Feeds**: Combine time-based and graph-based approaches; optimize with pagination and cursors.
- **Content Moderation**: Decouple moderation from the main `posts` table; use separate tables for visibility rules.
- **Feed Optimization**: Pre-generate feeds for large users; batch updates to followers.
- **Scalability**: Design for data growth (e.g., partition tables, use JSONB for flexible data).
- **Async Processing**: Offload heavy operations (e.g., feed updates) to background jobs.
- **Tradeoffs**: No perfect solution—balance consistency, scalability, and simplicity.

---

## Conclusion

Building a social media backend is a journey of tradeoffs. You’ll need to balance performance, scalability, and maintainability as your platform grows. The patterns in this post provide a solid foundation, but remember:

- Start simple, then optimize. Don’t over-engineer early.
- Monitor performance. Use tools like PostgreSQL’s `EXPLAIN ANALYZE` to identify bottlenecks.
- Iterate. Social media platforms evolve—so should your backend.

With these patterns, you’re now equipped to handle the core challenges of user relationships, feeds, and moderation. Happy coding—and may your feeds always load in under 200ms! 🚀

---
### Further Reading
- [PostgreSQL Indexing Guide](https://use-the-index-luke.com/)
- [Event Sourcing for Social Media](https://martinfowler.com/eaaDev/EventSourcing.html)
- [LinkedIn’s Distributed Feed Algorithm](https://engineering.linkedin.com/distributed-systems/linkedins-feed-algorithm)
```