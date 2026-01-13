# Dynamic Dataset Scaling Plan: 5K Gold Corpus → 1M Posts

**Date**: 2026-01-13
**Objective**: Generate scalable, parameterized datasets from a small gold corpus
**Output**: Git-ignored SQL/TSV files generated on-demand
**Scale**: 5K seed posts → configurable 1K to 1M variants

---

## Overview

Instead of committing 1M posts to git, generate them dynamically with parameters:

```bash
# Generate datasets at different scales
python scale_dataset.py --posts 5000 --users 500 --comments 50000
python scale_dataset.py --posts 1000000 --users 100000 --comments 5000000
python scale_dataset.py --scale-multiplier 200  # 5K seed × 200 = 1M posts
```

Output files (`.sql`, `.tsv`) are **git-ignored** and generated fresh each run.

---

## Current State Analysis

### Existing Structure

**Blog Posts**:
- 3,369 posts generated from vLLM
- Source: `database/seed-data/output/blog/`
- Formats: markdown (reference, tutorial, troubleshooting)

**Users**:
- 5,000 Faker-generated users
- Source: `load_blog_posts.py`
- Reproducible with seed

**Comments**:
- 0 comments (planned for later)
- Ready for generation

**Database Schema** (from `02-schema.sql`):
```sql
tb_user (pk_user, id, email, username, bio, avatar_url, ...)
tb_post (pk_post, id, fk_author, title, content, status, published_at, ...)
tb_comment (pk_comment, id, fk_post, fk_author, fk_parent, content, ...)
categories (id, name, slug)
post_categories (post_id, category_id) [many-to-many]
```

**Current Loader**: `load_blog_posts.py`
- Reads markdown posts from disk
- Generates users with Faker
- Uses PostgreSQL COPY for bulk insert
- Supports `--output` flag for SQL generation

---

## Proposed Architecture

### 1. Variant Generation System

**Core Concept**: Start with 5K AI-written seed posts, generate 200 lightweight variants per seed.

```
Gold Corpus (5K posts)
    ↓
Variant Generator
    ├── Title variants (with suffixes, audiences, formats)
    ├── Metadata variants (dates, authors, status)
    ├── Tag/category combinations
    ├── Content mutations (optional)
    └── Metrics (views, likes, bookmarks)
    ↓
Output: 1M Posts (5K × 200 variants)
```

### 2. Parameterization

Three configuration levels:

```yaml
# Level 1: Scale Multiplier (simple)
scale_multiplier: 200
# Result: 5K posts × 200 = 1M posts
#         automatically scale users & comments proportionally

# Level 2: Explicit Sizes (flexible)
num_seed_posts: 5000
num_posts: 1000000
num_users: 100000
num_comments: 5000000

# Level 3: Distribution Profiles (realistic)
profile: "production"  # scales all three proportionally
# Or custom ratios:
post_user_ratio: 10        # 10 posts per user
comment_post_ratio: 5      # 5 comments per post
```

### 3. File Structure

```
database/
  seed-data/
    gold-corpus/
      posts/              # 5K seed posts (committed)
      users.json          # 5K seed users metadata
      categories.json     # seed categories
    generated/            # Git-ignored output
      ├── users_*.tsv
      ├── posts_*.tsv
      ├── comments_*.tsv
      └── *.sql
    generator/
      ├── scale_dataset.py          # Main entry point
      ├── variant_generator.py      # Variant creation logic
      ├── bulk_loader.py            # Database insertion
      ├── config.yaml               # Scale configurations
      └── load_blog_posts.py        # (existing, refactored)
```

---

## Implementation Steps

### Phase 1: Extract Gold Corpus (Week 1)

#### 1.1 Create Gold Corpus

**Goal**: Identify and commit the "best of" 5K posts

```bash
# Extract from current 3,369 posts
python extract_gold_corpus.py \
  --input database/seed-data/output/blog/ \
  --output database/seed-data/gold-corpus/posts/ \
  --size 5000 \
  --quality-filter "length:500-5000 type:tutorial,reference"

# Result:
#   - 5000 markdown files (best quality)
#   - Reproducible selection (same files every time)
#   - Committed to git (small, high-quality)
```

**Files to create**:
- `database/seed-data/gold-corpus/posts/*.md` (5K files, ~500 MB compressed)
- `database/seed-data/gold-corpus/metadata.yaml` (post metadata)
- `database/seed-data/gold-corpus/categories.json` (category taxonomy)

#### 1.2 Extract User Seed

**Goal**: Create canonical user list (reproducible Faker seed)

```python
# In extract_gold_corpus.py
from faker import Faker

# Use fixed seed for reproducibility
fake = Faker()
Faker.seed(42)

users = []
for i in range(5000):
    users.append({
        "username": fake.username(),
        "email": fake.email(),
        "bio": fake.text(50),
        # ... etc
    })

# Save as JSON (committed)
with open("database/seed-data/gold-corpus/users_seed.json", "w") as f:
    json.dump(users, f)
```

**Files to create**:
- `database/seed-data/gold-corpus/users_seed.json` (5K users, ~5 MB)
- `database/seed-data/gold-corpus/categories_seed.json` (tag taxonomy)

---

### Phase 2: Variant Generator (Week 1-2)

#### 2.1 Create `variant_generator.py`

```python
# database/seed-data/generator/variant_generator.py

class VariantGenerator:
    """Generate lightweight variants from seed posts."""

    def __init__(self, seed_posts: List[Post], scale_multiplier: int):
        self.seed_posts = seed_posts
        self.multiplier = scale_multiplier
        self.variants_per_seed = scale_multiplier // len(seed_posts)

    def generate_variants(self) -> List[Post]:
        """Create self.variants_per_seed variants per seed post."""
        variants = []

        for seed_post in self.seed_posts:
            for variant_idx in range(self.variants_per_seed):
                # Create 200 lightweight variants
                variant = self._create_variant(seed_post, variant_idx)
                variants.append(variant)

        return variants

    def _create_variant(self, seed: Post, idx: int) -> Post:
        """Generate one variant by changing metadata, keeping body."""
        return Post(
            # Same body (or mutate lightly)
            title=self._mutate_title(seed.title, idx),
            content=seed.content,  # or self._mutate_content(seed.content, idx)

            # Different metadata
            slug=f"{seed.slug}-{idx}",
            published_at=self._spread_date(seed.published_at, idx),
            fk_author=self._rotate_author(seed.fk_author, idx),
            status=self._choose_status(idx),

            # Different relationships
            categories=self._recombine_categories(seed.categories, idx),
            views=random.randint(0, 10000),
            likes=random.randint(0, 500),
        )

    def _mutate_title(self, title: str, idx: int) -> str:
        """Add variants to title."""
        suffixes = [
            f" ({2024 + idx % 5})",
            " (Beginner's Guide)",
            " (Advanced)",
            " (Cheat Sheet)",
            " (Best Practices)",
            " (for Teams)",
            f" ({idx % 26 + 1})",  # 1-26 for A-Z
        ]
        return f"{title} {suffixes[idx % len(suffixes)]}"

    def _spread_date(self, base_date: datetime, idx: int) -> datetime:
        """Spread published dates over 5-10 years."""
        days_offset = (idx % 3650) - 1825  # ±5 years from base
        return base_date + timedelta(days=days_offset)

    def _rotate_author(self, seed_author_id: int, idx: int) -> int:
        """Rotate through user IDs (cycle through all users)."""
        num_users = 5000  # or parameterized
        return (seed_author_id + idx) % num_users

    def _choose_status(self, idx: int) -> str:
        """70% published, 30% draft."""
        return "published" if random.random() < 0.7 else "draft"

    def _recombine_categories(self, seed_cats: List[str], idx: int) -> List[str]:
        """Vary category combinations."""
        # Rotate, swap, add/remove categories
        rotated = seed_cats[idx % len(seed_cats):] + seed_cats[:idx % len(seed_cats)]
        if idx % 5 == 0:
            rotated = rotated[:-1]  # Remove one occasionally
        return rotated
```

#### 2.2 Content Mutation (Optional)

For realism, optionally mutate content lightly:

```python
def _mutate_content(self, content: str, idx: int) -> str:
    """Light content changes (optional)."""
    if idx % 50 == 0:  # Only mutate 2% of posts
        return content

    # Keep 95% identical, change 5%
    paragraphs = content.split('\n\n')

    # Shuffle paragraphs (but keep intro)
    if len(paragraphs) > 3:
        middle = paragraphs[1:-1]
        random.shuffle(middle)
        paragraphs = [paragraphs[0]] + middle + [paragraphs[-1]]

    # Add random FAQ or TL;DR occasionally
    if idx % 10 == 0:
        paragraphs.append("\n\n**TL;DR**: " + self._summarize(content))

    return '\n\n'.join(paragraphs)
```

---

### Phase 3: Scalable Loader (Week 2)

#### 3.1 Create `scale_dataset.py`

Main entry point for generating datasets:

```python
#!/usr/bin/env python
"""
Generate scalable datasets from gold corpus.

Usage:
    python scale_dataset.py --scale-multiplier 200 --output-dir /tmp/generated
    python scale_dataset.py --posts 1000000 --users 100000 --comments 5000000
    python scale_dataset.py --profile production
"""

import argparse
from pathlib import Path
from variant_generator import VariantGenerator
from bulk_loader import BulkLoader

def main():
    parser = argparse.ArgumentParser(description="Scale dataset from gold corpus")

    # Multiplier approach (simple)
    parser.add_argument('--scale-multiplier', type=int, default=1,
                        help='Multiply seed posts (default: 1 = no scaling)')

    # Explicit sizes (flexible)
    parser.add_argument('--seed-posts', type=int, default=5000,
                        help='Number of seed posts to use')
    parser.add_argument('--posts', type=int, default=None,
                        help='Target number of posts (overrides multiplier)')
    parser.add_argument('--users', type=int, default=None,
                        help='Target number of users')
    parser.add_argument('--comments', type=int, default=None,
                        help='Target number of comments')

    # Ratios
    parser.add_argument('--posts-per-user', type=float, default=10,
                        help='Posts per user (for auto-scaling)')
    parser.add_argument('--comments-per-post', type=float, default=5,
                        help='Comments per post')

    # Profile (preset configurations)
    parser.add_argument('--profile', choices=['tiny', 'dev', 'staging', 'production'],
                        help='Use preset profile')

    # Output
    parser.add_argument('--output-dir', type=Path, default=Path('/tmp/velocitybench'),
                        help='Output directory for SQL/TSV files')
    parser.add_argument('--format', choices=['sql', 'tsv', 'both'], default='both',
                        help='Output format')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be generated without writing')

    # Loading
    parser.add_argument('--load', action='store_true',
                        help='Load into PostgreSQL after generating')
    parser.add_argument('--connection', default='postgresql://localhost/velocitybench',
                        help='PostgreSQL connection string')

    args = parser.parse_args()

    # Resolve configuration
    config = resolve_config(args)

    # Load gold corpus
    gold_posts = load_gold_corpus('database/seed-data/gold-corpus')
    gold_users = load_gold_users('database/seed-data/gold-corpus')

    # Generate variants
    print(f"Generating {config.num_posts:,} posts from {len(gold_posts)} seed posts...")
    variant_gen = VariantGenerator(gold_posts, config.posts_multiplier)
    posts = variant_gen.generate_variants()

    # Generate users (if needed)
    if config.num_users > len(gold_users):
        print(f"Extending users from {len(gold_users)} to {config.num_users:,}...")
        users = extend_users(gold_users, config.num_users)
    else:
        users = gold_users

    # Generate comments (if needed)
    print(f"Generating {config.num_comments:,} comments...")
    comments = generate_comments(posts, users, config.num_comments)

    # Output
    loader = BulkLoader(config.output_dir, config.format)
    loader.save(posts, users, comments)

    print(f"\n✅ Generated:")
    print(f"  Posts:    {len(posts):,}")
    print(f"  Users:    {len(users):,}")
    print(f"  Comments: {len(comments):,}")
    print(f"  Output:   {config.output_dir}")

    if args.load:
        print(f"\n Loading into {args.connection}...")
        loader.load_to_db(args.connection, posts, users, comments)

def resolve_config(args) -> DatasetConfig:
    """Resolve configuration from arguments."""
    # Profile takes precedence
    if args.profile:
        config = PROFILES[args.profile]
    else:
        # Use multiplier or explicit sizes
        if args.scale_multiplier > 1:
            config = DatasetConfig(
                num_posts=5000 * args.scale_multiplier,
                num_users=int(5000 * args.scale_multiplier / args.posts_per_user),
                num_comments=int(5000 * args.scale_multiplier * args.comments_per_post),
            )
        else:
            config = DatasetConfig(
                num_posts=args.posts or 5000,
                num_users=args.users or 5000,
                num_comments=args.comments or 0,
            )

    return config

PROFILES = {
    'tiny': DatasetConfig(num_posts=100, num_users=50, num_comments=500),
    'dev': DatasetConfig(num_posts=5000, num_users=500, num_comments=25000),
    'staging': DatasetConfig(num_posts=100000, num_users=10000, num_comments=500000),
    'production': DatasetConfig(num_posts=1000000, num_users=100000, num_comments=5000000),
}

if __name__ == '__main__':
    main()
```

#### 3.2 Create `bulk_loader.py`

Handle efficient insertion:

```python
# database/seed-data/generator/bulk_loader.py

class BulkLoader:
    """Generate SQL/TSV for efficient bulk loading."""

    def __init__(self, output_dir: Path, format: str = 'both'):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.format = format

    def save(self, posts, users, comments):
        """Save to TSV and/or SQL."""

        if self.format in ['tsv', 'both']:
            self._save_tsv(posts, users, comments)

        if self.format in ['sql', 'both']:
            self._save_sql(posts, users, comments)

    def _save_tsv(self, posts, users, comments):
        """Save as TSV for COPY import (fastest)."""
        # Users
        with open(self.output_dir / 'users.tsv', 'w') as f:
            for user in users:
                f.write(f"{user.pk_user}\t{user.id}\t{user.email}\t...")

        # Posts
        with open(self.output_dir / 'posts.tsv', 'w') as f:
            for post in posts:
                f.write(f"{post.pk_post}\t{post.id}\t{post.fk_author}\t...")

        # Comments
        with open(self.output_dir / 'comments.tsv', 'w') as f:
            for comment in comments:
                f.write(f"{comment.pk_comment}\t{comment.id}\t...")

    def _save_sql(self, posts, users, comments):
        """Save as INSERT statements."""
        with open(self.output_dir / 'data.sql', 'w') as f:
            f.write("INSERT INTO tb_user (id, email, username, ...) VALUES\n")
            for i, user in enumerate(users):
                f.write(f"  ({user.values}){',\n' if i < len(users)-1 else ';\n'}")

            # ... similar for posts and comments

    def load_to_db(self, connection_str, posts, users, comments):
        """Load directly into PostgreSQL using COPY."""
        import psycopg

        with psycopg.connect(connection_str) as conn:
            with conn.cursor() as cur:
                # COPY is 10-100x faster than INSERT
                with open(self.output_dir / 'users.tsv') as f:
                    cur.copy_from(f, 'tb_user', columns=[...])

                with open(self.output_dir / 'posts.tsv') as f:
                    cur.copy_from(f, 'tb_post', columns=[...])

                with open(self.output_dir / 'comments.tsv') as f:
                    cur.copy_from(f, 'tb_comment', columns=[...])

            conn.commit()
```

---

### Phase 4: Integration & Testing (Week 2)

#### 4.1 Update `.gitignore`

```gitignore
# Git ignore generated datasets
database/seed-data/generated/
/tmp/velocitybench/

# But commit the gold corpus and configuration
!database/seed-data/gold-corpus/
!database/seed-data/generator/config.yaml
```

#### 4.2 Create `config.yaml`

```yaml
# database/seed-data/generator/config.yaml

# Gold corpus configuration
gold_corpus:
  posts_dir: "database/seed-data/gold-corpus/posts"
  users_file: "database/seed-data/gold-corpus/users_seed.json"
  categories_file: "database/seed-data/gold-corpus/categories_seed.json"
  num_seed_posts: 5000

# Output configuration
output:
  directory: "/tmp/velocitybench"
  format: "both"  # tsv, sql, or both

# Variant generation
variants:
  strategy: "lightweight"  # lightweight or full_mutation
  content_mutation_rate: 0.02  # 2% of posts get mutated
  date_spread_years: 5

# Profiles (preset scales)
profiles:
  tiny:
    num_posts: 100
    num_users: 50
    num_comments: 500

  dev:
    num_posts: 5000
    num_users: 500
    num_comments: 25000

  staging:
    num_posts: 100000
    num_users: 10000
    num_comments: 500000

  production:
    num_posts: 1000000
    num_users: 100000
    num_comments: 5000000

  custom:
    # Allow explicit overrides
    scale_multiplier: 200
```

#### 4.3 Create Test Suite

```python
# tests/test_dataset_scaling.py

def test_variant_generation():
    """Verify variants are created correctly."""
    seed_posts = load_test_posts(5)
    gen = VariantGenerator(seed_posts, multiplier=3)
    variants = gen.generate_variants()

    assert len(variants) == 15  # 5 seed × 3 multiplier
    assert variants[0].title != variants[1].title
    assert variants[0].slug != variants[1].slug
    assert variants[0].content == variants[1].content  # same body

def test_config_resolution():
    """Verify configuration is resolved correctly."""
    # Multiplier approach
    config1 = resolve_config(scale_multiplier=200)
    assert config1.num_posts == 1000000

    # Explicit sizes
    config2 = resolve_config(posts=1000000, users=100000)
    assert config2.num_posts == 1000000

    # Profile approach
    config3 = resolve_config(profile='production')
    assert config3.num_posts == 1000000

def test_bulk_output():
    """Verify TSV/SQL output is valid."""
    posts = generate_test_posts(100)
    loader = BulkLoader(Path('/tmp/test'))
    loader.save(posts, [], [])

    # Verify TSV can be imported
    assert (Path('/tmp/test') / 'posts.tsv').exists()
    # Verify rows match
    with open(Path('/tmp/test') / 'posts.tsv') as f:
        lines = f.readlines()
        assert len(lines) == 100
```

---

## Usage Examples

### Example 1: Generate 1M Posts (Production Scale)

```bash
cd database/seed-data/generator

# Generate using multiplier (simplest)
python scale_dataset.py --scale-multiplier 200 --output-dir /tmp/velocitybench

# Or using profile
python scale_dataset.py --profile production --output-dir /tmp/velocitybench

# Output:
#   ✅ Generated:
#     Posts:    1,000,000
#     Users:    100,000
#     Comments: 5,000,000
#     Output:   /tmp/velocitybench
```

### Example 2: Generate 100K Posts for Staging

```bash
python scale_dataset.py --posts 100000 --output-dir /tmp/staging

# Auto-scales users (10 posts per user) and comments (5 per post)
#   Posts:    100,000
#   Users:    10,000
#   Comments: 500,000
```

### Example 3: Load Directly to Database

```bash
python scale_dataset.py \
  --scale-multiplier 50 \
  --load \
  --connection "postgresql://user:pass@localhost/velocitybench"

# Generates AND loads to DB
```

### Example 4: Dev Environment (Tiny Dataset)

```bash
python scale_dataset.py --profile dev --output-dir ./generated

# Uses preset: 5K posts, 500 users, 25K comments
# Fast generation and small file sizes
```

---

## Architecture Benefits

### 1. Scalability ✅
- Generate 1K to 1M posts from same codebase
- Parameterized at three levels (multiplier, explicit, profile)
- No code changes needed for different scales

### 2. Git Efficiency ✅
- Only 5K seed posts in git (~500 MB)
- Generated datasets in `/tmp/` (ignored)
- Fast clones, quick builds

### 3. Reproducibility ✅
- Same seed = same gold corpus every time
- Same parameters = same variants every time
- Easy for CI/CD and team environments

### 4. Flexibility ✅
- Lightweight variants (200x scaling, no bloat)
- Optional content mutation for realism
- Multiple output formats (TSV, SQL)

### 5. Performance ✅
- Bulk insert via TSV + COPY (10-100x faster than row-by-row)
- Pre-generated slugs/IDs (no on-the-fly queries)
- Generators use iterators (memory-efficient)

---

## File Size Estimates

### Gold Corpus (Committed)
```
posts/       : 3-5 GB (5K markdown posts)
users.json   : 5 MB
categories   : 1 MB
Total        : ~5 GB (can be compressed to ~500 MB)
```

### Generated (Git-Ignored)
```
Production (1M posts):
  posts.tsv   : ~3 GB (text, slugs, metadata)
  users.tsv   : ~500 MB
  comments.tsv: ~5 GB
  Total       : ~8.5 GB

  Or SQL format:
  data.sql    : ~15-20 GB (less efficient)

Recommended: Use TSV + COPY, not SQL
```

---

## Integration with Existing System

### Keep Existing `load_blog_posts.py`

```python
# Refactor to use new system
from scale_dataset import scale_dataset
from bulk_loader import BulkLoader

def load_blog_posts(connection_str, scale='dev'):
    """Load blog posts at specified scale."""
    config = scale_dataset(profile=scale, output_dir='/tmp')
    loader = BulkLoader()
    loader.load_to_db(connection_str, config)
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Generate Test Dataset
  run: |
    cd database/seed-data/generator
    python scale_dataset.py --profile dev --load \
      --connection ${{ secrets.DATABASE_URL }}

# Quick (5 seconds): dev profile
# Full (30 seconds): staging profile
# Production setup: manual, uses production profile
```

---

## Success Criteria

- ✅ 5K gold corpus extracted and committed
- ✅ `scale_dataset.py` generates 1K-1M posts on-demand
- ✅ Generated files are git-ignored
- ✅ Parameterized (multiplier, explicit, profile)
- ✅ TSV format with COPY insertion (< 30 seconds for 1M posts)
- ✅ Tests verify variant generation and config resolution
- ✅ Documentation and usage examples

---

## Timeline

- **Week 1**:
  - Extract gold corpus (Phase 1)
  - Create variant generator (Phase 2)

- **Week 2**:
  - Create bulk loader (Phase 3)
  - Integration & testing (Phase 4)
  - Documentation

- **Week 3**:
  - Polish and optimization
  - CI/CD integration
  - Team training

---

## Next Steps

1. **Create Phase 1**: Extract and commit 5K gold corpus
2. **Create Phase 2**: Build variant generator
3. **Create Phase 3**: Build bulk loader and `scale_dataset.py`
4. **Create Phase 4**: Tests, integration, documentation
5. **Validate**: Generate at different scales and verify data quality

---

**Status**: Plan ready for implementation
**Estimated Effort**: 2-3 weeks
**Team**: 1-2 engineers
**Impact**: Unlimited dataset scaling with minimal git footprint
