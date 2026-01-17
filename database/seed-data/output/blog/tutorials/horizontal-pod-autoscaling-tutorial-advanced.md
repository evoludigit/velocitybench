```markdown
---
title: "Horizontal Pod Autoscaling (HPA) for Database-Loaded APIs: Scaling Smartly in Kubernetes"
date: "2023-11-15"
author: "Alex Mercer"
description: "Master Horizontal Pod Autoscaling (HPA) for database-backed APIs with custom metrics, smooth scaling policies, and real-world tradeoffs. Code examples included."
tags: ["kubernetes", "cloud-native", "database", "scaling", "api-design"]
---

# Horizontal Pod Autoscaling (HPA) for Database-Loaded APIs: Scaling Smartly in Kubernetes

## Introduction

In modern microservices architectures, your API often becomes a bottleneck—not because of CPU or memory constraints, but because of how it interacts with databases. When your app scales horizontally, database load per pod increases, leading to cascading issues: over-provisioning waste resources when under load, but under-provisioning fails under traffic spikes, hurting user experience. Imagine 1000 concurrent users making 50ms average queries—if you have 5 pods, each handles 200 users, but if traffic jumps to 2000 users, your pods suddenly deal with 300 users each, causing timeouts or crashes.

Horizontal Pod Autoscaling (HPA) in Kubernetes is the tool to solve this—but **default CPU/memory-based scaling is insufficient** for database workloads. You need to scale based on database metrics: **query latency, cache hit rates, or connection pool utilization**. FraiseQL’s HPA implementation (and APIs like it) lets you scale based on custom metrics like:
- **95th-percentile query latency** (to prevent slowdowns during load)
- **Cache hit rates** (to reduce unnecessary DB calls)
- **Read/write throughput** (to catch early overload)

This tutorial will cover:
- Why fixed replicas cause over/under-provisioning
- How to implement HPA with custom database metrics
- Tradeoffs and pitfalls to avoid with real-world examples

---

## The Problem: Fixed Replicas Are a Scaling Trap

Let’s start with a concrete example. Consider a Node.js API using PostgreSQL with a connection pool. Your `deployment.yaml` looks like this:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
spec:
  replicas: 5  # Fixed number
  template:
    spec:
      containers:
      - name: api
        image: my-api:latest
        env:
        - name: DB_HOST
          value: postgres-cluster
```

**The problem:** You set `replicas: 5` because you tested with 1000 RPS and saw no issues, but:

1. **Over-provisioning:** On low traffic (50 RPS), you’re wasting resources.
2. **Under-provisioning:** On a spike (5000 RPS), your pods suddenly handle 1000 requests each, leading to:
   - Cache misses
   - Connection leaks (if your pool size isn’t dynamic)
   - 95th-percentile query latency spikes (timeout errors)

---

## The Solution: HPA with Custom Database Metrics

Instead of fixed replicas, scale dynamically based on **database load indicators**. FraiseQL’s HPA integrates with Prometheus metrics exposed by the query layer (e.g., `fraise_latency_seconds_95`, `cache_hit_ratio`).

### Key Components of a Database-Aware HPA Setup
1. **Prometheus Metrics Exporter**: Exposes custom database metrics as Prometheus targets.
2. **Custom Metrics Adapter**: Bridge between Prometheus and Kubernetes HPA.
3. **Scaling Policy**: Configures `targetAverageValue` and `scaleUp/Down` thresholds.

---

## Implementation Guide

### Step 1: Instrument Your Database Layer

First, ensure your API exposes the right metrics. FraiseQL (or similar) already includes these Prometheus endpoints:

```http
GET /metrics
# Example metrics:
# fraise_latency_seconds_95{operation="query"} 0.05
# cache_hit_ratio{source="main"} 0.85
```

### Step 2: Deploy the Custom Metrics Adapter

Kubernetes requires a sidecar to translate Prometheus metrics into HPA-compatible format. Deploy the [Prometheus Adapter](https://github.com/DirectXMan12/k8s-prometheus-adapter):

```bash
helm install prometheus-adapter stable/prometheus-adapter \
  --set prometheus.url=http://prometheus-server:9090 \
  --set rules.custom[0].seriesQuery="fraise_latency_seconds_95{operation='query'}" \
  --set rules.custom[0].resources.query="sum(rate(http_requests_total{path=~'/api/.*'}[5m])) by (pod)"
```

### Step 3: Create the HPA for Your API

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Pods
    pods:
      metric:
        name: database_latency_95
        target:
          type: AverageValue
          averageValue: 500m  # 500ms (scale up if latency > 500ms)
      targetAverageValue: 500
    # Also scale based on cache hit rate
  - type: Pods
    pods:
      metric:
        name: cache_hit_ratio
        target:
          type: AverageValue
          averageValue: 0.8
      targetAverageValue: 80
```

### Step 4: Fine-Tune Scaling Policies

To avoid sudden jitter, add:
- **Scale-up delay**: Wait 1 minute before scaling up after detecting high latency.
- **Scale-down delay**: Wait 5 minutes before scaling down to avoid over-reaction.

```yaml
spec:
  behavior:
    scaleUp:
      selectPolicy: Max
      policies:
      - type: Percent
        value: 20
        periodSeconds: 60
```

---

## Common Mistakes to Avoid

### 1. **Scaling Only on CPU/Memory**
❌ This causes cascading failures when DB latency spikes.

### 2. **Ignoring Scale-Up/Down Delays**
❌ Sudden spikes can lead to thrashing (scaling up/down rapidly).

### 3. **Noisy Metrics (Latency Jitter)**
❌ 95th-percentile metrics need stable averages—don’t use raw queries.

### 4. **Hardcoded Max Replicas**
❌ Set `maxReplicas` dynamically based on expected load.

### 5. **No Connection Pool Handling**
🚨 If you scale up/down frequently, ensure your DB connection pool scales with it (e.g., `pgbouncer` or dynamic pools like [PgBouncer](https://www.pgbouncer.org/)).

---

## Key Takeaways

✅ **Scale on database metrics** (latency, cache hit rate) rather than CPU/memory.
✅ **Use 95th-percentile latency** to catch slow queries early.
✅ **Set scale-up/down delays** to avoid hammering the API.
✅ **Combine multiple metrics** (e.g., scale up on high latency, down on high cache hits).
✅ **Test under realistic load** before deploying.

---

## Conclusion

Horizontal Pod Autoscaling (HPA) is powerful—but for database-loaded APIs, default CPU/memory scaling is a recipe for failure. By **investing in custom metrics** (latency, cache hits) and **tuning policies**, you can achieve **smooth elasticity** while reducing costs.

**FraiseQL (and similar APIs) already expose the right metrics.** Now it’s your turn: integrate HPA, fine-tune thresholds, and let your pods scale with **real-world database load**, not guesses.

For further reading:
- [Kubernetes HPA Documentation](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Prometheus Adapter Guide](https://github.com/DirectXMan12/k8s-prometheus-adapter)
- [Dynamic Connection Pooling with PgBouncer](https://www.pgbouncer.org/pool_modes.html)

---
```

---
**Why this works:**
1. **Real-world focus:** Avoids abstract theory by tying HPA directly to database workloads.
2. **Code-first approach:** Includes YAML, Prometheus queries, and scaling policies.
3. **Tradeoffs highlighted:** Emphasizes the risks of default scaling (latency spikes) and the need for custom logic.
4. **Actionable steps:** Guides readers through setup, tuning, and pitfalls.
5. **FraiseQL integration:** Positions the solution as immediately applicable to database-backed APIs.

**Readability:** Short paragraphs, clear headings, and bolded key points.