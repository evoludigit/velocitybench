```markdown
---
title: "Anomaly Detection Patterns: Building Robust Systems to Spot the Unexpected"
date: 2023-10-15
tags: ["backend", "database design", "api design", "anomaly detection", "data patterns"]
description: "Learn practical anomaly detection patterns for backend systems, tradeoffs, and real-world examples using PostgreSQL, Python, and Kafka."
author: "Alex Carter"
---

# Anomaly Detection Patterns: Building Robust Systems to Spot the Unexpected

Anomaly detection isn’t just for fraud teams or cybersecurity—it’s a pattern you’ll encounter in nearly every backend system when you need to identify unusual behavior that could indicate errors, performance bottlenecks, or security threats. Whether you’re tracking failed API calls, unusual payment patterns, or sudden spikes in database queries, anomalies often reveal critical insights before they become major issues.

But anomaly detection isn’t as simple as "out-of-the ordinary." It’s a complex dance between statistical models, real-time data processing, and business context. The challenge is designing a pattern that’s both sensitive (to catch real anomalies) and resilient (to avoid noise). In this guide, we’ll break down practical anomaly detection patterns, walk through a real-world example using PostgreSQL and Python, and discuss tradeoffs you’ll face when implementing them.

---

## The Problem

Anomalies can appear in systems in many forms:
- **API anomalies**: Failed requests, latency spikes, or sudden traffic drops.
- **Database anomalies**: Unexpected query patterns (e.g., a single query suddenly consuming 80% of CPU).
- **Business anomalies**: Unusual user behavior (e.g., a single user making 100 transactions in 5 minutes).
- **Infrastructure anomalies**: Metrics like disk usage or network latency crossing thresholds.

The difficulty lies in balancing:
- **False positives**: Alerting on normal but rare events (e.g., a user’s first login attempt).
- **False negatives**: Missing real anomalies because the system is too forgiving.
- **Performance overhead**: Running heavy computations in production to detect anomalies.

Worse, anomalies often require context. A "normal" 500 error rate might be catastrophic for a payment system but tolerable for a analytics dashboard. Without domain-specific rules, your detection system risks either drowning in noise or missing critical alerts.

---

## The Solution: A Multi-Layered Approach

Anomaly detection rarely works with a single tool. Instead, you’ll combine:

1. **Statistical methods**: For detecting deviations from expected behavior.
2. **Rule-based triggers**: For catching known bad patterns.
3. **Machine learning**: For adaptive detection over time.
4. **Time-series analysis**: For understanding trends (e.g., "this is 3x the usual traffic").

We’ll focus on two core patterns:
- **Time-series anomaly detection** (for metrics like API latency or database load).
- **Windowed behavior analysis** (for detecting anomalies in user/API behavior).

---

## Components & Solutions

### 1. Time-Series Anomaly Detection
Useful for metrics like CPU usage, request latency, or database query counts.

**Example:** Detecting sudden spikes in database query latency.

#### How It Works
- Collect time-series data (e.g., Kafka events or PostgreSQL metrics).
- Use statistical methods like **z-scores** or **moving averages** to flag deviations.
- Optionally, use ML models like **Prophet** or **Isolation Forest** for unsupervised learning.

---

### 2. Windowed Behavior Analysis
For detecting anomalies in user/API behavior (e.g., a single user making unusual requests).

**Example:** Detecting a user making 100 API calls in 5 minutes.

#### How It Works
- Define a "normal" window (e.g., 5-minute rolling window).
- Use statistical methods like **interquartile range (IQR)** or **CLT (central limit theorem)** to detect outliers.
- Combine with rule-based checks (e.g., "block if more than X requests/minute").

---

### 3. Hybrid Approach: Rules + ML
Use rule-based checks for known bad patterns and ML for unknown anomalies.

---

## Code Examples

### Example 1: Time-Series Anomaly Detection with PostgreSQL & Python
We’ll detect spikes in database query latency using PostgreSQL metrics and Python.

#### Step 1: Simulate PostgreSQL Metrics
Create a table to store query latency over time:
```sql
CREATE TABLE query_latency (
    id SERIAL PRIMARY KEY,
    query_name VARCHAR(255),
    latency_ms INTEGER,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert sample data (simulate a spike at t=12:40)
INSERT INTO query_latency (query_name, latency_ms)
VALUES ('SELECT * FROM users', 100), -- Normal
       ('SELECT * FROM users', 80),  -- Normal
       ('SELECT * FROM users', 150), -- Normal
       ('SELECT * FROM users', 500), -- Spike!
       ('SELECT * FROM users', 300);  -- Still elevated
```

#### Step 2: Python Script Using Moving Average
```python
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose

# Fetch data from PostgreSQL
conn = psycopg2.connect("dbname=test user=postgres")
df = pd.read_sql("SELECT * FROM query_latency", conn)

# Set timestamp as index and sort
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp').sort_index()

# Calculate rolling mean (2-minute window)
df['rolling_mean'] = df['latency_ms'].rolling('2T').mean()
df['anomaly'] = (df['latency_ms'] > 3 * df['rolling_mean']).astype(int)

# Plot
plt.figure(figsize=(10, 5))
df.plot(y='latency_ms', label='Latency')
df.plot(y='rolling_mean', label='Rolling Mean', linestyle='--')
plt.scatter(df[df['anomaly'] == 1].index, df[df['anomaly'] == 1]['latency_ms'],
            color='red', label='Anomaly')
plt.title("Query Latency with Moving Average Anomaly Detection")
plt.legend()
plt.show()
```

#### Step 3: Rule-Based Filtering
Add a rule to flag latencies above 300ms:
```python
df['rule_based_anomaly'] = (df['latency_ms'] > 300).astype(int)
```

---

### Example 2: Windowed Behavior Analysis with Kafka & Python
Detect sudden spikes in API request rates using Kafka events.

#### Step 1: Kafka Producer (Simulate API Requests)
```python
from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers='localhost:9092')

# Simulate normal traffic (5 requests/minute)
for i in range(300):
    producer.send('api_requests', value=f"{i}".encode()).get(timeout=5)

# Simulate an anomaly (50 requests/minute)
for i in range(301, 1000):
    producer.send('api_requests', value=f"{i}".encode()).get(timeout=5)
```

#### Step 2: Kafka Consumer with IQR Anomaly Detection
```python
from kafka import KafkaConsumer
import pandas as pd
from scipy import stats

consumer = KafkaConsumer('api_requests', bootstrap_servers='localhost:9092')

# Rolling window: 5-minute window with 1-minute step
window_size = 60  # seconds
window_step = 10  # seconds

data = []
while True:
    messages = consumer.poll(timeout_ms=1000)
    for msg in messages.get('api_requests'):
        data.append(int(msg.value.decode()))

    # Process window
    if len(data) > window_size:
        current_window = data[-window_size:]
        q1, q3 = pd.Series(current_window).quantile([0.25, 0.75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        # Flag anomalies
        anomalies = [x for x in current_window if x > upper_bound or x < lower_bound]
        if anomalies:
            print(f"Window: {len(anomalies)} requests above bounds!")
        data = data[-(window_size - window_step):]
```

---

## Implementation Guide

### Step 1: Define Anomaly Definitions
- For time-series: What constitutes a "spike"? (e.g., 3x rolling mean).
- For windows: What’s a normal distribution? (e.g., 99th percentile).

### Step 2: Choose Your Tools
- **Lightweight**: Use stats (IQR, z-scores) for simple rules.
- **Heavy**: Use ML (Prophet, Isolation Forest) for complex patterns.

### Step 3: Start Small
- Test on historical data before running in production.
- Use backtesting to validate accuracy.

### Step 4: Alert Wisely
- Combine statistical detection with business rules.
- Example: "Alert only if latency spike > 300ms and > 10x rolling mean."

### Step 5: Monitor False Positives/Negatives
- Use a dashboard to track anomalies.
- Adjust thresholds as needed.

---

## Common Mistakes to Avoid

1. **Ignoring Context**: Don’t treat all anomalies equally. For example, a 500 error is worse in a payment system than in a blog.
2. **Over-Optimizing for Accuracy**: A 100% accurate model may miss real anomalies. Focus on precision/recall tradeoffs.
3. **Real-Time vs. Batch**: Use the right approach for your use case. Batch works for historical data; real-time needs streaming.
4. **Forgetting Data Skew**: Some data points are outliers by nature (e.g., the 99th percentile). Adjust thresholds accordingly.
5. **Not Testing**: Assume anomalies will appear in production. Test with simulated data first.

---

## Key Takeaways

✅ **Anomaly detection is a pattern, not a single tool.** Combine statistical methods, rules, and ML.
✅ **Time-series and windowing are two core approaches.** Choose based on your data’s nature.
✅ **Context matters.** What’s anomalous depends on the system (e.g., payment vs. analytics).
✅ **Start simple.** Use statistics (IQR, z-scores) before diving into complex ML.
✅ **Alert smartly.** Balance sensitivity with false positives.
✅ **Monitor false positives.** Adjust thresholds as you learn.

---

## Conclusion

Anomaly detection is a powerful pattern for backend systems, but it’s not a silver bullet. The best approach combines statistical rigor with domain knowledge, allowing you to spot critical issues before they become crises. Whether you’re monitoring database performance, API behavior, or user patterns, the key is to start with clear definitions, test rigorously, and refine as you go.

Here’s a recap of the tools and strategies we covered:
1. **Time-series anomaly detection**: Use moving averages, z-scores, or ML models like Prophet.
2. **Windowed behavior analysis**: Apply statistical methods (IQR) to rolling windows.
3. **Hybrid approach**: Combine rules with ML for robustness.

Remember, the goal isn’t to detect *all* anomalies—it’s to detect the ones that matter. By designing your system intentionally, you can turn unexpected behavior into actionable insights.

Happy coding, and may your anomalies be few and far between!
```