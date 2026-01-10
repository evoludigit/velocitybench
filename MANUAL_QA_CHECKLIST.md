# VelocityBench - Manual QA Checklist

**Purpose**: Step-by-step verification of implementation
**Time Estimate**: 15-20 minutes
**Requires**: PostgreSQL database access

---

## Pre-Flight Checks

- [ ] PostgreSQL server is running and accessible
- [ ] User has `psql` command available
- [ ] Python 3.8+ installed and available
- [ ] Current directory is `/home/lionel/code/velocitybench`

---

## Section 1: File Verification (5 minutes)

### Code Files Exist
```bash
ls -l database/schema-template.sql
ls -l database/setup.py
ls -l frameworks/postgraphile/database/extensions.sql
ls -l frameworks/fraiseql/database/extensions.sql
ls -l scripts/run-benchmarks.py
```

**Checklist**:
- [ ] All 5 files exist
- [ ] All files have content (non-zero size)
- [ ] `setup.py` and `run-benchmarks.py` are executable

### Documentation Files Exist
```bash
ls -l README_ARCHITECTURE.md QUICK_START.md IMPLEMENTATION_GUIDE.md SESSION_SUMMARY.md QA_REPORT.md
```

**Checklist**:
- [ ] All 5 documentation files exist
- [ ] Each file has substantial content (>100 lines)

---

## Section 2: Python Validation (3 minutes)

### Syntax Check
```bash
python3 -m py_compile database/setup.py
python3 -m py_compile scripts/run-benchmarks.py
```

**Expected**: No output (success)

**Checklist**:
- [ ] `setup.py` compiles without errors
- [ ] `run-benchmarks.py` compiles without errors

### Import Check
```bash
python3 -c "import database.setup; print('setup.py OK')"
python3 -c "import scripts.run_benchmarks; print('run-benchmarks.py OK')"
```

**Expected**: Messages like "setup.py OK"

**Checklist**:
- [ ] Both scripts can be imported as modules

---

## Section 3: SQL Validation (3 minutes)

### Syntax Check (Schema Template)
```bash
head -50 database/schema-template.sql
grep -c "CREATE TABLE" database/schema-template.sql
grep -c "CREATE INDEX" database/schema-template.sql
```

**Expected**:
- First 50 lines show table definitions
- At least 5 CREATE TABLE statements
- Multiple CREATE INDEX statements

**Checklist**:
- [ ] schema-template.sql starts with comments
- [ ] Contains CREATE TABLE for tb_user, tb_post, tb_comment
- [ ] Contains CREATE INDEX statements

### Trinity Pattern Verification
```bash
grep "pk_user SERIAL PRIMARY KEY" database/schema-template.sql
grep "id UUID UNIQUE NOT NULL" database/schema-template.sql
grep "fk_author INTEGER NOT NULL" database/schema-template.sql
```

**Expected**: Each command shows one match

**Checklist**:
- [ ] tb_user has pk_user SERIAL PRIMARY KEY
- [ ] tb_post has id UUID UNIQUE NOT NULL
- [ ] tb_post has fk_author INTEGER NOT NULL

### FraiseQL Views Verification
```bash
grep -c "CREATE OR REPLACE VIEW v_" frameworks/fraiseql/database/extensions.sql
grep -c "CREATE OR REPLACE VIEW tv_" frameworks/fraiseql/database/extensions.sql
```

**Expected**:
- 3 projection views (v_user, v_post, v_comment)
- 3 composition views (tv_user, tv_post, tv_comment)

**Checklist**:
- [ ] 3 v_* projection views exist
- [ ] 3 tv_* composition views exist

### PostGraphile Smart Tags Verification
```bash
grep -c "COMMENT ON COLUMN" frameworks/postgraphile/database/extensions.sql
grep "@omit all" frameworks/postgraphile/database/extensions.sql | head -5
```

**Expected**:
- Multiple COMMENT ON statements
- @omit directives visible

**Checklist**:
- [ ] PostGraphile has smart tag comments
- [ ] @omit directives are present

---

## Section 4: Architecture Validation (4 minutes)

### Database Setup Script Functionality
```bash
python3 database/setup.py --help 2>/dev/null || \
python3 database/setup.py 2>&1 | head -20
```

**Expected**: Help output or usage information

**Checklist**:
- [ ] Script has main() function
- [ ] Script handles command-line arguments

### Test Runner Script Functionality
```bash
python3 scripts/run-benchmarks.py --help 2>/dev/null || \
python3 scripts/run-benchmarks.py 2>&1 | head -20
```

**Expected**: Help output or usage information

**Checklist**:
- [ ] Script has main() function
- [ ] Script validates frameworks

---

## Section 5: Documentation Quality (2 minutes)

### README_ARCHITECTURE.md
```bash
head -20 README_ARCHITECTURE.md
grep -c "Quick Navigation\|For Users\|For Architects" README_ARCHITECTURE.md
```

**Expected**: Navigation section with role-based guidance

**Checklist**:
- [ ] Clear role-based navigation
- [ ] Links to other documents
- [ ] Purpose clearly stated

### QUICK_START.md
```bash
grep -c "TL;DR\|Setup\|Test\|Debug" QUICK_START.md
```

**Expected**: Multiple sections covering key tasks

**Checklist**:
- [ ] Has quick commands
- [ ] Has troubleshooting section
- [ ] Clear and concise

### IMPLEMENTATION_GUIDE.md
```bash
grep -c "Phase\|Trinity Pattern\|Adding a New Framework" IMPLEMENTATION_GUIDE.md
```

**Expected**: Multiple phases and frameworks discussed

**Checklist**:
- [ ] Covers implementation phases
- [ ] Explains Trinity Pattern
- [ ] Has framework addition guide

---

## Section 6: Content Validation (3 minutes)

### Schema Template Completeness
```bash
grep "CREATE TABLE IF NOT EXISTS" database/schema-template.sql
```

**Expected**: tb_user, tb_post, tb_comment, categories, post_categories, user_follows, post_likes, user_profiles

**Checklist**:
- [ ] All 8 tables defined
- [ ] Supporting tables present
- [ ] Foreign keys properly configured

### Extension Completeness
```bash
ls -la frameworks/*/database/extensions.sql | wc -l
```

**Expected**: At least 2 (PostGraphile, FraiseQL)

**Checklist**:
- [ ] PostGraphile extensions file exists
- [ ] FraiseQL extensions file exists

### Documentation Consistency
```bash
grep -l "VelocityBench\|Trinity Pattern\|Sequential" *.md | wc -l
```

**Expected**: Multiple files reference key concepts

**Checklist**:
- [ ] Key terms used consistently
- [ ] Cross-references between documents

---

## Section 7: Integration Check (2 minutes)

### Schema Template References in Setup
```bash
grep "schema-template.sql" database/setup.py
```

**Expected**: References to schema-template.sql

**Checklist**:
- [ ] Setup script references schema template
- [ ] File path is correct

### Framework Detection in Test Runner
```bash
grep -c "package.json\|requirements.txt\|Gemfile\|pom.xml" scripts/run-benchmarks.py
```

**Expected**: Multiple framework types detected

**Checklist**:
- [ ] Node.js detection present
- [ ] Python detection present
- [ ] Ruby detection present
- [ ] Java detection present

---

## Section 8: Production Readiness (3 minutes)

### Error Handling Present
```bash
grep -c "try:\|except\|if not\|logging" database/setup.py scripts/run-benchmarks.py
```

**Expected**: Multiple error handling patterns

**Checklist**:
- [ ] Try/except blocks present
- [ ] Validation logic present
- [ ] Logging/output present

### Configuration Support
```bash
grep -c "os.getenv\|environment\|ENV\|config" database/setup.py scripts/run-benchmarks.py
```

**Expected**: Environment variable usage

**Checklist**:
- [ ] Database credentials configurable
- [ ] Timeout configurable
- [ ] Default values provided

### Documentation in Code
```bash
grep -c "def \|class \|'''\|\"\"\"" database/setup.py | head -1
```

**Expected**: Docstrings present

**Checklist**:
- [ ] Classes documented
- [ ] Methods documented
- [ ] Parameters described

---

## Summary

After completing all sections above, record results:

**Total Checks**: _____ / 50

**Sections Passed**:
- [ ] Section 1: File Verification (8 checks)
- [ ] Section 2: Python Validation (3 checks)
- [ ] Section 3: SQL Validation (6 checks)
- [ ] Section 4: Architecture Validation (2 checks)
- [ ] Section 5: Documentation Quality (3 checks)
- [ ] Section 6: Content Validation (3 checks)
- [ ] Section 7: Integration Check (2 checks)
- [ ] Section 8: Production Readiness (3 checks)

**Overall Result**: 
- [ ] **✅ PASS** - All checks passed, ready for production
- [ ] **⚠️ WARN** - Some checks failed, review needed
- [ ] **❌ FAIL** - Critical checks failed, do not deploy

**Issues Found**:
```
[List any issues discovered]
```

**Sign-Off**:
- Checked by: _________________
- Date: _________________
- Approved: [ ] Yes [ ] No

---

## Next Steps After QA

If all checks pass:
1. Proceed with `python database/setup.py postgraphile` test
2. Proceed with database connectivity verification
3. Proceed with framework test execution

If any checks fail:
1. Document issues in QA_REPORT.md
2. Request code review
3. Fix issues
4. Re-run QA checklist

