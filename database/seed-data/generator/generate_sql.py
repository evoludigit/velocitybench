#!/usr/bin/env python3
"""
SQL Generator - Converts YAML corpus to executable SQL seed data

This generator reads the YAML corpus and produces SQL files for
different dataset sizes (xs, medium, large).

Usage:
    python generate_sql.py --size xs --output ../output/sql/03-data-xs.sql
    python generate_sql.py --size medium --output ../output/sql/03-data-medium.sql
    python generate_sql.py --size large --output ../output/sql/03-data-large.sql

The generated SQL follows the Trinity Pattern schema and includes:
- Fixed fixtures (Alice, Bob, Charlie, Diana, Eve) with predictable UUIDs
- Generated users, posts, comments following configured distributions
- Relationships (follows, likes, categories)
"""

import argparse
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

# Seed for reproducibility
random.seed(42)

# Base path for corpus
CORPUS_PATH = Path(__file__).parent.parent / "corpus"


def load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML file and return parsed content."""
    with open(path) as f:
        return yaml.safe_load(f)


def load_dataset_config(size: str) -> dict[str, Any]:
    """Load dataset configuration for given size."""
    config_path = CORPUS_PATH / "datasets" / f"{size}.yaml"
    return load_yaml(config_path)


def load_pattern(pattern_id: str) -> dict[str, Any]:
    """Load pattern definition from corpus."""
    # Search in pattern directories
    for category in [
        "identifiers",
        "queries",
        "architecture",
        "relationships",
        "performance",
    ]:
        pattern_path = CORPUS_PATH / "patterns" / category / f"{pattern_id}.yaml"
        if pattern_path.exists():
            return load_yaml(pattern_path)
    raise FileNotFoundError(f"Pattern not found: {pattern_id}")


def get_fixtures() -> list[dict]:
    """Get fixed user fixtures from Trinity Pattern definition."""
    pattern = load_pattern("trinity-pattern")
    return pattern["seed_data"]["fixtures"]


def generate_uuid_v4() -> str:
    """Generate a random UUID v4."""
    return str(uuid.uuid4())


def random_timestamp(days_back: int = 365) -> str:
    """Generate random timestamp within the last N days."""
    base = datetime.now()
    delta = timedelta(days=random.randint(0, days_back))
    return (base - delta).strftime("%Y-%m-%d %H:%M:%S")


def generate_users_sql(config: dict) -> str:
    """Generate SQL for users table."""
    fixtures = get_fixtures()
    total_users = config["counts"]["users"]
    generated_count = total_users - len(fixtures)

    lines = [
        "-- ============================================================",
        f"-- Users ({total_users} total)",
        "-- Pattern: Trinity Identifiers (pk_, id, username)",
        "-- ============================================================",
        "",
        "SET search_path TO benchmark, public;",
        "",
        f"-- Fixed fixtures ({len(fixtures)} users) - predictable UUIDs for testing",
        "INSERT INTO tb_user (id, email, username, first_name, last_name, bio, is_active) VALUES",
    ]

    # Fixed fixtures
    fixture_values = []
    for user in fixtures:
        bio = user.get("bio", "").replace("'", "''")
        fixture_values.append(
            f"    ('{user['id']}', '{user['email']}', '{user['username']}', "
            f"'{user['first_name']}', '{user['last_name']}', '{bio}', {str(user['is_active']).lower()})"
        )

    lines.append(",\n".join(fixture_values) + ";")

    # Generated users
    lines.extend(
        [
            "",
            f"-- Generated users ({generated_count} users)",
            "INSERT INTO tb_user (email, username, first_name, last_name, bio, is_active)",
            "SELECT",
            "    'user' || i || '@example.com',",
            "    'user' || i,",
            "    'First' || i,",
            "    'Last' || i,",
            f"    'Generated user ' || i || ' for {config['id']} dataset benchmarking',",
            "    true",
            f"FROM generate_series({len(fixtures) + 1}, {total_users}) AS i;",
        ]
    )

    return "\n".join(lines)


def generate_posts_sql(config: dict) -> str:
    """Generate SQL for posts table."""
    fixtures = get_fixtures()
    total_posts = config["counts"]["posts"]
    total_users = config["counts"]["users"]

    lines = [
        "",
        "-- ============================================================",
        f"-- Posts ({total_posts} total)",
        "-- Pattern: Foreign key uses INTEGER (fk_author), not UUID",
        "-- ============================================================",
        "",
        "-- Fixed fixture posts (predictable content for testing)",
    ]

    # Create some fixed posts for fixtures
    fixture_posts = []
    post_pk = 1
    for user in fixtures:
        post_count = user.get("post_count", 5)
        for j in range(post_count):
            slug = f"{user['username']}-post-{j + 1}"
            title = f"{user['first_name']}'s Post #{j + 1}"
            content = f"This is a post by {user['username']} about backend development."
            fixture_posts.append(
                f"    (gen_random_uuid(), '{slug}', {user['pk']}, '{title}', '{content}', NOW() - interval '{post_pk} days')"
            )
            post_pk += 1

    lines.append(
        "INSERT INTO tb_post (id, slug, fk_author, title, content, published_at) VALUES"
    )
    lines.append(",\n".join(fixture_posts[:50]) + ";")  # First 50 fixture posts

    # Generated posts distributed across users
    remaining_posts = total_posts - len(fixture_posts[:50])
    lines.extend(
        [
            "",
            f"-- Generated posts ({remaining_posts} posts) distributed across users",
            "INSERT INTO tb_post (slug, fk_author, title, content, published_at)",
            "SELECT",
            "    'post-' || i,",
            f"    1 + (i % {total_users}),  -- Distribute across users",
            "    'Generated Post #' || i,",
            "    'Content for generated post ' || i || '. This post demonstrates the Trinity Pattern in action.',",
            "    NOW() - (i || ' hours')::interval",
            f"FROM generate_series({len(fixture_posts[:50]) + 1}, {total_posts}) AS i;",
        ]
    )

    return "\n".join(lines)


def generate_comments_sql(config: dict) -> str:
    """Generate SQL for comments table."""
    total_comments = config["counts"]["comments"]
    total_posts = config["counts"]["posts"]
    total_users = config["counts"]["users"]
    nested_prob = config["distributions"].get("nested_comment_probability", 0.15)

    lines = [
        "",
        "-- ============================================================",
        f"-- Comments ({total_comments} total)",
        "-- Pattern: Self-referential for threading (parent_comment_id)",
        "-- ============================================================",
        "",
        f"-- Top-level comments ({int(total_comments * (1 - nested_prob))} comments)",
        "INSERT INTO tb_comment (fk_post, fk_author, content, parent_comment_id)",
        "SELECT",
        f"    1 + (i % {total_posts}),  -- Distribute across posts",
        f"    1 + (i % {total_users}),  -- Distribute across users",
        "    'Comment #' || i || ' on this post. Great content!',",
        "    NULL  -- Top-level comment",
        f"FROM generate_series(1, {int(total_comments * (1 - nested_prob))}) AS i;",
        "",
        f"-- Nested/reply comments ({int(total_comments * nested_prob)} comments)",
        "INSERT INTO tb_comment (fk_post, fk_author, content, parent_comment_id)",
        "SELECT",
        "    c.fk_post,  -- Same post as parent",
        f"    1 + (i % {total_users}),",
        "    'Reply to comment ' || c.pk_comment || ': I agree with this!',",
        "    c.pk_comment  -- Reference parent comment",
        "FROM",
        f"    generate_series(1, {int(total_comments * nested_prob)}) AS i,",
        f"    (SELECT pk_comment, fk_post FROM tb_comment ORDER BY pk_comment LIMIT {int(total_comments * (1 - nested_prob) / 10)}) AS c",
        "WHERE i % 10 = 0;",  # Spread replies across subset of comments
    ]

    return "\n".join(lines)


def generate_categories_sql(config: dict) -> str:
    """Generate SQL for categories and post_categories."""
    total_categories = config["counts"]["categories"]
    total_post_categories = config["counts"]["post_categories"]
    total_posts = config["counts"]["posts"]

    category_names = [
        "Technology",
        "Programming",
        "Database",
        "GraphQL",
        "REST",
        "Performance",
        "Security",
        "DevOps",
        "Cloud",
        "Architecture",
        "Testing",
        "Frontend",
        "Backend",
        "Mobile",
        "AI/ML",
        "Career",
        "Tutorial",
        "Opinion",
        "News",
        "Review",
        "JavaScript",
        "Python",
        "Go",
        "Rust",
        "Java",
        "PostgreSQL",
        "MongoDB",
        "Redis",
        "Kubernetes",
        "Docker",
        "AWS",
        "GCP",
        "Azure",
        "Linux",
        "Git",
        "Agile",
        "Best Practices",
        "Code Review",
        "Documentation",
        "Open Source",
        "Startups",
        "Enterprise",
        "Scale",
        "Microservices",
        "Monolith",
        "API Design",
        "Data Modeling",
        "Caching",
        "Queues",
        "Monitoring",
    ]

    lines = [
        "",
        "-- ============================================================",
        f"-- Categories ({total_categories} categories)",
        "-- Pattern: Many-to-many with junction table",
        "-- ============================================================",
        "",
        "INSERT INTO categories (name, slug, description) VALUES",
    ]

    category_values = []
    for i in range(min(total_categories, len(category_names))):
        name = category_names[i]
        slug = name.lower().replace("/", "-").replace(" ", "-")
        category_values.append(f"    ('{name}', '{slug}', 'Posts about {name}')")

    lines.append(",\n".join(category_values) + ";")

    # Post categories (many-to-many)
    lines.extend(
        [
            "",
            f"-- Post-Category relationships ({total_post_categories} relationships)",
            "INSERT INTO post_categories (fk_post, fk_category)",
            "SELECT DISTINCT",
            f"    1 + (i % {total_posts}),",
            f"    1 + ((i * 7) % {total_categories})  -- Semi-random distribution",
            f"FROM generate_series(1, {total_post_categories}) AS i",
            "ON CONFLICT DO NOTHING;",  # Ignore duplicates
        ]
    )

    return "\n".join(lines)


def generate_relationships_sql(config: dict) -> str:
    """Generate SQL for user_follows and post_likes."""
    total_follows = config["counts"]["user_follows"]
    total_likes = config["counts"]["post_likes"]
    total_users = config["counts"]["users"]
    total_posts = config["counts"]["posts"]

    lines = [
        "",
        "-- ============================================================",
        f"-- User Follows ({total_follows} relationships)",
        "-- Pattern: Graph relationships (follower -> followed)",
        "-- ============================================================",
        "",
        "INSERT INTO user_follows (fk_follower, fk_followed)",
        "SELECT DISTINCT",
        f"    1 + (i % {total_users}),",
        f"    1 + ((i * 17) % {total_users})  -- Different user",
        f"FROM generate_series(1, {total_follows}) AS i",
        f"WHERE (i % {total_users}) != ((i * 17) % {total_users})  -- Can't follow yourself",
        "ON CONFLICT DO NOTHING;",
        "",
        "-- ============================================================",
        f"-- Post Likes ({total_likes} likes)",
        "-- Pattern: Many-to-many with timestamp",
        "-- ============================================================",
        "",
        "INSERT INTO post_likes (fk_user, fk_post)",
        "SELECT DISTINCT",
        f"    1 + (i % {total_users}),",
        f"    1 + ((i * 13) % {total_posts})",
        f"FROM generate_series(1, {total_likes}) AS i",
        "ON CONFLICT DO NOTHING;",
    ]

    return "\n".join(lines)


def generate_profiles_sql(config: dict) -> str:
    """Generate SQL for user_profiles (JSONB flexible schema)."""
    total_profiles = config["counts"]["user_profiles"]

    lines = [
        "",
        "-- ============================================================",
        f"-- User Profiles ({total_profiles} profiles)",
        "-- Pattern: JSONB for flexible/extensible schemas",
        "-- ============================================================",
        "",
        "INSERT INTO user_profiles (fk_user, profile_data)",
        "SELECT",
        "    u.pk_user,",
        "    jsonb_build_object(",
        "        'theme', CASE WHEN u.pk_user % 2 = 0 THEN 'dark' ELSE 'light' END,",
        "        'notifications', jsonb_build_object(",
        "            'email', true,",
        "            'push', u.pk_user % 3 = 0",
        "        ),",
        "        'social', jsonb_build_object(",
        "            'twitter', '@user' || u.pk_user,",
        "            'github', 'user' || u.pk_user",
        "        ),",
        "        'preferences', jsonb_build_object(",
        "            'language', 'en',",
        "            'timezone', 'UTC'",
        "        )",
        "    )",
        "FROM tb_user u",
        f"LIMIT {total_profiles};",
    ]

    return "\n".join(lines)


def generate_sql(size: str) -> str:
    """Generate complete SQL for dataset size."""
    config = load_dataset_config(size)

    sections = [
        f"-- VelocityBench Seed Data - {config['name']} Dataset",
        f"-- Generated: {datetime.now().isoformat()}",
        f"-- Size: {size}",
        f"-- Description: {config['description']}",
        "--",
        f"-- Users: {config['counts']['users']:,}",
        f"-- Posts: {config['counts']['posts']:,}",
        f"-- Comments: {config['counts']['comments']:,}",
        f"-- Categories: {config['counts']['categories']}",
        "--",
        "-- This file is auto-generated from the YAML corpus.",
        "-- Do not edit directly - modify corpus files instead.",
        "",
        "BEGIN;",
        "",
        generate_users_sql(config),
        generate_posts_sql(config),
        generate_comments_sql(config),
        generate_categories_sql(config),
        generate_relationships_sql(config),
        generate_profiles_sql(config),
        "",
        "COMMIT;",
        "",
        f"-- Dataset loaded successfully: {config['name']}",
        f"-- Expected load time: {config['performance_expectations']['load_time']}",
        f"-- Expected database size: {config['performance_expectations']['database_size']}",
    ]

    return "\n".join(sections)


def main():
    parser = argparse.ArgumentParser(
        description="Generate SQL seed data from YAML corpus"
    )
    parser.add_argument(
        "--size",
        choices=["xs", "medium", "large"],
        default="xs",
        help="Dataset size to generate",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: ../output/sql/03-data-{size}.sql)",
    )
    parser.add_argument(
        "--stdout", action="store_true", help="Output to stdout instead of file"
    )

    args = parser.parse_args()

    sql = generate_sql(args.size)

    if args.stdout:
        print(sql)
    else:
        output_path = args.output or (
            Path(__file__).parent.parent / "output" / "sql" / f"03-data-{args.size}.sql"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(sql)
        print(f"Generated: {output_path}")
        print(f"Size: {args.size}")
        config = load_dataset_config(args.size)
        print(f"Users: {config['counts']['users']:,}")
        print(f"Posts: {config['counts']['posts']:,}")
        print(f"Comments: {config['counts']['comments']:,}")


if __name__ == "__main__":
    main()
