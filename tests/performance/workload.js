import { check, sleep } from 'k6';
import { SharedArray } from 'k6/data';
import execution from 'k6/execution';
import { Counter, Rate, Trend } from 'k6/metrics';

export const origin = 'https://localhost:28443';
const fixtures = new SharedArray('isolated EquipTrack fixtures', () => [
  JSON.parse(open('/fixture/sessions.json')),
]);
export const fixture = fixtures[0];
const vus = Number(__ENV.VUS || '1');
if (fixture.origin !== origin || ![1, 10, 50].includes(vus) || fixture.borrowers.length < vus) {
  throw new Error('Expected the isolated EquipTrack fixture and 1, 10, or 50 users');
}

const requests = new Counter('transaction_requests');
const latency = new Trend('transaction_latency', true);
const errors = new Rate('transaction_http_errors');
const invalid = new Rate('transaction_validation_errors');

export const config = {
  scenarios: {
    measure: { executor: 'constant-vus', vus, duration: __ENV.DURATION || '30s', gracefulStop: '10s' },
  },
  summaryTrendStats: ['avg', 'p(95)', 'min', 'max', 'count'],
  thresholds: {
    transaction_http_errors: ['rate<0.01'],
    transaction_validation_errors: ['rate<0.01'],
  },
};

export function session() {
  const borrower = fixture.borrowers[execution.vu.idInTest - 1];
  return {
    equipment_id: borrower.equipment_id,
    params: {
      cookies: { [borrower.cookie_name]: borrower.cookie_value },
      headers: {
        Origin: origin,
        'Content-Type': 'application/json',
        'X-CSRF-Token': borrower.csrf_token,
      },
      redirects: 0,
      timeout: '8s',
      tags: { workload: __ENV.WORKLOAD },
    },
  };
}

export function record(response, expectedStatus, matchesBody) {
  requests.add(1);
  latency.add(response.timings.duration);
  errors.add(response.status !== expectedStatus);
  const valid = check(response, {
    'expected status and response body': (result) => {
      if (result.status !== expectedStatus) return false;
      try {
        return matchesBody(result.json());
      } catch {
        return false;
      }
    },
  });
  invalid.add(!valid);
  sleep(1);
}

export function handleSummary(data) {
  return {
    '/results/summary.json': JSON.stringify(data, null, 2) + '\n',
    stdout: `${__ENV.WORKLOAD} at ${vus} VUs finished with ${data.metrics.transaction_requests?.values.count || 0} transactions\n`,
  };
}
