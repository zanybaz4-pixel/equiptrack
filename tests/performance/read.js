import http from 'k6/http';
import { config, handleSummary, session, record, origin, fixture } from './workload.js';

export const options = config;
export { handleSummary };

export default function () {
  const query = [
    'limit=12',
    `borrow_at=${encodeURIComponent(fixture.borrow_at)}`,
    `due_at=${encodeURIComponent(fixture.due_at)}`,
  ].join('&');
  const response = http.get(`${origin}/api/equipment?${query}`, session().params);
  record(response, 200, (body) => Array.isArray(body.items) && body.items.length === 12);
}
