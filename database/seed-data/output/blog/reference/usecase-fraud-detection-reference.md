# **[Fraud Detection Patterns] Reference Guide**
*Detect and mitigate fraudulent transactions in real-time and batch systems*

---

## **Overview**
Fraud Detection Patterns provide a structured framework for identifying suspicious activities across financial transactions, e-commerce, telecom, and other domains prone to fraud. By combining statistical anomaly detection, rule-based analysis, machine learning, and behavioral models, these patterns help organizations reduce false positives/negatives while improving response times. Common use cases include credit card fraud, account takeovers, synthetic identity fraud, and chargeback prevention. This guide covers key patterns, implementation strategies, and schema requirements for integrating fraud detection into applications.

---

## **Core Patterns & Schema Reference**

| **Pattern Name**               | **Description**                                                                                     | **Key Input Fields**                                                                                     | **Output Fields**                                                                 |
|---------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Anomaly-Based Detection**     | Uses statistical models (e.g., Z-score, Isolation Forest) to flag transactions deviating from norms. | `transaction_id`, `amount`, `merchant_id`, `user_history`, `time_since_last_tx`                     | `anomaly_score` (0–1), `is_fraud`, `threshold_breach`                            |
| **Rule-Based Filtering**        | Applies predefined rules (e.g., "amount > $10K in 1 hour") to block high-risk transactions.        | `tx_amount`, `tx_time`, `device_fingerprint`, `region`, `velocity` (txs/minute)                       | `rule_id`, `rule_matched`, `action_recommendation` (e.g., "hold_for_review")     |
| **Behavioral Analysis**         | Tracks user behavior (e.g., login patterns, purchase frequency) to detect synthetic or hijacked accounts. | `user_id`, `login_history`, `purchase_freq`, `device_changes`, `geolocation`                          | `behavioral_score`, `is_synthetic`, `risk_category` (e.g., "account_takeover")    |
| **Network/Graph Analysis**      | Identifies fraud rings by analyzing relationships between accounts (e.g., shared IPs, devices).     | `user_id`, `ip_address`, `device_id`, `transaction_graph`, `social_network_links`                     | `fraction_of_risky_connections`, `cluster_id`, `ring_confidence_score`             |
| **Velocity Thresholding**       | Flags unusual transaction rates (e.g., 50 logins in 5 minutes).                                      | `user_id`, `event_type` (login/purchase), `event_time`, `time_window` (e.g., "5m")                   | `velocity_score`, `threshold_violation`, `alert_type` (e.g., "brute_force")        |
| **Machine Learning (Supervised)**| Trains on labeled fraud/non-fraud data to classify new transactions (e.g., Random Forest, XGBoost). | `feature_vector` (e.g., `amount`, `merchant_category`, `time_since_last_tx`, `device_type`)            | `predicted_fraud_prob`, `model_version`, `confidence_interval`                    |
| **Graph Embeddings**            | Embeds transaction/network data into vectors to detect fraud clusters (e.g., Node2Vec, GNNs).       | `transaction_graph`, `node_features` (e.g., `user_behavior`, `merchant_reputation`)                   | `embedding_vector`, `similarity_to_risky_clusters`, `anomaly_in_embedding_space`  |

---

## **Implementation Details**

### **1. Data Sources**
- **Transaction Data**: Structured logs (e.g., `tx_id`, `amount`, `timestamp`, `merchant`).
- **User Profiles**: Historical behavior (e.g., `login_freq`, `typical_spend`).
- **Device/Network Data**: IP geolocation, device fingerprints, VPN usage.
- **External Data**: Watchlists (e.g., stolen cards), dark web feeds, or fraud databases.

### **2. Key Algorithms**
| **Algorithm**               | **Use Case**                                  | **Pros**                                  | **Cons**                                  |
|-----------------------------|-----------------------------------------------|-------------------------------------------|-------------------------------------------|
| **Z-Score/Isolation Forest** | Anomaly detection in low-data scenarios.      | Fast, no training data needed.           | Slower for high-dimensional data.        |
| **Random Forest/XGBoost**   | High-accuracy supervised classification.      | Handles non-linear patterns.            | Requires labeled data; slower inference.|
| **Graph Neural Networks**   | Detecting fraud rings/synthetic IDs.          | Captures relational fraud.               | Complex to implement; high compute cost.|
| **Time-Series Analysis**    | Detecting velocity-based fraud (e.g., brute force). | Works with sequential data.           | Needs historical context.                |

### **3. Architecture Components**
- **Real-Time Engine**: Stream processing (e.g., Apache Flink/Spark) for low-latency decisions.
- **Batch Processing**: Hadoop/Spark for offline ML model training.
- **Scoring Service**: REST/gRPC API to compute risk scores for transactions.
- **Feedback Loop**: Human review -> model retraining pipeline for continuous improvement.

### **4. Deployment Options**
| **Option**               | **Latency** | **Scalability** | **Complexity** | **Best For**                     |
|--------------------------|-------------|-----------------|----------------|----------------------------------|
| **Embedded Rules**       | <1ms        | Low             | Low            | Simple rule-based filtering.     |
| **Microservice API**     | 50–500ms    | High            | Medium         | Real-time ML scoring.            |
| **Serverless (AWS Lambda)**| 100–1000ms  | Elastic         | Medium         | Spiky traffic workloads.         |
| **Edge Computing**       | <10ms       | Low             | High           | Low-latency IoT/finance apps.    |

---

## **Query Examples**
### **1. Anomaly Detection (SQL)**
```sql
-- Flag transactions with high Z-score in amount
SELECT
  tx_id,
  amount,
  AVG(amount) OVER (PARTITION BY user_id) AS avg_amount,
  (amount - avg_amount) / STDDEV(amount) OVER (PARTITION BY user_id) AS z_score
FROM transactions
WHERE z_score > 3
ORDER BY z_score DESC;
```

### **2. Velocity-Based Fraud (Spark Query)**
```python
# PySpark: Flag users with >10 logins in 1 hour
from pyspark.sql.functions import count, window

df.groupBy("user_id", window("timestamp", "1 hour"))
  .agg(count("*").alias("login_count"))
  .filter("login_count > 10")
  .show()
```

### **3. Graph-Based Fraud Ring Detection (Neo4j)**
```cypher
-- Find users connected to known fraudsters (degree > 3)
MATCH (u:User)-[*1..3]-(fraudster:User {is_fraud: true})
WHERE size((u)-[*]->()) > 3
RETURN u.user_id, size((u)-[*]->()) AS risky_connections;
```

### **4. ML Scoring (Scikit-Learn)**
```python
from sklearn.ensemble import RandomForestClassifier

# Train on labeled data
model = RandomForestClassifier().fit(X_train, y_train)

# Score a new transaction
tx_features = [[amount, merchant_category, time_since_last_tx]]
prediction = model.predict_proba(tx_features)[0, 1]  # Probability of fraud
```

---

## **Related Patterns**
1. **Velocity Detection Patterns**
   - *Use Case*: Detecting brute-force attacks or high-frequency fraud (e.g., bots, synthetic IDs).
   - *Reference*: [Velocity-Based Fraud Detection](https://www.oreilly.com/library/view/design-patterns-for/9781617291612/ch04.html).

2. **Threshold-Based Scoring**
   - *Use Case*: Simple rule engines for low-latency filtering (e.g., "block transactions > $10K").
   - *Reference*: [Rule-Based Systems](https://en.wikipedia.org/wiki/Rule-based_system).

3. **Graph Analytics for Fraud**
   - *Use Case*: Identifying fraud rings or cascading failures (e.g., money laundering).
   - *Reference*: [Graph Algorithms for Fraud Detection](https://www.gartner.com/en/documents/3992264/gartner-says-graph-analytics-will-continue-to-mature).

4. **Real-Time Event Streaming**
   - *Use Case*: Processing transactions as they occur (e.g., Kafka + Flink).
   - *Reference*: [Real-Time Data Processing Patterns](https://www.oreilly.com/library/view/stream-processing-cookbook/9781492033493/).

5. **Feedback Loop for ML**
   - *Use Case*: Continuously improving models with human-labeled data.
   - *Reference*: [Active Learning in ML](https://www.jmlr.org/papers/volume21/19-477/19-477.pdf).

---

## **Best Practices**
1. **Start Simple**: Use rule-based patterns before adopting ML (lower maintenance).
2. **Monitor False Positives/Negatives**: Track precision/recall metrics (e.g., "false positives < 1%").
3. **Hybrid Models**: Combine rules + ML for explainability (e.g., "flag if ML score > 0.9 OR rule `A` matches").
4. **Data Privacy**: Anonymize user data for ML training (GDPR/CCPA compliance).
5. **Edge Deployment**: For ultra-low latency, deploy lightweight models (e.g., ONNX runtime) at the edge.
6. **Cost Optimization**: Use approximate algorithms (e.g., Locality-Sensitive Hashing) for large-scale velocity checks.

---
**See Also**:
- [Fraud Detection Taxonomy (OASIS)](https://www.oasis-open.org/committees/td/fraud-detection/)
- [NIST Fraud Guidelines](https://csrc.nist.gov/publications/detail/sp/800-63/3/final)