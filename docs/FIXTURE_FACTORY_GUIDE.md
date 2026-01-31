# Fixture Factory Guide

## Overview

VelocityBench provides two complementary fixtures for creating test data:

1. **`factory` fixture** - Create individual entities with custom values
2. **`bulk_factory` fixture** - Create many entities efficiently

This guide shows how to use each for different testing scenarios.

---

## The `factory` Fixture

The `factory` fixture provides a `TestFactory` class with methods for creating individual test entities.

### Location

```python
from tests.common.fixtures import db  # Uses this under the hood
```

### Creating Users

#### Basic User Creation

```python
def test_basic_user_creation(db, factory):
    """Create a user with minimal data."""
    user = factory.create_user("alice", "alice@example.com")

    assert user["username"] == "alice"
    assert user["email"] == "alice@example.com"
    assert user["pk_user"] is not None
    assert user["id"] is not None  # UUID
```

#### User Creation with Full Details

```python
def test_user_with_full_profile(db, factory):
    """Create a user with complete information."""
    user = factory.create_user(
        username="alice",
        email="alice@example.com",
        full_name="Alice Smith",
        bio="Software engineer from San Francisco"
    )

    assert user["username"] == "alice"
    assert user["full_name"] == "Alice Smith"
    assert user["bio"] == "Software engineer from San Francisco"
```

#### User Creation with Identifier

```python
def test_user_with_custom_identifier(db, factory):
    """Create a user with custom identifier (slug)."""
    user = factory.create_user(
        username="alice",
        email_or_identifier="alice-smith",
        email="alice@example.com"
    )

    assert user["identifier"] == "alice-smith"
    assert user["username"] == "alice"
```

### Returned User Object

All `create_user` methods return a dictionary:

```python
{
    "pk_user": 1,                              # Internal ID
    "id": UUID("..."),                         # Public API ID
    "username": "alice",                       # Unique username
    "identifier": "alice-smith",               # URL-friendly slug
    "email": "alice@example.com",              # Email address
    "full_name": "Alice Smith",                # Display name
    "bio": "My biography"                      # User bio
}
```

**Use `pk_user` for foreign keys, `id` for APIs.**

### Creating Posts

#### Post Creation with Author

```python
def test_create_post_with_author(db, factory):
    """Create a post for an existing user."""
    user = factory.create_user("alice", "alice@example.com")

    post = factory.create_post(
        fk_author=user["pk_user"],
        title="My First Post",
        content="Hello world!",
        identifier="my-first-post"
    )

    assert post["title"] == "My First Post"
    assert post["content"] == "Hello world!"
    assert post["fk_author"] == user["pk_user"]
```

#### Post Creation Shorthand

```python
def test_create_post_with_defaults(db, factory):
    """Create a post with auto-generated identifier."""
    user = factory.create_user("alice", "alice@example.com")

    post = factory.create_post(
        fk_author=user["pk_user"],
        title="Quick Post"
    )

    assert post["title"] == "Quick Post"
    assert post["identifier"] is not None  # Auto-generated from title
```

### Returned Post Object

```python
{
    "pk_post": 1,                              # Internal ID
    "id": UUID("..."),                         # Public API ID
    "fk_author": 1,                            # Author's pk_user
    "title": "My First Post",                  # Post title
    "identifier": "my-first-post",             # URL slug
    "content": "Hello world!",                 # Post content
    "created_at": datetime(...),               # Creation timestamp
    "updated_at": datetime(...)                # Last update timestamp
}
```

### Creating Comments

#### Comment Creation with Context

```python
def test_create_comment_on_post(db, factory):
    """Create a comment on an existing post."""
    user = factory.create_user("alice", "alice@example.com")
    post = factory.create_post(fk_author=user["pk_user"], title="Post")

    commenter = factory.create_user("bob", "bob@example.com")
    comment = factory.create_comment(
        fk_post=post["pk_post"],
        fk_author=commenter["pk_user"],
        content="Great post!"
    )

    assert comment["content"] == "Great post!"
    assert comment["fk_post"] == post["pk_post"]
    assert comment["fk_author"] == commenter["pk_user"]
```

### Factory Method Summary

| Method | Purpose | Required Args | Optional Args |
|--------|---------|---------------|---------------|
| `create_user` | Create a user | username, email | full_name, bio, identifier |
| `create_post` | Create a post | fk_author, title | content, identifier |
| `create_comment` | Create a comment | fk_post, fk_author, content | is_approved |

---

## The `bulk_factory` Fixture

The `bulk_factory` fixture provides methods for creating many entities efficiently.

### Creating Multiple Users

#### Basic Bulk User Creation

```python
def test_bulk_user_creation(db, bulk_factory):
    """Create 100 users efficiently."""
    users = bulk_factory.create_bulk_users(count=100)

    assert len(users) == 100
    assert users[0]["username"] == "user0"
    assert users[99]["username"] == "user99"
```

#### Bulk Creation with Custom Prefix

```python
def test_bulk_users_with_prefix(db, bulk_factory):
    """Create users with custom naming prefix."""
    developers = bulk_factory.create_bulk_users(count=10, prefix="dev")

    assert developers[0]["username"] == "dev0"
    assert developers[0]["email"] == "dev0@example.com"
    assert developers[0]["full_name"] == "Dev 0"
```

### User with Multiple Posts

#### Create User and Their Posts in One Call

```python
def test_user_with_multiple_posts(db, bulk_factory):
    """Create a user with 10 posts efficiently."""
    result = bulk_factory.create_user_with_posts(
        username="alice",
        identifier="alice",
        email="alice@example.com",
        post_count=10
    )

    user = result["user"]
    posts = result["posts"]

    assert user["username"] == "alice"
    assert len(posts) == 10
    assert all(post["fk_author"] == user["pk_user"] for post in posts)
```

### User with Posts and Comments

#### Create Full Hierarchy

```python
def test_user_with_posts_and_comments(db, bulk_factory):
    """Create user, posts, and comments in realistic structure."""
    result = bulk_factory.create_user_with_posts_and_comments(
        username="alice",
        identifier="alice",
        email="alice@example.com",
        post_count=5,
        comments_per_post=3
    )

    user = result["user"]
    posts = result["posts"]
    comments = result["comments"]

    assert len(posts) == 5
    assert len(comments) == 15  # 5 posts × 3 comments
    assert all(comment["fk_post"] in [p["pk_post"] for p in posts] for comment in comments)
```

### Bulk Factory Method Summary

| Method | Purpose | Key Args | Returns |
|--------|---------|----------|---------|
| `create_bulk_users` | Create N users | count, prefix | List[User] |
| `create_user_with_posts` | Create user + posts | username, post_count | {user, posts} |
| `create_user_with_posts_and_comments` | Create full hierarchy | username, post_count, comments_per_post | {user, posts, comments} |
| `count_users` | Count users in DB | - | int |
| `count_posts` | Count posts in DB | - | int |
| `count_comments` | Count comments in DB | - | int |

---

## Combining Factories

### Using Both Factory and Bulk Factory

```python
def test_mixed_data_creation(db, factory, bulk_factory):
    """Create mixed manual and bulk data."""
    # Manually create specific users with custom data
    alice = factory.create_user("alice", "alice@example.com", full_name="Alice Smith")
    bob = factory.create_user("bob", "bob@example.com", full_name="Bob Jones")

    # Bulk create 100 generic users
    bulk_users = bulk_factory.create_bulk_users(count=100, prefix="user")

    # Alice and Bob are special, bulk users are default
    assert alice["full_name"] == "Alice Smith"
    assert bulk_users[0]["full_name"] == "User 0"
    assert len(bulk_users) + 2 == 102  # Total users
```

### Mixing Manual and Bulk Post Creation

```python
def test_mixed_post_creation(db, factory, bulk_factory):
    """Create posts manually and in bulk."""
    # Create author
    author = factory.create_user("alice", "alice@example.com")

    # Create specific post
    featured_post = factory.create_post(
        fk_author=author["pk_user"],
        title="Featured Post",
        content="This is important"
    )

    # Bulk create additional posts for same author
    with db.cursor() as cursor:
        for i in range(10):
            cursor.execute(
                "INSERT INTO benchmark.tb_post (fk_author, title) VALUES (%s, %s)",
                (author["pk_user"], f"Regular Post {i}")
            )

    # Check all posts exist
    with db.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s",
                      (author["pk_user"],))
        count = cursor.fetchone()[0]
        assert count == 11  # 1 featured + 10 regular
```

---

## Real-World Test Examples

### Example 1: Testing User Uniqueness Constraint

```python
def test_duplicate_username_raises_constraint_violation(db, factory):
    """Test that duplicate usernames are rejected."""
    # Create first user
    factory.create_user("alice", "alice1@example.com")

    # Try to create with same username
    with pytest.raises(Exception):  # psycopg.errors.UniqueViolation
        factory.create_user("alice", "alice2@example.com")
```

### Example 2: Testing N+1 Query Prevention

```python
def test_user_with_posts_dataloader_prevents_n_plus_one(db, bulk_factory):
    """Test that DataLoader prevents N+1 queries."""
    # Create user with 100 posts
    result = bulk_factory.create_user_with_posts(
        username="alice",
        identifier="alice",
        email="alice@example.com",
        post_count=100
    )

    # In real code, DataLoader would batch these queries
    # This test verifies the setup for DataLoader testing
    user = result["user"]
    posts = result["posts"]

    assert len(posts) == 100
    assert all(post["fk_author"] == user["pk_user"] for post in posts)
```

### Example 3: Testing Pagination

```python
def test_post_pagination_with_large_dataset(db, bulk_factory):
    """Test pagination works correctly with large dataset."""
    # Create user with 1000 posts
    result = bulk_factory.create_user_with_posts(
        username="alice",
        identifier="alice",
        email="alice@example.com",
        post_count=1000
    )

    user = result["user"]

    # In real code, query posts with pagination
    with db.cursor() as cursor:
        # Get page 1 (posts 0-9)
        cursor.execute(
            "SELECT * FROM benchmark.tb_post WHERE fk_author = %s ORDER BY pk_post LIMIT 10 OFFSET 0",
            (user["pk_user"],)
        )
        page1 = cursor.fetchall()

        # Get page 2 (posts 10-19)
        cursor.execute(
            "SELECT * FROM benchmark.tb_post WHERE fk_author = %s ORDER BY pk_post LIMIT 10 OFFSET 10",
            (user["pk_user"],)
        )
        page2 = cursor.fetchall()

    assert len(page1) == 10
    assert len(page2) == 10
    assert page1[0][0] != page2[0][0]  # Different posts
```

### Example 4: Performance Testing

```python
@pytest.mark.perf
def test_query_performance_with_large_dataset(db, bulk_factory):
    """Test query performance with realistic data volume."""
    import time

    # Create 1000 users with 5 posts each
    users = bulk_factory.create_bulk_users(count=1000)
    for user in users:
        for i in range(5):
            with db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO benchmark.tb_post (fk_author, title) VALUES (%s, %s)",
                    (user["pk_user"], f"Post {i}")
                )

    # Time the query
    start = time.time()
    with db.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM benchmark.tb_post")
        count = cursor.fetchone()[0]
    elapsed = time.time() - start

    assert count == 5000
    assert elapsed < 0.1  # Should complete in < 100ms
```

---

## Performance Tips

### Batch Operations

For creating many related entities, batch inserts are faster than individual creates:

```python
# ✅ FASTER: Batch insert
def create_many_posts(db, user_pk, count):
    """Create many posts in batch."""
    with db.cursor() as cursor:
        for i in range(count):
            cursor.execute(
                "INSERT INTO benchmark.tb_post (fk_author, title) VALUES (%s, %s)",
                (user_pk, f"Post {i}")
            )
    db.commit()

# ❌ SLOWER: Individual inserts
def create_many_posts_slow(db, factory, user_pk, count):
    """Create many posts individually."""
    for i in range(count):
        factory.create_post(fk_author=user_pk, title=f"Post {i}")
```

### Reuse Created Entities

```python
# ✅ GOOD: Create once, reuse
def test_posts_with_same_author(db, factory):
    """Test multiple posts by same author."""
    author = factory.create_user("alice", "alice@example.com")

    post1 = factory.create_post(fk_author=author["pk_user"], title="Post 1")
    post2 = factory.create_post(fk_author=author["pk_user"], title="Post 2")
    post3 = factory.create_post(fk_author=author["pk_user"], title="Post 3")

    # Reuse author dict
    assert post1["fk_author"] == author["pk_user"]
    assert post2["fk_author"] == author["pk_user"]
    assert post3["fk_author"] == author["pk_user"]

# ❌ WASTEFUL: Create user multiple times
def test_posts_with_same_author_bad(db, factory):
    """Test multiple posts by same author (inefficient)."""
    post1 = factory.create_post(fk_author=factory.create_user("alice", "a1@example.com")["pk_user"], title="Post 1")
    post2 = factory.create_post(fk_author=factory.create_user("alice", "a2@example.com")["pk_user"], title="Post 2")
    # Creates duplicate users unnecessarily!
```

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Foreign key error | Parent entity missing | Create user before post |
| Duplicate key error | Entity already exists | Use different username/identifier |
| Empty result | Test data not created | Verify factory method call |
| Fixture not found | Wrong import | Use `from tests.common.fixtures import db` |
| Database timeout | Too many inserts | Use bulk methods for large datasets |

---

## Related Documentation

- [Test Isolation Strategy](TEST_ISOLATION_STRATEGY.md) - How data is cleaned between tests
- [Test Naming Conventions](TEST_NAMING_CONVENTIONS.md) - How to name test methods
- [Cross-Framework Test Data](CROSS_FRAMEWORK_TEST_DATA.md) - Data consistency across frameworks
