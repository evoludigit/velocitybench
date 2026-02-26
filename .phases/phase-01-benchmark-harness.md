# Phase 1: Benchmark Harness & Diagnostics

## Objective

Improve the benchmark harness so that when frameworks fail, we know exactly *why* — and extend the query coverage to include deep nesting and mutations.

## Current Problems

1. `bench_sequential.py` silently swallows errors — a 97% error rate gives no clue whether the issue is connection refused, HTTP 500, malformed JSON, or GraphQL `errors` array
2. REST error detection only checks HTTP status (no body validation)
3. Missing Q3 (deep nesting: `comments → author + post`) and M1 (mutations) from sequential benchmark
4. No `make status` command for quick health overview

## Tasks

### 1.1 Add Diagnostic Logging to bench_sequential.py

**File:** `tests/benchmark/bench_sequential.py`

**Changes:**
- In `_post_graphql()` (around line 509): Log the first error response body when a framework starts failing. Capture up to 3 sample error responses per framework per query.
- In `_get_rest()` (around line 529): Parse response body and validate JSON structure. Log non-200 status codes and malformed responses.
- Add a `--verbose` / `-v` CLI flag that dumps all error samples to stderr.
- Add a `--diagnose` flag that runs 5 requests per query at concurrency=1 before the full benchmark, printing full request/response pairs for any failures.

**Error categorization to add:**
```
- connection_refused: urllib.error.URLError with ConnectionRefusedError
- timeout: urllib.error.URLError with timeout
- http_error: HTTP status != 200 (log status code)
- json_error: Response body is not valid JSON (log first 200 chars)
- graphql_error: Valid JSON but has "errors" key (log first error message)
- missing_data: Valid JSON but no "data" key
```

**Output enhancement:**
- Add error breakdown column to Markdown report: instead of just "47.0%", show "47.0% (graphql_error: 45%, timeout: 2%)"
- Keep existing format as default, add `--detailed-errors` for the breakdown

### 1.2 Add Q3 Deep Nesting Query

**File:** `tests/benchmark/bench_sequential.py`

**Add to query constants (after line 48):**
```python
_GQL_Q3 = "{ comments(limit: 20) { id content author { username } post { title } } }"
```

**Add Q3 to every GraphQL framework entry in FRAMEWORKS dict:**
- For each GraphQL framework, add `"Q3": ("<url>", _GQL_Q3)`
- For REST frameworks, add equivalent: `"Q3": "<url>/comments?limit=20&include=author,post"`
- Mark Q3 as `None` for frameworks that don't support comment queries

**Add Q3 table to report output** (after Q2b section).

### 1.3 Add M1 Mutation Query

**File:** `tests/benchmark/bench_sequential.py`

**Add mutation constant:**
```python
_GQL_M1 = '''mutation { updateUser(id: "<test-user-uuid>", input: { bio: "bench" }) { id bio } }'''
```

**Implementation notes:**
- Need to discover a valid user UUID during the warmup phase
- Run Q1 first, extract first user's ID, use it for M1
- For REST: `PUT <url>/users/<uuid>` with `{"bio": "bench"}`
- M1 should be optional (not all frameworks implement mutations yet)

### 1.4 Add `make status` Target

**File:** `make/framework.mk`

**Behavior:**
```bash
$ make status
Framework Health Check (2026-02-25)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Framework            │ Container │ Health │ Q1 Smoke │ Type
──────────────────────┼───────────┼────────┼──────────┼─────────
 actix-web-rest       │ ✓ UP      │ ✓ 200  │ ✓ OK     │ REST
 async-graphql        │ ✓ UP      │ ✓ 200  │ ✓ OK     │ GraphQL
 apollo-server        │ ✗ DOWN    │ —      │ —        │ GraphQL
 ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Summary: 11/33 healthy
```

**Implementation:** Simple bash script that:
1. Checks `docker compose ps` for container status
2. Curls each health endpoint
3. Sends one Q1 query and checks for errors
4. Prints summary table

### 1.5 REST Response Body Validation

**File:** `tests/benchmark/bench_sequential.py`

**Change `_get_rest()`** to parse JSON and validate basic structure:
```python
body = json.loads(data)
# Check that response contains expected keys (users/posts/comments)
ok = resp.status == 200 and isinstance(body, (dict, list))
```

This ensures REST frameworks returning HTML error pages or empty bodies are caught.

## Verification

- [ ] `bench_sequential.py --diagnose --frameworks fraiseql-tv` shows full request/response for 5 queries
- [ ] `bench_sequential.py --verbose` logs error samples for failing frameworks
- [ ] Q3 column appears in benchmark report for GraphQL frameworks
- [ ] `make status` produces readable health table
- [ ] REST error detection catches non-JSON responses
