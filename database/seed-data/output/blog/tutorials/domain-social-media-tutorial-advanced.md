```markdown
# Building Robust Social Networks: Domain Patterns for Scalable Backends

*By [Your Name], Senior Backend Engineer*

---

## Introduction

Social media platforms are among the most complex systems in the modern web ecosystem. They’re built on domain patterns that combine data modeling, event-driven architectures, and real-time capabilities—all while managing billions of daily interactions. As a backend engineer, mastering the domain patterns that power these systems helps you design scalable, maintainable, and resilient APIs that handle everything from friend requests to viral content distribution.

This guide dives deep into *Social-Media Domain Patterns*—a collection of battle-tested techniques for building backend systems that mirror real-world interactions. We’ll cover how to model users, connections, posts, and content propagation; how to handle real-time updates efficiently; and when to prioritize consistency over eventual consistency. Along the way, we’ll examine code examples, tradeoffs, and anti-patterns to avoid.

By the end of this post, you’ll have a practical toolkit to architect any social media backend, whether you're building a niche community platform or optimizing an existing one.

---

## The Problem

Social media platforms face unique challenges that generic database or API design patterns don’t fully address:

1. **Graph-Centric Data**: Users aren’t just entities; they’re nodes in a dynamic graph of connections (followers, friends, groups). Traditional relational schemas struggle to model this efficiently.
2. **Real-Time Requirements**: From notifications to live updates, social media thrives on low-latency interactions. Push-based architectures (e.g., WebSockets) complicate traditional request-response flows.
3. **Eventual Consistency Needs**: Scaling horizontal writes often requires sacrificing strict consistency. Handling eventual consistency for posts, reactions, and comments adds complexity.
4. **Content Propagation**: Viral content requires efficient fan-out to followers. Recalculating "home feeds" in real-time is computationally expensive.
5. **Moderation and Privacy**: Dynamic rules (e.g., "hide posts from certain friends") demand flexible query patterns that relational databases may not support natively.

### Example of Pain Without Patterns
Consider a simple "like" feature in a relational database:
```sql
-- Basic like table (often seen in early social apps)
CREATE TABLE post_likes (
    post_id INT NOT NULL,
    user_id INT NOT NULL,
    created_at TIMESTAMP,
    PRIMARY KEY (post_id, user_id)
);
```
This works for small-scale apps but fails under scale:
- **Performance**: Querying a user’s liked posts requires a self-join or a full table scan for large `post_likes`.
- **Real-Time Updates**: Notifying followers of a post when they’re liked requires a slow, linear scan of all post fans.
- **Eventual Consistency**: If you denormalize for performance (e.g., cache liked_post_ids in the user table), you introduce consistency issues.

---

## The Solution: Social-Media Domain Patterns

To address these challenges, we use a combination of patterns that prioritize:
- **Graph data structures** for connections.
- **Event-driven architectures** for real-time updates.
- **Materialized views** for performance-critical queries.
- **Optimistic concurrency** for content propagation.

Here’s how these patterns work together:

| Problem               | Pattern Solution                          | Example Use Case                  |
|-----------------------|------------------------------------------|-----------------------------------|
| Graph traversal       | Adjacency lists + BFS/DFS              | Finding mutual friends            |
| Real-time updates     | Event sourcing + WebSockets              | Live notification feeds           |
| Feed generation       | Materialized timeline (TTL cache)       | Home/Explore pages                |
| Moderation rules      | Rule-based triggers + Redis Bloom filters | Hiding inappropriate content       |
| Content propagation   | Push-based fan-out (e.g., RabbitMQ)      | Sharing posts to followers        |

---

## Core Components and Solutions

### 1. Modeling Users and Connections: The Adjacency List Pattern

**Problem**: How to represent a graph of connections efficiently?
**Solution**: Use an adjacency list to represent bidirectional relationships (e.g., follower/followee) with a dedicated table.

```sql
-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP,
    -- Add indexes for frequently queried fields
    USER_OPCLASS btree hash
);

-- Adjacency list for bidirectional connections (e.g., "following")
CREATE TABLE user_follows (
    follower_id INT NOT NULL,
    followee_id INT NOT NULL,
    -- Optional: add a "since" timestamp to distinguish states
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (follower_id, followee_id),
    INDEX idx_followee (followee_id),
    CONSTRAINT valid_follow CHECK (follower_id != followee_id)
);
```

**Tradeoffs**:
- *Pros*: Simple to query for direct connections (e.g., `SELECT from user_follows WHERE followee_id = ?`).
- *Cons*: Finding mutual friends requires a nested query (or a dedicated mutual-friends graph table).
- *Scale*: Works well up to ~10M users; beyond that, consider a graph database like Neo4j.

**Optimized Query Example**:
```sql
-- Get all posts from a user's followers (for their timeline)
SELECT p.post_id, p.content, p.created_at
FROM posts p
JOIN user_follows uf ON p.author_id = uf.followee_id
WHERE uf.follower_id = :user_id
ORDER BY p.created_at DESC
LIMIT 20;
```

---

### 2. Real-Time Feeds: Event Sourcing + Fan-Out

**Problem**: How to notify followers when a post is updated?
**Solution**: Use event sourcing to log changes and a fan-out system (e.g., RabbitMQ) to push updates to subscribers.

#### Step 1: Event Sourcing
Log every change as an immutable event:
```sql
-- Event table
CREATE TABLE events (
    event_id UUID PRIMARY KEY,
    user_id INT NOT NULL,
    event_type VARCHAR(20) NOT NULL, -- e.g., "POST_CREATED", "LIKE_ADDED"
    payload JSONB NOT NULL,         -- e.g., {"post_id": 123, "timestamp": "..."}
    created_at TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_type (event_type)
);
```

#### Step 2: Fan-Out with a Message Queue
When a post is created/liked, publish an event to a topic and consume it to update timelines:
```python
# Example using RabbitMQ (Python)
from pika import BlockingConnection, ConnectionParameters

def publish_event(event_type, payload):
    connection = BlockingConnection(ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange='social_events', exchange_type='fanout')
    channel.basic_publish(
        exchange='social_events',
        routing_key='',
        body=json.dumps({
            'type': event_type,
            'payload': payload,
            'timestamp': datetime.now().isoformat()
        })
    )
    connection.close()

# Example payload for a POST_CREATED event:
{
    "type": "POST_CREATED",
    "payload": {
        "post_id": 42,
        "author_id": 100,
        "content": "Hello world!"
    }
}
```

#### Step 3: Timeline Materialization
Use a background worker to update timelines (e.g., Redis Stream or a dedicated table):
```sql
-- Timeline snapshot (optimized for read-heavy workloads)
CREATE TABLE user_timelines (
    user_id INT NOT NULL,
    post_id INT NOT NULL,
    created_at TIMESTAMP,
    PRIMARY KEY (user_id, post_id),
    INDEX idx_recent (user_id, created_at DESC)
);
```

**Tradeoffs**:
- *Pros*: Decouples events from consumers; scales horizontally.
- *Cons*: Eventual consistency; requires idempotency handling for retries.

---

### 3. Feed Generation: The Feed Algorithm Pattern
**Problem**: How to efficiently generate a "home feed" combining:
- Posts from followed users.
- Recommended content (e.g., trending).
- Past interactions (e.g., "You liked this—check it out")?

**Solution**: Combine:
- **Materialized timelines** (cold start performance).
- **Incremental updates** (fan-out + Redis pub/sub).
- **Scoring algorithms** (e.g., rank posts by recency + engagement).

#### Example Scoring Function (Python):
```python
def score_post(post, user_interactions):
    base_score = 100  # Recency is handled by sorting
    # Adjust score for likes/comments by user
    if post["id"] in user_interactions.get("liked_posts", []):
        base_score += 20
    if post["id"] in user_interactions.get("recent_comments", []):
        base_score += 15
    return base_score
```

#### Optimized Query (PostgreSQL):
```sql
-- Generate a hybrid feed (followed + recommended)
WITH followed_posts AS (
    SELECT p.post_id, p.content, p.created_at,
           ROW_NUMBER() OVER (PARTITION BY p.author_id ORDER BY p.created_at DESC) as post_rank
    FROM posts p
    JOIN user_follows uf ON p.author_id = uf.followee_id
    WHERE uf.follower_id = :user_id
),
recommended_posts AS (
    SELECT p.post_id, p.content, p.created_at,
           ROW_NUMBER() OVER (ORDER BY recency_score DESC) as rank
    FROM posts p
    WHERE p.author_id NOT IN (
        SELECT followee_id FROM user_follows WHERE follower_id = :user_id
    )
),
unioned_feeds AS (
    SELECT 'followed' as source, post_id, content, created_at, post_rank as rank
    FROM followed_posts
    WHERE post_rank <= 3  -- Top 3 posts per followed user
    UNION ALL
    SELECT 'recommended' as source, post_id, content, created_at, rank
    FROM recommended_posts
    WHERE rank <= 10     -- Top 10 recommended posts
)
SELECT post_id, content, created_at, source
FROM unioned_feeds
ORDER BY created_at DESC, rank ASC
LIMIT 20;
```

**Tradeoffs**:
- *Pros*: Hybrid feeds balance personalization and performance.
- *Cons*: Complexity; requires tuning for each platform.

---

### 4. Content Propagation: Push vs. Pull
**Problem**: How to share content with followers efficiently?
**Solution**: Use a hybrid approach:
- **Push**: Fan-out via RabbitMQ (low-latency).
- **Pull**: Lazy-load from a materialized table (e.g., `user_follows_posts`).

#### Push Example (RabbitMQ Consumer):
```python
# Consumer script for POST_CREATED events
def process_post_created(ch, method, properties, body):
    event = json.loads(body)
    post = event["payload"]
    # Push to all followers' timelines (async)
    for follower_id in get_followers(post["author_id"]):
        update_timeline(follower_id, post["post_id"])
```

#### Pull Example (Optimized Query):
```sql
-- Get a user's recent timeline with followee posts
SELECT p.post_id, p.content, p.created_at
FROM posts p
WHERE p.post_id IN (
    SELECT post_id FROM user_follows_posts
    WHERE user_id = :user_id
    ORDER BY created_at DESC
    LIMIT 100  -- Recent posts for lazy loading
)
ORDER BY p.created_at DESC
LIMIT 20;
```

**Tradeoffs**:
- *Push*: Better for real-time but adds complexity.
- *Pull*: Simpler but requires timely updates (e.g., via cron jobs).

---

### 5. Moderation: Rule-Based Triggers
**Problem**: How to enforce dynamic rules (e.g., "hide posts from certain friends")?
**Solution**: Use Redis Bloom filters for quick rule checks and PostgreSQL triggers for enforcement.

#### Example Rule: Hide Posts from Blocked Users
```sql
-- Blocked users table
CREATE TABLE user_blocks (
    blocker_id INT NOT NULL,
    blocked_id INT NOT NULL,
    PRIMARY KEY (blocker_id, blocked_id)
);

-- Trigger to block posts from blocked users
CREATE OR REPLACE FUNCTION hide_blocked_posts()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM user_blocks ub
        WHERE ub.blocker_id = NEW.user_id AND ub.blocked_id = OLD.author_id
    ) THEN
        NEW.visible = FALSE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to timeline updates
CREATE TRIGGER trg_hide_blocked_posts
BEFORE INSERT OR UPDATE ON user_timelines
FOR EACH ROW EXECUTE FUNCTION hide_blocked_posts();
```

#### Bloom Filter for Fast Rule Checks (Redis):
```python
# Add a blocked user to a Bloom filter
redis = Redis()
redis.zadd(f"blocked:{blocker_id}", {blocked_id: 1})

# Check if a post should be hidden
def should_hide_post(user_id, post_author_id):
    return redis.sismember(f"blocked:{user_id}", post_author_id)
```

**Tradeoffs**:
- *Pros*: Fast rule evaluation; scalable with Redis.
- *Cons*: Bloom filters have false positives; triggers can slow writes.

---

## Implementation Guide

### Step 1: Start with a Graph Model
- Use PostgreSQL or a graph database for connections.
- Begin with an adjacency list; optimize later with graph algorithms.

### Step 2: Adopt Event Sourcing
- Log every change to an `events` table.
- Use a queue (RabbitMQ/Kafka) for fan-out.

### Step 3: Materialize Timelines
- Create a `user_timelines` table for cold-start performance.
- Update it via background jobs or real-time processing.

### Step 4: Implement Hybrid Feeds
- Combine followed posts + recommendations in a single query.
- Use PostgreSQL’s `UNION ALL` and window functions.

### Step 5: Add Moderation Rules
- Use Redis Bloom filters for quick checks.
- Enforce rules with triggers or application logic.

### Step 6: Test at Scale
- Load-test with tools like Locust.
- Monitor queue lag and query performance.

---

## Common Mistakes to Avoid

1. **Over-Optimizing Early**:
   - Don’t prematurely denormalize or use complex graph databases for small-scale apps. Start simple and iterate.

2. **Ignoring Eventual Consistency**:
   - Assume eventual consistency for user profiles, posts, and timelines. Use techniques like CRDTs or operational transforms if needed.

3. **Tight Coupling**:
   - Avoid direct DB-to-DB replication. Use event sourcing and materialized views to decouple systems.

4. **Forgetting Idempotency**:
   - Event-driven systems require idempotent handlers to avoid duplicate processing.

5. **Underestimating Real-Time Costs**:
   - WebSockets and queues add operational complexity. Benchmark before committing.

6. **Neglecting Privacy**:
   - Ensure moderation rules (blocks, privacy settings) are enforced at all layers (DB, app, client).

7. **Using Raw JSON for Relationships**:
   - Avoid storing JSON graphs in a single column. Normalize relationships for performance.

---

## Key Takeaways

- **Graphs first**: Model users and connections as an adjacency list or graph database.
- **Event first**: Use event sourcing for auditing and fan-out.
- **Materialize hot paths**: Cache timelines and feeds to avoid slow queries.
- **Hybrid feeds**: Combine followed content + recommendations for engagement.
- **Moderate dynamically**: Use Bloom filters + triggers for flexible rules.
- **Tradeoffs matter**: Push vs. pull for content distribution; consistency vs. latency.

---

## Conclusion

Building a social media backend is a journey from simple CRUD operations to a complex, event-driven system. By leveraging **social-media domain patterns**, you can tackle scalability, real-time requirements, and moderation challenges with confidence. Start with a graph model, adopt event sourcing, and optimize incrementally. Remember: no single pattern is a silver bullet. The key is balancing tradeoffs—whether that’s push vs. pull for content distribution or eventual vs. strong consistency.

For further reading:
- [Event Sourcing Patterns](https://eventstore.com/blog/banana-strawberry)
- [Graph Databases for Social Networks](https://neo4j.com/graph-academy/)
- [PostgreSQL for High-Performance Feeds](https://www.citusdata.com/blog/)

Now go build that viral app!
```

---
**Tone Notes**:
- The post balances technical depth with practical advice.
- Code blocks are concise but complete, with real-world relevance.
- Tradeoffs are highlighted to encourage critical thinking.
- The conclusion ties everything together while leaving room for exploration.