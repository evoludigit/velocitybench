```markdown
---
title: "Aggregate Tables for Pre-Computed Rollups (ta_*): Building Real-Time Dashboards at Scale"
date: "2023-11-15"
author: "Jane Doe, Senior Backend Engineer"
tags: ["database patterns", "data architecture", "performance optimization", "aggregates", "ETL"]
description: "Learn how to pre-compute aggregations using the Aggregate Tables (ta_*) pattern to serve billion-row datasets in sub-second queries. Practical examples, tradeoffs, and implementation guidance."
---

# Aggregate Tables for Pre-Computed Rollups (ta_*): Building Real-Time Dashboards at Scale

![Aggregate Tables Illustration](https://miro.medium.com/max/1400/1*XyZ1qJ23456789abcdef0123456789.jpg)
*Diagram: Aggregate tables (ta_*) complement raw fact tables for instant dashboards*

As backend engineers, we’ve all been there: a dashboard that was fast yesterday is now crawling to a halt as our fact tables grow into the billions. Business users need *real-time* insights, but GROUP BY queries over 1B rows take 10+ seconds—even with proper indexing. The Aggregate Tables (ta_*) pattern solves this by trading storage for speed, pre-computing rollups at granularities that match query patterns.

This post covers:
- **Why** aggregate tables matter when raw fact tables become a bottleneck
- **How** to structure them for flexibility (JSONB for dimensions, columns for measures)
- **When** to use hourly vs. daily vs. monthly aggregations
- **Pitfalls** like stale data or unmanageable storage growth
- **Real-world tradeoffs** (e.g., balancing freshness vs. performance)

By the end, you’ll have a battle-tested pattern to implement—ready for production dashboards.

---

## The Problem: Why Your GROUP BY Queries Are Slowing Down

Fact tables are the foundation of analytics, but they’re not designed for ad-hoc queries. Here’s the reality:

```sql
-- Querying a 1B-row fact table (simplified)
SELECT
    customer_segment,
    SUM(revenue) as total_revenue,
    AVG(clicks) as avg_clicks
FROM fact_sessions
WHERE date >= '2023-01-01'
GROUP BY customer_segment
ORDER BY total_revenue DESC
LIMIT 100;
```

**Performance bottlenecks:**
1. **Aggregation cost**: Even with proper indexes, GROUP BY operations scale linearly with row count. At 1B rows, this becomes a multi-second operation.
2. **Repeated work**: Daily reports re-run the same aggregations every morning. Business users then *refresh their dashboards* in case the data changed—triggering redundant calculations.
3. **Peak load**: During business hours, every sales team member’s dashboard refresh compounds into a database storm. Replication lag and query timeouts follow.
4. **Real-time constraints**: Sub-second response times are impossible for large fact tables. Dashboards become tool-y instead of actionable.

### The Real-World Impact
Consider a SaaS analytics stack serving 100+ users with user-facing dashboards. Without pre-aggregations:
- **Latency spikes** during Q3 revenue reporting (10+ users querying simultaneously).
- **Stale dashboards**: Users refresh, only to see outdated numbers while new data is still aggregating.
- **Scaling limits**: Adding new features (like anomaly detection) becomes a performance nightmare because every query hits the same raw data.

---

## The Solution: Pre-Compute Rollups with Aggregate Tables

The Aggregate Tables (ta_*) pattern addresses this by maintaining *separate materialized tables* for pre-computed aggregations. The key insight: **most dashboards reuse the same aggregations repeatedly**. Why re-calculate yesterday’s data every morning?

### Core Components

| Component          | Purpose                                                                 | Example Table                 |
|--------------------|-------------------------------------------------------------------------|-------------------------------|
| **Fact Table**     | Raw, immutable transactional data (e.g., clicks, orders).              | `fact_user_sessions`          |
| **Aggregate Tables** | Pre-computed metrics at hourly/daily/monthly granularities.            | `ta_user_sessions_daily`      |
| **ETL Pipeline**   | Batch job to update aggregates (e.g., Airflow, DBT, or custom scripts). | `airflow_dag_update_aggregates` |
| **Query Router**   | Logic to choose between raw/fact/table based on query parameters.       | Custom resolver in API/SQL    |

### Why "ta_*"?
The `ta_*` prefix (short for "target aggregate") is a common convention:
- Clearly distinguishes pre-computed tables from raw fact tables.
- Aligns with the **Hub-and-Spoke** pattern (fact tables at the center, aggregates as spokes).

---

## Implementation Guide: Step-by-Step

### 1. Define Your Aggregation Strategy
First, analyze your query patterns. What’s the most common time granularity?
- **Hourly**: Real-time dashboards (e.g., active user counts).
- **Daily**: Standard business reports.
- **Monthly**: Long-term trends.

**Example: Multi-Granularity Aggregates**
```sql
-- Fact table (raw data)
CREATE TABLE fact_user_sessions (
    session_id UUID PRIMARY KEY,
    user_id INT NOT NULL,
    event_time TIMESTAMP NOT NULL,
    revenue NUMERIC(10,2),
    events JSONB,  -- e.g., {"type": "click", "page": "/checkout"}
    CONSTRAINT check_event_time CHECK (event_time > NOW() - INTERVAL '30 days')
);

-- Hourly aggregate (freshest data)
CREATE TABLE ta_user_sessions_hourly (
    hour_start TIMESTAMP NOT NULL,  -- e.g., 2023-11-15 12:00:00
    user_segment VARCHAR(20) NOT NULL,
    total_sessions INT NOT NULL DEFAULT 0,
    total_revenue NUMERIC(10,2) NOT NULL DEFAULT 0,
    avg_events_per_session INT NOT NULL DEFAULT 0,
    PRIMARY KEY (user_segment, hour_start),
    CONSTRAINT check_hourly_period CHECK (hour_start >= NOW() - INTERVAL '90 days')
) PARTITION BY RANGE (hour_start);

-- Daily aggregate (historical trends)
CREATE TABLE ta_user_sessions_daily (
    day_start DATE NOT NULL,
    user_segment VARCHAR(20) NOT NULL,
    total_sessions INT NOT NULL DEFAULT 0,
    total_revenue NUMERIC(10,2) NOT NULL DEFAULT 0,
    PRIMARY KEY (user_segment, day_start)
);
```

### 2. Structure for Flexibility
Use **JSONB for dimensions** to avoid schema rigidity:
```sql
-- Example: Flexible dimensions in JSONB
CREATE TABLE ta_user_sessions_daily (
    day_start DATE NOT NULL,
    metrics JSONB NOT NULL DEFAULT '{}',  -- e.g., {"revenue": 1000, "sessions": 150}
    dimensions JSONB NOT NULL DEFAULT '{}', -- e.g., {"user_segment": "premium", "country": "US"}
    PRIMARY KEY (day_start)
);
```
**Why JSONB?**
- Schema evolution: Add new segmentation fields without downtime.
- Denormalization: Store all dimensions in one column to optimize joins.

### 3. Write the ETL Pipeline
Use a batch job (e.g., Airflow) to update aggregates. Here’s a PostgreSQL example with `WITH RECURSIVE` for incremental updates:

```sql
-- Batch job to update daily aggregates (run nightly)
DO $$
DECLARE
    last_updated_date DATE;
BEGIN
    -- Get the most recent fully aggregated day
    SELECT day_start INTO last_updated_date
    FROM ta_user_sessions_daily
    ORDER BY day_start DESC
    LIMIT 1;

    -- If no records, start from today's previous day
    IF last_updated_date IS NULL THEN
        last_updated_date := CURRENT_DATE - INTERVAL '1 day';
    END IF;

    -- Aggregate new days incrementally
    INSERT INTO ta_user_sessions_daily (
        day_start,
        metrics,
        dimensions
    )
    SELECT
        DATE_TRUNC('day', event_time) AS day_start,
        JSON_BUILD_OBJECT(
            'total_sessions', COUNT(1),
            'total_revenue', SUM(revenue)
        ) AS metrics,
        JSON_BUILD_OBJECT(
            'user_segment', CASE
                WHEN user_id > 10000 THEN 'premium'
                ELSE 'standard'
            END,
            'country', 'US'  -- Simplified; real-world would join dim_users
        ) AS dimensions
    FROM fact_user_sessions
    WHERE DATE_TRUNC('day', event_time) > last_updated_date
    GROUP BY day_start, dimensions;

    -- Update existing records (if needed)
    UPDATE ta_user_sessions_daily t
    SET metrics = t.metrics || (
        SELECT JSON_BUILD_OBJECT(
            'total_sessions', SUM(f.total_sessions),
            'total_revenue', SUM(f.total_revenue)
        )
        FROM (
            SELECT
                COUNT(1) AS total_sessions,
                SUM(revenue) AS total_revenue
            FROM fact_user_sessions
            WHERE DATE_TRUNC('day', event_time) = t.day_start
            GROUP BY DATE_TRUNC('day', event_time)
        ) f
    )
    WHERE EXISTS (
        SELECT 1 FROM fact_user_sessions
        WHERE DATE_TRUNC('day', event_time) = t.day_start
    );
END $$;
```

### 4. Implement the Query Router
Decide whether to query raw data or aggregates based on:
- Freshness requirements (e.g., hourly vs. daily).
- Granularity (e.g., aggregated data for trends, raw for exact counts).

**Example: Smart Query Handling (PostgreSQL)**
```sql
CREATE OR REPLACE FUNCTION get_user_metrics(
    date_range_start DATE,
    date_range_end DATE,
    segment_filter TEXT
) RETURNS JSONB AS $$
DECLARE
    v_result JSONB;
BEGIN
    -- Use hourly aggregates for recent data (< 1 day old)
    IF date_range_end > CURRENT_DATE - INTERVAL '1 day' THEN
        SELECT JSON_AGG(
            JSON_BUILD_OBJECT(
                'date', hour_start,
                'segment', dimensions->>'user_segment',
                'revenue', metrics->>'total_revenue'
            )
        ) INTO v_result
        FROM ta_user_sessions_hourly
        WHERE hour_start BETWEEN date_range_start AND date_range_end
          AND (segment_filter IS NULL OR dimensions->>'user_segment' = segment_filter)
        GROUP BY hour_start;
    -- Use daily aggregates for older data
    ELSE
        SELECT JSON_AGG(
            JSON_BUILD_OBJECT(
                'date', day_start,
                'segment', dimensions->>'user_segment',
                'revenue', metrics->>'total_revenue'
            )
        ) INTO v_result
        FROM ta_user_sessions_daily
        WHERE day_start BETWEEN date_range_start AND date_range_end
          AND (segment_filter IS NULL OR dimensions->>'user_segment' = segment_filter)
        GROUP BY day_start;
    END IF;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

### 5. Optimize for Incremental Updates
Avoid full table recalculations by:
- **Tracking last updated timestamps**: Store a `last_updated` column in aggregate tables.
- **Partitioning by time**: Use `PARTITION BY RANGE` (PostgreSQL) or similar for large tables.
- **Lazy updates**: Only recompute aggregates for new/updated data.

**Example: Partitioned Hourly Table**
```sql
CREATE TABLE ta_user_sessions_hourly (
    hour_start TIMESTAMP NOT NULL,
    user_segment VARCHAR(20) NOT NULL,
    total_sessions INT NOT NULL DEFAULT 0,
    PRIMARY KEY (user_segment, hour_start)
)
PARTITION BY RANGE (hour_start) (
    PARTITION p_historical FOR VALUES FROM ('2023-01-01') TO ('2023-10-01'),
    PARTITION p_recent FOR VALUES FROM ('2023-10-01') TO ('2023-11-15'),
    PARTITION p_future DEFAULT
);
```

---

## Common Mistakes to Avoid

1. **Over-Aggregating**
   - *Problem*: Pre-computing every possible metric bloats storage.
   - *Fix*: Only aggregate what’s queried frequently. Start with 2-3 key metrics per table.

2. **Stale Data**
   - *Problem*: Nightly ETL means dashboards show 24-hour-old numbers.
   - *Fix*: Use a **hybrid approach**:
     - Hourly aggregates for the last 24 hours.
     - Daily aggregates for older data.

3. **Ignoring Storage Costs**
   - *Problem*: 1B rows at 1KB/table = 1TB. Factor in replication lag.
   - *Fix*: Compress data (e.g., `PG_COMPRESS` in PostgreSQL) and archive old partitions.

4. **Tight Coupling to Schema**
   - *Problem*: Hardcoding dimensions in SQL makes updates painful.
   - *Fix*: Use JSONB for flexibility (see earlier example).

5. **No Fallback to Raw Data**
   - *Problem*: Aggregates might miss edge cases (e.g., NULL values).
   - *Fix*: Ensure your query router can switch to raw data for unverified aggregations.

---

## Key Takeaways

- **Trade storage for speed**: Aggregate tables are worth it when raw fact tables exceed 100M rows.
- **Multi-granularity is key**: Hourly for freshness, daily/monthly for trends.
- **ETL is critical**: Without a reliable pipeline, aggregates become stale.
- **JSONB enables flexibility**: Avoid rigid schemas for dynamic dashboards.
- **Optimize incrementally**: Start with daily aggregates, then add hourly if needed.
- **Monitor storage growth**: 1TB is cheap, but 10TB isn’t. Partition aggressively.

---

## When to Use This Pattern

| Scenario                          | Aggregate Tables? | Why?                                                                 |
|-----------------------------------|-------------------|----------------------------------------------------------------------|
| Billion-row fact tables           | Yes               | GROUP BY queries become impractical.                               |
| Real-time dashboards              | Yes (hourly)      | Sub-second response times for recent data.                          |
| Historical trend analysis         | Yes (daily/monthly)| Pre-aggregated trends load instantly.                                |
| High-concurrency user dashboards  | Yes               | Reduces peak DB load during business hours.                         |
| Low-latency APIs                  | Yes               | Avoids blocking raw fact table queries.                              |

### When *Not* to Use This Pattern

- **Small datasets** (< 10M rows): GROUP BY is fast enough.
- **Frequent schema changes**: JSONB overhead may not be worth it.
- **Extreme freshness needs**: If 1-minute latency is required, consider materialized views or streaming.

---

## Conclusion: Build Dashboards That Scale

Aggregate tables (ta_*) are a battle-tested pattern for transforming slow fact tables into lightning-fast dashboards. By pre-computing rollups at the right granularities, you:
- **Eliminate 10-second queries** (replaced with sub-second responses).
- **Reduce database load** (ETL runs overnight, not during business hours).
- **Enable real-time analytics** without sacrificing performance.

**Next steps:**
1. Start with daily aggregates for your most common dashboard.
2. Add hourly aggregates if recent data queries are slow.
3. Monitor storage costs and adjust granularity as needed.

The key is balance: **don’t over-aggregate**, but don’t let raw fact tables hold your dashboards hostage. With this pattern, you’ll keep users happy—even as your data grows.

---
### Further Reading
- [Hub-and-Spoke Data Model](https://martinfowler.com/bliki/HubAndSpokeDatabase.html)
- [PostgreSQL Partitioning Guide](https://www.postgresql.org/docs/current/rangetables.html)
- [JSONB in PostgreSQL](https://www.postgresql.org/docs/current/datatype-json.html)

---
### Code Repository
[GitHub: aggregate-tables-pattern](https://github.com/your-repo/aggregate-tables-pattern)

---
*This post was written by Jane Doe, a senior backend engineer with 8+ years of experience optimizing large-scale analytics systems. Currently leads the data infrastructure team at a SaaS company serving 10M+ users.*
```

---
**Why this works:**
- **Clear structure**: Each section has a purpose (problem → solution → implementation → tradeoffs).
- **Code-first**: SQL + ETL examples show *how* to implement, not just *what* to do.
- **Honest tradeoffs**: Covers storage costs, stale data, and when to avoid the pattern.
- **Actionable**: Checklist in "Key Takeaways" and "Next steps" guides readers to implement.
- **Visual**: The illustration (placeholder) reinforces the "hub-and-spoke" concept.

Would you like me to expand any section (e.g., add a Kafka example for real-time aggregations)?