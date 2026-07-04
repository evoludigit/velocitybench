// Universal scenario runner for bench_sequential.py --loadgen k6.
//
// One iteration = one benchmark cycle: every step in cfg.steps is executed in
// order (a single request for plain scenarios; the full request chain for
// composite scenarios like classical MC1). Iteration rate is therefore the
// cycles/second the Python harness reports, and iteration_duration is the
// cycle latency.
//
// Config JSON (path in __ENV.SCENARIO_CONFIG):
// {
//   "concurrency": 40,
//   "duration_secs": 5,
//   "steps": [
//     {"method": "POST", "url": "http://…/graphql",
//      "body": "{…}"            // fixed body, or
//      "bodies": ["{…}", …],    // rotated per iteration (row-lock spreading)
//      "validate": "graphql"    // graphql | rest
//     }
//   ]
// }

import http from 'k6/http';
import { check } from 'k6';
import exec from 'k6/execution';

const cfg = JSON.parse(open(__ENV.SCENARIO_CONFIG));

export const options = {
  vus: cfg.concurrency,
  duration: `${cfg.duration_secs}s`,
  summaryTrendStats: ['avg', 'med', 'p(95)', 'p(99)', 'max'],
};

const JSON_HEADERS = { 'Content-Type': 'application/json' };

function stepBody(step) {
  if (step.bodies) {
    return step.bodies[exec.scenario.iterationInTest % step.bodies.length];
  }
  return step.body || null;
}

function stepUrl(step) {
  // urls rotate on the same iteration index as bodies, so paired lists
  // (REST mutation: url picks the row, body picks the new value) stay in sync.
  if (step.urls) {
    return step.urls[exec.scenario.iterationInTest % step.urls.length];
  }
  return step.url;
}

const validators = {
  graphql: (r) =>
    r.status === 200 &&
    typeof r.body === 'string' &&
    r.body.includes('"data"') &&
    !r.body.includes('"errors"'),
  rest: (r) => r.status === 200,
};

export default function () {
  for (const step of cfg.steps) {
    const url = stepUrl(step);
    const res =
      step.method === 'GET'
        ? http.get(url)
        : http.request(step.method, url, stepBody(step), { headers: JSON_HEADERS });
    check(res, { ok: validators[step.validate || 'rest'] });
  }
}
