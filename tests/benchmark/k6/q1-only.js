/**
 * VelocityBench k6 — Q1-Only Benchmark
 *
 * Isolates Q1 performance to understand baseline throughput.
 * Q1 = users(limit: 20) { id username fullName }
 *
 * Stages:
 *   0:00 –  0:30  Warmup     (10 VUs)
 *   0:30 –  2:30  Ramp-up    (10 → 100 VUs)
 *   2:30 –  7:30  Sustained  (100 VUs, 5 minutes)
 *   7:30 –  8:00  Cooldown   (100 → 0 VUs)
 *
 * Usage:
 *   k6 run --env FRAMEWORK=fraiseql-tv tests/benchmark/k6/q1-only.js
 *
 * Expected: Higher RPS than full_suite.js due to no expensive Q3
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { FRAMEWORK_URLS, GQL_QUERIES, ALICE_UUID } from './config.js';

// Framework selection
const FRAMEWORK = __ENV.FRAMEWORK || 'strawberry';
const CONFIG = FRAMEWORK_URLS[FRAMEWORK];

if (!CONFIG) {
  throw new Error(
    `Unknown framework: "${FRAMEWORK}". ` +
    `Valid values: ${Object.keys(FRAMEWORK_URLS).join(', ')}`
  );
}

// Metrics
const errorRate = new Rate('errors');
const q1Duration = new Trend('q1_duration_ms', true);
const q1Requests = new Counter('q1_requests');

// Stages
export const options = {
  stages: [
    { duration: '30s', target: 10  },
    { duration: '2m',  target: 100 },
    { duration: '5m',  target: 100 },
    { duration: '30s', target: 0   },
  ],
  thresholds: {
    'http_req_failed':   ['rate<0.01'],
    'http_req_duration': ['p(99)<2000'],
    'errors':            ['rate<0.05'],
  },
};

// Request helper
function gqlPost(query) {
  const payload = JSON.stringify({ query });
  const params = {
    headers: { 'Content-Type': 'application/json' },
    tags: { framework: FRAMEWORK },
  };
  const res = http.post(CONFIG.url, payload, params);
  const ok = check(res, {
    'HTTP 200': (r) => r.status === 200,
    'no gql errors': (r) => {
      try {
        const body = JSON.parse(r.body);
        return !body.errors || body.errors.length === 0;
      } catch { return false; }
    },
    'has data': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.data !== null && body.data !== undefined;
      } catch { return false; }
    },
  });
  errorRate.add(!ok);
  q1Duration.add(res.timings.duration);
  q1Requests.add(1);
  return res;
}

// Main scenario — Q1 only
export default function () {
  gqlPost(GQL_QUERIES.Q1);

  // Minimal think time
  sleep(Math.random() * 0.1);
}

// Summary
export function handleSummary(data) {
  const m = data.metrics;

  const summary = {
    framework:      FRAMEWORK,
    timestamp:      new Date().toISOString(),
    test_type:      'Q1-only',
    rps:            m.http_reqs?.values?.rate            ?? 0,
    p50_ms:         m.http_req_duration?.values?.['p(50)'] ?? 0,
    p95_ms:         m.http_req_duration?.values?.['p(95)'] ?? 0,
    p99_ms:         m.http_req_duration?.values?.['p(99)'] ?? 0,
    error_rate:     m.http_req_failed?.values?.rate       ?? 0,
    q1_p99_ms:      m.q1_duration_ms?.values?.['p(99)']   ?? 0,
    q1_count:       m.q1_requests?.values?.count          ?? 0,
    total_requests: m.http_reqs?.values?.count            ?? 0,
  };

  const dateStr   = new Date().toISOString().split('T')[0];
  const outFile   = `reports/k6-${FRAMEWORK}-q1-only-${dateStr}.json`;
  const stdout    = (
    `\n${'='.repeat(60)}\n` +
    `${FRAMEWORK} — k6 Q1-Only Benchmark\n` +
    `${'='.repeat(60)}\n` +
    `RPS:      ${summary.rps.toFixed(0)}\n` +
    `p50:      ${summary.p50_ms.toFixed(1)} ms\n` +
    `p95:      ${summary.p95_ms.toFixed(1)} ms\n` +
    `p99:      ${summary.p99_ms.toFixed(1)} ms\n` +
    `Errors:   ${(summary.error_rate * 100).toFixed(2)}%\n` +
    `Requests: ${summary.total_requests}\n` +
    `Q1 p99:   ${summary.q1_p99_ms.toFixed(1)} ms\n`
  );

  return {
    [outFile]: JSON.stringify(summary, null, 2),
    stdout,
  };
}
