# Dataset Scaling Plan - Executive Summary

**Date**: 2026-01-13
**Commit**: b7ca83d
**Status**: ✅ Plan Complete - Ready for Implementation

---

## The Goal

Scale VelocityBench dataset from **3,369 blog posts** to **1M posts** without bloating git.

**Key Constraint**: Generated data is created on-demand, not committed. Only the "gold corpus" is in git.

---

## The Strategy: 5K Gold Corpus + 200x Variants

### Step 1: Extract Gold Corpus (Committed to Git)
- Take best 5K posts from existing 3,369
- Save as high-quality seed corpus
- ~500 MB compressed, included in repo

### Step 2: Generate Variants (Git-Ignored)
- For each of 5K posts, create 200 lightweight variants
- **5,000 seed posts × 200 variants = 1,000,000 posts**
- Variants differ in:
  - Title (add suffixes: "(2026)", "(Beginner)", "(Cheat Sheet)")
  - Slug (`original-slug-0` to `original-slug-199`)
  - Published date (spread over 5-10 years)
  - Author (rotate through 100K users)
  - Tags/categories (recombine)
  - Status (70% published, 30% draft)
  - Metrics (random views, likes, bookmarks)
- **Body stays the same** (or lightly mutated at 2% rate)

### Step 3: Parameterized Generation
Generate at any scale with simple commands:

```bash
# Simple: Use multiplier
python scale_dataset.py --scale-multiplier 200

# Flexible: Explicit sizes
python scale_dataset.py --posts 1000000 --users 100000 --comments 5000000

# Preset: Use profiles
python scale_dataset.py --profile production  # 1M posts, 100K users, 5M comments
python scale_dataset.py --profile dev        # 5K posts, 500 users, 25K comments
python scale_dataset.py --profile tiny       # 100 posts (instant, for testing)
```

### Step 4: Efficient Output
- Generate as **TSV files** (not SQL)
- Use PostgreSQL `COPY` for bulk insert (10-100x faster)
- < 30 seconds to load 1M posts into database

---

## Architecture

### Directory Structure

```
database/seed-data/
  gold-corpus/              # Committed to git (~500 MB)
    posts/                  # 5000 markdown files
    users_seed.json         # 5000 canonical users
    categories_seed.json    # Tag taxonomy
    metadata.yaml

  generated/                # Git-ignored
    users.tsv
    posts.tsv
    comments.tsv
    data.sql                # Alternative format

  generator/
    scale_dataset.py        # Main entry point
    variant_generator.py    # Create variants
    bulk_loader.py          # Output TSV/SQL
    config.yaml             # Configuration
```

### Three Configuration Levels

**Level 1: Multiplier (Simplest)**
```python
--scale-multiplier 200
# Result: 5K × 200 = 1M posts
# Users & comments auto-scale proportionally
```

**Level 2: Explicit (Most Flexible)**
```python
--posts 1000000 --users 100000 --comments 5000000
# Specify exactly what you want
```

**Level 3: Profiles (Presets)**
```python
--profile production  # Uses preset config
--profile staging     # 100K posts, 10K users
--profile dev         # 5K posts, 500 users (fast)
--profile tiny        # 100 posts (instant)
```

---

## Implementation Phases

### Phase 1: Extract Gold Corpus (Week 1)
- Identify best 5K posts from 3,369
- Create `users_seed.json` and `categories_seed.json`
- Commit to git

### Phase 2: Build Variant Generator (Week 1-2)
- Create `VariantGenerator` class
- Implement title mutations, date spreading, author rotation, etc.
- Generate 200 variants per seed post

### Phase 3: Build Bulk Loader (Week 2)
- Create `BulkLoader` class
- Output TSV format
- Support SQL output (slower, but compatible)
- Implement PostgreSQL COPY loading

### Phase 4: Integration & Testing (Week 2-3)
- Update `.gitignore` for `/tmp/velocitybench` and `generated/`
- Create test suite
- CI/CD integration
- Documentation

---

## Key Features

### 1. Scalability ✅
- 1K to 1M posts with same code
- Parameterized at three levels
- No code changes needed

### 2. Git Efficiency ✅
- Only 5K seed posts in git
- Generated data stays in `/tmp/` (git-ignored)
- Fast clones, small repository

### 3. Reproducibility ✅
- Fixed Faker seed = same users every time
- Same parameters = same variants every time
- Perfect for CI/CD and teams

### 4. Lightweight Variants ✅
- 200x scaling without bloat
- Same body (or 2% content mutation)
- Different metadata = different query patterns
- Realistic distributions (70% published, 30% draft, etc.)

### 5. Fast Loading ✅
- TSV format with PostgreSQL COPY
- 10-100x faster than row-by-row INSERT
- 1M posts loaded in < 30 seconds

---

## File Sizes

### Gold Corpus (Committed)
```
5K markdown posts:   3-5 GB (or ~500 MB compressed)
users_seed.json:     5 MB
categories.json:     1 MB
Total:               ~5 GB (or ~500 MB compressed)
```

### Generated (Git-Ignored)
```
Production (1M posts):
  posts.tsv:         ~3 GB
  users.tsv:         ~500 MB
  comments.tsv:      ~5 GB
  Total:             ~8.5 GB

Dev (5K posts):
  posts.tsv:         ~15 MB
  users.tsv:         ~2.5 MB
  comments.tsv:      ~75 MB
  Total:             ~100 MB
```

---

## Usage Examples

### Generate 1M Posts (Production)
```bash
python scale_dataset.py --scale-multiplier 200 --output-dir /tmp/velocitybench
# Result: 1M posts, 100K users, 5M comments (generated in ~2 min)
```

### Load to Database
```bash
python scale_dataset.py \
  --scale-multiplier 200 \
  --load \
  --connection "postgresql://user:pass@localhost/velocitybench"
# Result: Database populated in < 30 seconds
```

### Dev Environment (Quick)
```bash
python scale_dataset.py --profile dev --load
# Result: 5K posts, 500 users, 25K comments (< 5 seconds)
```

### Staging (Medium)
```bash
python scale_dataset.py --posts 100000 --load
# Auto-scales: 100K posts, 10K users, 500K comments
```

---

## Integration with Existing Code

### Keep `load_blog_posts.py`
Refactor to use new system:

```python
def load_blog_posts(connection_str, scale='dev'):
    from scale_dataset import scale_dataset
    config = scale_dataset(profile=scale)
    loader.load_to_db(connection_str, config)
```

### CI/CD Integration
```yaml
# Generate and load test dataset automatically
- name: Setup Test Database
  run: |
    cd database/seed-data/generator
    python scale_dataset.py --profile dev --load
```

---

## Success Criteria

- ✅ 5K gold corpus extracted and committed
- ✅ `scale_dataset.py` generates 1K-1M posts
- ✅ Git-ignored generated files
- ✅ Parameterized (multiplier/explicit/profile)
- ✅ TSV + COPY loading (< 30 seconds for 1M)
- ✅ Test suite (variants, config, output)
- ✅ Documentation complete
- ✅ CI/CD integration working

---

## Timeline

- **Week 1**: Extract gold corpus + build variant generator
- **Week 2**: Build bulk loader + integration
- **Week 2-3**: Testing, CI/CD, documentation

**Total**: 2-3 weeks, 1-2 engineers

---

## Key Decisions Made

1. **TSV + COPY** (not SQL INSERT)
   - 10-100x faster
   - PostgreSQL native bulk loading

2. **Lightweight variants** (not full rewrites)
   - Same body, different metadata
   - Realistic query patterns
   - 200x scaling without content bloat

3. **Three config levels** (not just one)
   - Multiplier: Simple (`--scale-multiplier 200`)
   - Explicit: Flexible (`--posts 1000000`)
   - Profiles: Preset (`--profile production`)

4. **Git-ignored generated data**
   - Only gold corpus committed
   - Generated on-demand
   - Fast clones, small repo

---

## Next Steps

1. **Review plan** with team (this document)
2. **Start Phase 1**: Extract gold corpus
3. **Code review** after each phase
4. **Test at each phase**: Verify output quality
5. **Document as you go**: Keep examples updated

---

## FAQ

**Q: Won't variants with same body be unrealistic?**
A: No. Query patterns depend on metadata (tags, dates, authors, status), not body text. Same body with different metadata creates realistic join patterns, filtering, and pagination behaviors.

**Q: How do we ensure reproducibility?**
A: Fixed Faker seed (42) + same parameters = same output every time. Perfect for CI/CD.

**Q: Can we switch between scales easily?**
A: Yes. Just change `--scale-multiplier` (or profile). Same code, different output.

**Q: Why commit gold corpus but not generated data?**
A: Because gold corpus is stable (high-quality, reviewed) but generated variants are disposable (recreated each time). Keeps repo small while ensuring reproducibility.

**Q: How fast is loading?**
A: TSV + COPY: ~30 seconds for 1M posts. SQL INSERT: ~10 minutes (we won't use this).

---

**Status**: Plan ready for implementation
**Commit**: b7ca83d
**Next**: Review with team, start Phase 1
