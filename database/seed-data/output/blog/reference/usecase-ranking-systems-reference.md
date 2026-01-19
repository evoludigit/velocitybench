---
# **[Pattern] Ranking Systems Patterns – Reference Guide**

---

## **Overview**
Ranking Systems Patterns define structured approaches to scoring, prioritizing, and ordering items based on predefined rules, weights, or dynamic algorithms. These patterns are essential for applications requiring ranked results, such as recommendation engines, search relevance, leaderboards, or business insights. This guide categorizes common ranking patterns, their implementations, and key considerations to ensure scalability, fairness, and adaptability in various domains.

---

## **Schema Reference**

| **Pattern Name**               | **Use Case**                          | **Core Components**                                                                 | **Key Metrics**                          | **Implementation Challenges**                     |
|---------------------------------|---------------------------------------|--------------------------------------------------------------------------------------|------------------------------------------|---------------------------------------------------|
| **Weighted Scoring**           | Assign fixed weights to criteria     | - Criteria (e.g., price, reviews, recency) <br>- Normalized weights (0–1) <br>- Scoring formula | Accuracy, bias mitigation                | Weight balancing, dynamic criteria adjustment    |
| **Collaborative Filtering**    | User-item interactions                | - User-item matrix <br>- Similarity metrics (cosine, Pearson) <br>- Recommendation model | Precision, recall, diversity            | Cold-start problem, scalability                   |
| **Content-Based Filtering**     | Item attributes                        | - Feature vectors (TF-IDF, embeddings) <br>- Similarity functions                   | Relevance, coverage                      | Limited personalization                           |
| **Hybrid Ranking**              | Combine multiple methods              | - Weighted fusion of models (e.g., 60% CF + 40% CB) <br>- Ensemble learning           | Performance trade-offs                   | Model coordination, interpretability               |
| **Time-Based Decay**            | Recency-sensitive rankings            | - Exponential decay factor (λ) <br>- Last activity timestamp <br>- Rank adjustment | Freshness, trend responsiveness          | Tuning λ for balance                               |
| **Tiered Thresholds**           | Categorical ranking                   | - Fixed tiers (e.g., Bronze/Silver/Gold) <br>- Threshold rules (e.g., >=90% = Gold) | Clarity, consistency                     | Arbitrary threshold selection                     |
| **Personalization (Context-Aware)** | User-specific rules           | - Context data (location, preferences) <br>- Dynamic rule engine                    | Personalization gain, engagement         | Data privacy, real-time processing                |
| **Feature Importance**         | ML-driven ranking                     | - Ranked feature importance (e.g., SHAP values) <br>- Interpretability tools         | Model fairness, explainability          | Feature selection bias, interpretability trade-offs |

---

## **Implementation Details**

### **1. Weighted Scoring**
**Concept:**
Assign numerical weights to predefined criteria (e.g., price: 0.3, reviews: 0.5, recency: 0.2) and compute a score:

**Formula:**
`Score = Σ(weight_i × normalized_value_i)`

**Example Use Cases:**
- E-commerce product ranking
- Job candidate prioritization

**Implementation Notes:**
- Normalize values (e.g., min-max scaling) to prevent dominance by high-magnitude metrics.
- Use **lambda calculus** for dynamic weights (e.g., `λ = 1 - (time_since_action / max_age)`).

---

### **2. Collaborative Filtering**
**Concept:**
Leverage user-item interactions (e.g., clicks, ratings) to infer preferences. Key variants:
- **User-based:** Recommend items liked by similar users.
- **Item-based:** Recommend items similar to those the user interacted with.

**Key Steps:**
1. Build user-item matrix (sparse for large datasets).
2. Compute similarity (e.g., cosine similarity: `sim(u1, u2) = (A·B) / (||A||·||B||)`).
3. Predict ratings or scores via regression (e.g., SVD, matrix factorization).

**Libraries:**
- Python: `surprise`, `implicit` (for implicit feedback).
- Big Data: Apache Spark (ALS algorithm).

**Challenges:**
- **Cold start:** New users/items lack interaction data → use hybrid approaches or content-based fallback.
- **Scalability:** Use approximate nearest-neighbor search (e.g., Annoy, FAISS).

---

### **3. Content-Based Filtering**
**Concept:**
Rank items based on semantic similarity to user preferences or query features.

**Implementation:**
1. **Vectorize items** (e.g., TF-IDF for text, embeddings for images/videos).
2. **Compute similarity** (e.g., cosine similarity between query vector and item vectors).
3. **Rank by score.**

**Example (Python):**
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

items = ["laptop", "phone", "tablet"]
query = "gaming laptop"
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform([query] + items)
similarities = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1:])
print(similarities.flatten())  # Scores for each item
```

**Limitations:**
- **Over-specialization:** May miss serendipity (unexpected but relevant items).

---

### **4. Hybrid Ranking**
**Combine models** (e.g., 70% collaborative + 30% content-based) via:
- **Weighted averaging** of scores.
- **Late fusion** (e.g., predict user preference confidence and blend models accordingly).

**Example (Rule-Based Blending):**
```python
def hybrid_rank(user_id, item_id, cf_score, cb_score):
    if user_activity(user_id) > THRESHOLD:  # Trust CF more
        return 0.7 * cf_score + 0.3 * cb_score
    else:
        return 0.4 * cf_score + 0.6 * cb_score
```

**Tools:**
- **TensorFlow Recommenders** (for end-to-end hybrid models).
- **Bayesian Personalized Ranking (BPR)** for implicit feedback.

---

### **5. Time-Based Decay**
**Concept:**
Adjust rankings based on recency. Common formulas:
- **Exponential decay:** `score = original_score × e^(−λ×time_since_event)`
- **Linear decay:** `score = original_score × (1 − time_normalized)`

**Example (Python):**
```python
import math

def decay_score(original_score, time_since_event, lambda_=0.5):
    return original_score * math.exp(-lambda_ * time_since_event)
```

**Use Cases:**
- News/trending topics
- Social media feeds

**Tuning:**
- `λ` controls decay speed (higher `λ` = faster decay). Test with A/B experiments.

---

### **6. Tiered Thresholds**
**Concept:**
Assign discrete tiers (e.g., "High," "Medium," "Low") based on thresholds.

**Schema:**
| Tier   | Condition                          | Example Rule                     |
|--------|------------------------------------|----------------------------------|
| Gold   | Score ≥ 90%                        | `score ≥ quantile(90%)`           |
| Silver | 70% ≤ Score < 90%                  | `70 ≤ score < 90`                 |
| Bronze | Score < 70%                        | `score < quantile(30%)`           |

**Implementation:**
- Use **percentile ranking** or domain-specific rules (e.g., "Top 10%").
- Visualize thresholds with **decile plots**.

**Challenges:**
- Arbitrary thresholds → validate with business metrics (e.g., conversion rates).

---

### **7. Personalization (Context-Aware)**
**Concept:**
Dynamically adjust rankings using real-time context (e.g., location, time, device).

**Approaches:**
1. **Rule-Based:** Apply context filters (e.g., "Show nearby stores" for `location="urban"`).
2. **ML-Based:** Train models on context × user interactions (e.g., deep learning for sequential context).

**Example (Rule Engine Pseudo-Code):**
```python
if user.timezone == "EST" and event.hour < 18:
    apply_decay_factor(0.8)  # Discount scores for off-peak hours
```

**Tools:**
- **Apache Beam** (for real-time context processing).
- **Rules Engines:** Drools, Easy Rules.

---

### **8. Feature Importance (ML-Driven)**
**Concept:**
Use model interpretability tools to rank features by contribution.

**Methods:**
- **SHAP values:** Measure feature impact on predictions.
- **Permutation importance:** Shuffle a feature and track rank drop.

**Example (SHAP with XGBoost):**
```python
import shap
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_train)
shap.summary_plot(shap_values, X_train)  # Ranks features by importance
```

**Use Cases:**
- Debug biased rankings.
- Prioritize feature engineering.

---

## **Query Examples**

### **1. Weighted Scoring (SQL)**
```sql
SELECT
    product_id,
    (price_score * 0.3 +
     review_score * 0.5 +
     recency_score * 0.2) AS total_rank
FROM products
ORDER BY total_rank DESC;
```

### **2. Collaborative Filtering (Python)**
```python
from surprise import Dataset, Reader, KNNBasic

# Load data
reader = Reader(rating_scale=(1, 5))
data = Dataset.load_from_file('ratings.dat', reader)

# Train user-based CF
sim_options = {'name': 'cosine', 'user_based': True}
model = KNNBasic(sim_options=sim_options)
model.fit(data.build_full_trainset())

# Predict ratings for user 123 on item 456
print(model.predict(123, 456).est)  # Predicted score
```

### **3. Hybrid Ranking (Pseudocode)**
```python
def rank_item(user_id, item_id, cf_score, cb_score, user_activity):
    if user_activity > 10:  # Active user
        return 0.6 * cf_score + 0.4 * cb_score
    else:
        return 0.3 * cf_score + 0.7 * cb_score
```

### **4. Time-Based Decay (JavaScript)**
```javascript
function rankWithDecay(originalScore, timestamp, now) {
    const hoursAgo = (now - timestamp) / (1000 * 60 * 60);
    const lambda = 0.3; // Adjust for faster/slower decay
    return originalScore * Math.exp(-lambda * Math.sqrt(hoursAgo));
}
```

---

## **Related Patterns**

| **Pattern**               | **Connection to Ranking Systems**                                                                 | **Reference**                          |
|---------------------------|------------------------------------------------------------------------------------------------|----------------------------------------|
| **Feature Store**         | Centralized storage of features (e.g., user embeddings) used in ranking models.                 | [Feature Store Pattern](link)          |
| **Event Sourcing**        | Track interactions (e.g., clicks) for dynamic ranking updates.                                  | [Event Sourcing Pattern](link)         |
| **A/B Testing**           | Validate ranking algorithm improvements (e.g., hybrid vs. baseline).                           | [A/B Testing Pattern](link)             |
| **Real-Time Processing**  | Stream processing for live ranking updates (e.g., Kafka + Flink).                              | [CQRS Pattern](link)                    |
| **Caching**               | Cache ranked results to reduce compute overhead (e.g., Redis).                                 | [Caching Pattern](link)                 |
| **Model Monitoring**      | Detect ranking drift (e.g., drop in precision over time).                                    | [Model Monitoring Pattern](link)       |

---

## **Key Considerations**
1. **Bias Mitigation:**
   - Audit rankings for demographic skew (e.g., "Do Black users see fewer top results?").
   - Use **fairness-aware ML** (e.g., adversarial debiasing).
2. **Explainability:**
   - Provide **rank justifications** (e.g., "Ranked #1 because 80% review rating and 2-day recency").
   - Tools: LIME, SHAP.
3. **Scalability:**
   - For large datasets, use **distributed ranking** (e.g., Apache Spark’s `rank` functions).
   - Approximate nearest neighbors for real-time queries.
4. **Feedback Loops:**
   - Continuously update rankings using **online learning** (e.g., bandit algorithms).
5. **Latency:**
   - Pre-compute rankings for static criteria; use **incremental updates** for dynamic ones.

---
**See Also:**
- [Recommender Systems Patterns](link)
- [Search Ranking Algorithms](link)
- [Fairness in Machine Learning](link)