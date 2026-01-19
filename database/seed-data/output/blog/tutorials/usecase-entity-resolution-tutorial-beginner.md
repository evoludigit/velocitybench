```markdown
# **Entity Resolution Patterns: Matching and Merging Duplicates in Your Database**

*How to manage data consistency when the same real-world entity appears in your database under different IDs—without manual workarounds.*

---

## **Introduction**

Imagine this: your users can sign up using **email, phone, or social media**, and sometimes the same person registers multiple times—each time with a unique ID in your database. Or perhaps your e-commerce system imports products from multiple suppliers, and the same item gets listed with different SKUs, prices, and descriptions. Without a system to **detect and merge these duplicates**, your data becomes messy, your analytics unreliable, and your users frustrated.

This is the **entity resolution problem**—and it’s more common than you think. Whether you're building a customer database, a product catalog, or a recommendation engine, you’ll eventually need a way to:

- **Find duplicates** (e.g., "Is this user’s email `john@example.com` the same as `john.doe@example.com`?")
- **Determine which version is "correct"** (if any)
- **Merge them into a single record** without losing data

In this post, we’ll explore **practical entity resolution patterns**—from simple fuzzy matching to advanced probabilistic approaches—using real-world examples in **SQL and Python**. We’ll cover tradeoffs, pitfalls, and when to use each technique.

---

## **The Problem: Why Entity Resolution is Hard**

Entity resolution (also called **record linkage** or **deduplication**) is tricky because:

### **1. Silent Data Duplication**
Duplicates often introduce **two copies of the same data**, leading to:
- **Inconsistent reports** (e.g., "John Doe" appears twice in analytics)
- **Wasted storage** (duplicate records take up space)
- **Confused users** (e.g., "Why do I have two accounts?")
- **Broken calculations** (e.g., inventory counts double)

#### **Example: E-Commerce Inventory**
```sql
-- Two records for the same product, but different SKUs and prices
SELECT * FROM products WHERE sku IN ('P123', 'SKU-456');
```
| sku  | name          | price | supplier_id |
|------|---------------|-------|-------------|
| P123 | "Wireless Headphones" | 99.99 | 101         |
| SKU-456 | "Wireless Headphones - Noise Cancelling" | 89.99 | 102  |

**Problem:** These are the same product, but different suppliers listed them differently.

---

### **2. The "Partial Match" Dilemma**
Real-world data is **messy**:
- **Typos:** `john.doe@example.com` vs. `john@doe.com`
- **Formatting differences:** `123 Main St` vs. `123, Main St.`
- **Missing data:** One record has a phone number; another doesn’t.
- **Context matters:** `Apple Inc.` (tech company) vs. `Apple` (fruit).

A simple exact-match query (`WHERE email = 'john@example.com'`) fails when the data isn’t perfect.

---

### **3. The "Correct Version" Paradox**
Even if you find duplicates, **which record should "win"?**
- Should you **merge all fields** (risking data loss)?
- Should you **pick a canonical source** (e.g., newest record)?
- Should you **flag them as duplicates** without merging?

---

## **The Solution: Entity Resolution Patterns**

There’s no one-size-fits-all solution, but here are **five practical patterns** to handle entity resolution, ranked from **simplest to most advanced**:

1. **Exact Matching (Fast but Too Strict)**
2. **Fuzzy Matching (Flexible but Approximate)**
3. **Graph-Based Linking (Scalable for Large Datasets)**
4. **Probabilistic Record Linkage (Statistical Confidence)**
5. **Hybrid Approaches (Combining Rules + ML)**

We’ll dive into the first three with **code examples**, then discuss tradeoffs.

---

## **1. Exact Matching: The Simple (But Limited) Baseline**

**When to use:**
- When data is **clean and consistent** (e.g., internal systems with controlled inputs).
- For **initial filtering** before applying fuzzier methods.

**How it works:**
Compare attributes **exactly** (e.g., `email = 'john@example.com'`). If two records match all key fields, they’re duplicates.

### **Example: SQL Query for Exact Duplicates**
```sql
-- Find users with the same email (exact match)
SELECT u1.id, u2.id
FROM users u1
JOIN users u2 ON u1.email = u2.email AND u1.id < u2.id;
```
**Limitations:**
- **Fails on typos** (e.g., `john.doe@example.com` vs. `john@doe.com`).
- **No flexibility** for reformatting (e.g., `123 Main St` vs. `123 Main Street`).

---

## **2. Fuzzy Matching: Handling Messy Data**

**When to use:**
- When data has **typos, formatting variations, or partial matches**.
- For **high-recall scenarios** (better to flag "maybe duplicates" than miss them).

**Approaches:**
| Technique          | Use Case                          | Example Tools/Libraries          |
|--------------------|-----------------------------------|----------------------------------|
| **Levenshtein Distance** | Measures edit distance (e.g., "kitten" vs. "sitting") | `python-Levenshtein`, `fuzzywuzzy` |
| **Soundex/Metaphone** | Similar-sounding names (e.g., "Smith" vs. "Smythe") | `python-soundex` |
| **Token-Based Matching** | Splits text into words (e.g., "Wireless Headphones" vs. "headphones wireless") | `spaCy`, `NLTK` |
| **Regular Expressions** | Wildcard matching (e.g., `email.*@example\.com`) | SQL `LIKE`, Python `re` |

### **Example: Fuzzy Email Matching (Python)**
```python
from fuzzywuzzy import fuzz

def are_emails_similar(email1, email2, threshold=80):
    return fuzz.ratio(email1.lower(), email2.lower()) >= threshold

# Example usage
print(are_emails_similar("john.doe@example.com", "john@doe.com"))  # True (90% similarity)
print(are_emails_similar("jane@example.com", "jane.smith@example.org"))  # False (55%)
```

### **Example: SQL with Soundex for Names**
```sql
-- Find users with similar-sounding names using SQL's Soundex (PostgreSQL)
SELECT u1.id, u2.id, soundex(u1.name) = soundex(u2.name)
FROM users u1
JOIN users u2 ON u1.id < u2.id
WHERE soundex(u1.name) = soundex(u2.name);
```
**Tradeoffs:**
✅ **Catches typos and reformatting.**
❌ **Can produce false positives** (e.g., `John Doe` vs. `Jane Doe`).
❌ **Performance overhead** (fuzzy matching is slower than exact matching).

---

## **3. Graph-Based Linking: Scaling to Large Datasets**

**When to use:**
- When you have **millions of records** and need **scalable deduplication**.
- When duplicates form **clusters** (e.g., a user has 3 accounts, each matching 2 others).

**How it works:**
1. **Build a graph** where nodes = records, edges = similarity scores.
2. **Find connected components** (groups of highly similar records).
3. **Merge or flag duplicates** within each component.

### **Example: Building a Similarity Graph (Python)**
```python
import networkx as nx
from fuzzywuzzy import fuzz

# Create a graph
G = nx.Graph()

# Add nodes (users)
users = [
    {"id": 1, "email": "john@example.com"},
    {"id": 2, "email": "john.doe@example.com"},
    {"id": 3, "email": "jane@example.com"},
]

for user in users:
    G.add_node(user["id"], **user)

# Add edges based on fuzzy matching
for i in range(len(users)):
    for j in range(i + 1, len(users)):
        similarity = fuzz.ratio(users[i]["email"], users[j]["email"])
        if similarity > 80:
            G.add_edge(users[i]["id"], users[j]["id"], weight=similarity)

# Find connected components (duplicate groups)
duplicate_groups = list(nx.connected_components(G))
print(duplicate_groups)  # Output: [[1, 2], [3]]
```

### **Visualizing the Graph**
```python
import matplotlib.pyplot as plt

pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_size=1000)
plt.show()
```
**Tradeoffs:**
✅ **Handles large datasets** (scalable with graph algorithms).
✅ **Captures complex relationships** (e.g., A→B, B→C implies A→C).
❌ **Computationally expensive** (O(n²) for pairwise comparisons).
❌ **Requires tuning similarity thresholds**.

---

## **4. Probabilistic Record Linkage (The Gold Standard)**

**When to use:**
- When you need **high accuracy** (e.g., healthcare, finance).
- When duplicates follow **statistical patterns** (e.g., 90% of matching pairs share a name + address).

**How it works:**
Use **Bayesian probability** to calculate the likelihood that two records refer to the same real-world entity. Common algorithms:
- **Jaro-Winkler Distance** (better for short strings like names).
- **Blockers** (pre-filter unlikely pairs, e.g., same first name).

### **Example: Blocking + Jaro-Winkler (Python)**
```python
from jeroenjanssens.dedupe import Dataset, Feature, Classifier

# Define features (columns to compare)
features = [
    Feature("email", weight=0.8),
    Feature("name", weight=0.5),
]

# Create a dataset
dataset = Dataset(features)
dataset.add_model("name_blocker", "name", "name")

# Train a classifier (in practice, you'd train on labeled data)
classifier = Classifier(dataset)
classifier.train([{"email": ["john@example.com", "john.doe@example.com"], "name": ["John Doe", "John Doe"]}])

# Predict duplicates
pairs = classifier.detect(dataset)
print(pairs)
```
**Tradeoffs:**
✅ **Highest accuracy** (statistically sound).
❌ **Requires labeled training data** (or domain expertise to set weights).
❌ **Slower than fuzzy matching** (due to probabilistic calculations).

---

## **5. Hybrid Approaches: Best of Both Worlds**

Combine **rules + machine learning** for robustness:
1. **Rule-based filtering** (e.g., "only compare emails from the same domain").
2. **ML for similarity scoring** (e.g., a neural network ranks candidate duplicates).

### **Example: Rule + Fuzzy Hybrid (SQL)**
```sql
-- Step 1: Rule-based blocking (only compare emails from example.com)
WITH same_domain AS (
    SELECT u1.id, u2.id
    FROM users u1
    JOIN users u2 ON u1.email LIKE '%@example.com'
        AND u2.email LIKE '%@example.com'
        AND u1.id < u2.id
),
-- Step 2: Fuzzy matching on limited fields
fuzzy_matches AS (
    SELECT u1.id, u2.id,
           SIMILARITY(u1.name, u2.name) AS name_similarity
    FROM same_domain
)
-- Step 3: Flag high-confidence duplicates
SELECT * FROM fuzzy_matches
WHERE name_similarity > 0.8;
```

---

## **Implementation Guide: Step-by-Step**

Here’s how to **build a deduplication system** for a real-world scenario (e.g., a user database):

### **Step 1: Identify Key Attributes**
Choose fields that are **likely to match for duplicates**:
- `email`
- `phone` (if available)
- `name` (first + last)
- `address` (for geolocation-basedapps)

```sql
-- Example: Find potential duplicates based on email + name
SELECT u1.id, u2.id
FROM users u1
JOIN users u2 ON
    -- Rule 1: Same domain
    SUBSTRING(u1.email FROM '[^@]+@') = SUBSTRING(u2.email FROM '[^@]+@')
    -- Rule 2: Name similarity > 80%
    AND SIMILARITY(u1.name, u2.name) > 0.8
    AND u1.id < u2.id;
```

### **Step 2: Choose a Matching Strategy**
| Scenario               | Recommended Approach          |
|------------------------|--------------------------------|
| Small dataset (<10K)   | Fuzzy matching (Python/SQL)   |
| Large dataset (>100K)  | Graph-based linking           |
| High-stakes data       | Probabilistic record linkage   |
| Mixed data quality     | Hybrid (rules + fuzzy)         |

### **Step 3: Implement Merging Logic**
Decide how to **combine duplicates**. Options:
1. **Merge into a "canonical" record** (e.g., newest or most complete).
2. **Store as a linked list** (keep all versions but track relationships).
3. **Flag as duplicates** (non-destructive).

#### **Example: Merging Users in SQL**
```sql
-- Merge users by creating a "merged_by" field and copying data
WITH duplicates AS (
    SELECT u1.id AS keep_id, u2.id AS discard_id
    FROM users u1
    JOIN users u2 ON u1.email = u2.email AND u1.id < u2.id
)
UPDATE discard
SET merged_by = (SELECT keep_id FROM duplicates WHERE discard_id = discard.id),
    is_duplicate = TRUE;
```

### **Step 4: Automate and Monitor**
- **Schedule regular runs** (e.g., weekly deduplication job).
- **Log false positives/negatives** to improve the model.
- **Alert on anomalies** (e.g., "10 new duplicate pairs detected").

---

## **Common Mistakes to Avoid**

1. **Ignoring Data Quality First**
   - **Fix source systems** (e.g., standardize email formats at signup) before deduplication.
   - Example: If users enter `123 Main St` or `123 Main Street`, **store them consistently**.

2. **Over-Merging**
   - **Don’t merge unrelated records** (e.g., `John Doe` vs. `Jane Doe`).
   - **Use confidence thresholds** (e.g., only merge if similarity > 90%).

3. **Forgetting to Preserve Data**
   - **Always back up before merging.**
   - **Store metadata** (e.g., `merged_by_id`, `merger_timestamp`).

4. **Performance Pitfalls**
   - **Avoid O(n²) algorithms** for large datasets (use blocking or sampling).
   - **Cache results** (e.g., pre-compute similarity scores).

5. **Assuming "Exact Match" is Enough**
   - **Real-world data isn’t perfect.** Start with fuzzy methods even if your data *feels* clean.

---

## **Key Takeaways**

✅ **Entity resolution is about tradeoffs:**
- **Speed vs. Accuracy:** Exact matching is fast but misses duplicates; fuzzy matching is slower but catches more.
- **Manual vs. Automated:** Rules work for simple cases; ML shines for complex patterns.

🔍 **Start simple:**
1. Use **exact matching** for clean data.
2. Add **fuzzy matching** for typos/reformatting.
3. Scale with **graph-based** or **probabilistic** methods.

🛠 **Tools to Leverage:**
- **SQL:** `SIMILARITY`, `SOUNDEX`, `LIKE` with wildcards.
- **Python:** `fuzzywuzzy`, `networkx`, `dedupe`.
- **Databases:** PostgreSQL (with `fuzzystrmatch`), Elasticsearch (for text search).

🚀 **Next Steps:**
- **Profile your data:** What are the most common duplicate patterns?
- **Start small:** Deduplicate one table before scaling.
- **Iterate:** Refine your rules based on false positives/negatives.

---

## **Conclusion**

Entity resolution is **not a one-time task**—it’s an ongoing process to keep your data clean. Whether you’re dealing with user accounts, product catalogs, or sensor data, **duplicates will appear**, but with the right patterns, you can handle them systematically.

**Start with fuzzy matching** for flexibility, **scale with graphs** for large datasets, and **add probabilistic methods** when accuracy is critical. And remember: **data quality is an investment, not a cost.**

---
**Further Reading:**
- ["Record Linkage" by Peter Christen](https://www.dcs.gla.ac.uk/~petec/MLS07/RecordLinkage.pdf) (Academic paper)
- [Elasticsearch Fuzziness](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-fuzzy-query.html) (For search-based deduplication)
- [Google’s BigQuery Entity Matching](https://cloud.google.com/bigquery/docs/reference/standard-sql/ entity-matching) (Serverless option)

**What’s your biggest entity resolution challenge?** Share in the comments—I’d love to hear how you tackle duplicates in your systems!