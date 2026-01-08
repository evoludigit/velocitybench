# Phase 8: Continuous Resource Monitoring

This directory contains the monitoring infrastructure for the FraiseQL Performance Assessment project.

## 📋 Overview

Phase 8 implements continuous resource monitoring during benchmark execution, providing:
- **Real-time metrics** at 1-second intervals
- **System-level monitoring** (CPU, memory, disk I/O, network)
- **Container-level monitoring** (per-framework resource usage)
- **Database monitoring** (connections, transactions, cache hit ratio)
- **Visual dashboards** for analysis and debugging

## 🏗️ Architecture

```
monitoring/
├── docker-compose.monitoring.yml  # Monitoring stack definition
├── prometheus.yml                 # Prometheus configuration
├── prometheus/
│   └── rules/
│       └── benchmark.yml          # 40+ recording rules
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── prometheus.yml     # Auto-configured datasource
        └── dashboards/
            ├── default.yml        # Dashboard provisioning
            └── fraiseql-performance.json  # Main dashboard (15 panels)
```

## 🚀 Quick Start

### 1. Start Monitoring Stack

```bash
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. Verify Services Running

```bash
# Check all containers are healthy
docker-compose -f docker-compose.monitoring.yml ps

# Verify Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'
```

### 3. Access Dashboards

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **cAdvisor**: http://localhost:8080

### 4. View Performance Dashboard

1. Open Grafana: http://localhost:3000
2. Login with `admin` / `admin`
3. Navigate to **Dashboards** → **FraiseQL Performance Benchmark**
4. Select time range and framework to analyze

## 📊 Dashboard Panels

The main dashboard includes 15 panels organized in 5 rows:

### Row 1: System Overview
- **CPU Usage** - Total, user, system, iowait breakdown
- **Memory Usage** - Percentage and available GB
- **Load Average** - 1m, 5m, 15m

### Row 2: Framework Comparison
- **CPU Usage per Framework** - Resource consumption comparison
- **Memory Usage per Framework** - Memory footprint analysis
- **Request Rate** - Throughput comparison (req/sec)
- **Response Time Percentiles** - p50, p95, p99 latency

### Row 3: Database Performance
- **Active Connections** - Active, idle, idle-in-transaction
- **Transaction Rate** - Commits and rollbacks per second
- **Cache Hit Ratio** - Buffer cache effectiveness (target: >95%)

### Row 4: I/O Performance
- **Network Throughput** - RX/TX rates in MB/s
- **Disk I/O** - Read/write rates in MB/s
- **Container Network I/O** - Per-framework network usage
- **Database Query Latency** - p50, p95, p99 at database level

### Row 5: Health Status
- **Framework Health** - UP/DOWN status for all 8 frameworks

## 🔧 Configuration

### Prometheus Scrape Interval

**Critical for micro-benchmarks**: 1-second scrape interval configured in `prometheus.yml`

```yaml
global:
  scrape_interval: 1s       # Sample every second
  evaluation_interval: 1s   # Evaluate rules every second
```

### Recording Rules

40+ recording rules pre-aggregate metrics for fast dashboard queries:

- **System metrics**: CPU, memory, disk I/O, network
- **Container metrics**: Per-framework resource usage
- **Database metrics**: Connection counts, transaction rates
- **Application metrics**: Request rates, response times

**Location**: `monitoring/prometheus/rules/benchmark.yml`

**Reload rules**:
```bash
curl -X POST http://localhost:9090/-/reload
```

### Data Retention

- **Prometheus**: 30 days (configurable in docker-compose)
- **Grafana**: Persistent across restarts via Docker volume

## 🎯 Monitoring Targets

Prometheus scrapes metrics from:

1. **Node Exporter** (port 9100) - System metrics
2. **cAdvisor** (port 8080) - Container metrics  
3. **PostgreSQL Exporter** (port 9187) - Database metrics
4. **Framework endpoints** - Application metrics (if exposed)

## 📈 Using the Dashboard During Benchmarks

### Before Benchmark
1. Start monitoring stack
2. Verify all targets are UP in Prometheus
3. Open Grafana dashboard
4. Set time range to "Last 5 minutes" with auto-refresh

### During Benchmark
1. Monitor real-time metrics as test runs
2. Watch for:
   - CPU spikes correlating with latency increases
   - Memory growth (potential leaks)
   - I/O bottlenecks (high iowait)
   - Database connection saturation
   - Cache hit ratio drops

### After Benchmark
1. Select time range covering the benchmark run
2. Analyze:
   - Framework comparison (CPU, memory, throughput)
   - Bottleneck identification (CPU/memory/I/O/database)
   - Query performance patterns
3. Export data for reporting

## 🔍 Troubleshooting

### Prometheus Not Scraping

```bash
# Check Prometheus logs
docker logs prometheus

# Verify targets are reachable
curl http://localhost:9090/api/v1/targets

# Reload configuration
curl -X POST http://localhost:9090/-/reload
```

### Grafana Dashboard Not Loading

```bash
# Check Grafana logs
docker logs grafana

# Verify datasource connection
curl http://localhost:3000/api/datasources

# Restart Grafana
docker-compose -f docker-compose.monitoring.yml restart grafana
```

### Missing Metrics

```bash
# Check if exporter is running
docker ps | grep -E "node-exporter|cadvisor|postgres-exporter"

# Test exporter endpoint
curl http://localhost:9100/metrics  # node-exporter
curl http://localhost:8080/metrics  # cadvisor
curl http://localhost:9187/metrics  # postgres-exporter
```

### High Resource Usage

```bash
# Check Prometheus storage size
du -sh monitoring/prometheus_data

# Reduce retention period (in docker-compose.yml)
--storage.tsdb.retention.time=7d  # Instead of 30d

# Restart Prometheus
docker-compose -f docker-compose.monitoring.yml restart prometheus
```

## 📝 Metrics Reference

### Key Metrics to Monitor

| Metric | Purpose | Target |
|--------|---------|--------|
| CPU Usage % | System load | <70% |
| Memory Usage % | Memory pressure | <80% |
| Load Average | Queue depth | <CPU count |
| DB Cache Hit % | Buffer effectiveness | >95% |
| DB Connections | Connection pool usage | <max_connections |
| Request Rate | Throughput | Framework-specific |
| Response Time p99 | Tail latency | <200ms (Python), <100ms (Go) |

### Recording Rules Available

View all pre-computed metrics:
```bash
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | .name'
```

## 🧪 Testing the Monitoring Stack

### Quick Validation

```bash
# Start monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Wait 30 seconds for startup
sleep 30

# Check all services healthy
docker-compose -f docker-compose.monitoring.yml ps

# Verify Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'
# Should return: 4 (node-exporter, cadvisor, postgres-exporter, prometheus)

# Verify recording rules loaded
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups | length'
# Should return: 5 (benchmark rules)

# Access Grafana
curl -s http://localhost:3000/api/health | jq '.database'
# Should return: "ok"
```

### Full Integration Test

```bash
# Start monitoring + main stack
docker-compose -f docker-compose.monitoring.yml up -d
docker-compose up -d

# Wait for all services
sleep 60

# Run simple benchmark
cd tests/perf
./scripts/run-workload.sh simple fraiseql 10s

# Check metrics captured
curl -s "http://localhost:9090/api/v1/query?query=up" | jq '.data.result | length'

# Open Grafana dashboard and verify panels rendering
```

## 🎓 Best Practices

### During Development
- Keep monitoring stack running for quick feedback
- Use 5-second auto-refresh in Grafana
- Monitor single framework at a time initially

### During Benchmarking
- Start monitoring 2 minutes before benchmark
- Run warmup phase while monitoring stabilizes
- Keep monitoring running 1 minute after benchmark
- Export dashboard as PDF for reporting

### For Analysis
- Use absolute time ranges (not "Last 5m")
- Correlate latency spikes with resource metrics
- Compare baseline runs vs optimized runs
- Track metrics over multiple runs for consistency

## 📚 Additional Resources

- **Prometheus Documentation**: https://prometheus.io/docs/
- **Grafana Documentation**: https://grafana.com/docs/
- **Phase 8 Planning**: `../.phases/PHASE_8*.md` (50,000+ words)
- **Recording Rules**: `prometheus/rules/benchmark.yml`

## 🔄 Maintenance

### Backup Configuration

```bash
# Backup Prometheus data
docker cp prometheus:/prometheus ./backup/prometheus-$(date +%Y%m%d)

# Backup Grafana dashboards
docker cp grafana:/var/lib/grafana ./backup/grafana-$(date +%Y%m%d)
```

### Clean Up Old Data

```bash
# Stop monitoring stack
docker-compose -f docker-compose.monitoring.yml down

# Remove volumes (WARNING: deletes all metrics)
docker volume rm monitoring_prometheus_data monitoring_grafana_data

# Restart fresh
docker-compose -f docker-compose.monitoring.yml up -d
```

## ✅ Success Criteria

Phase 8 is complete when:

- ✅ All monitoring containers running and healthy
- ✅ Prometheus scraping all targets (4+) successfully
- ✅ Recording rules loaded (40+)
- ✅ Grafana accessible with auto-configured datasource
- ✅ Dashboard displays all 15 panels with real data
- ✅ 1-second sampling interval confirmed
- ✅ Metrics visible during benchmark execution

## 🎉 Next Steps

With Phase 8 complete, proceed to:

**Phase 9: Benchmark Execution**
1. Run all 8 workloads against all 8 frameworks
2. Capture metrics continuously
3. Analyze results using Grafana dashboard
4. Generate comparison reports
5. Identify optimization opportunities

See `../.phases/phase-9-execution.md` for details.

---

**Status**: Phase 8 Complete ✅  
**Last Updated**: December 16, 2025  
**Monitoring Stack Version**: 1.0
