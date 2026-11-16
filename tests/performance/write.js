import http from 'k6/http';
import { config, handleSummary, session, record, origin, fixture } from './workload.js';

export const options = config;
export { handleSummary };

export default function () {
  const borrower = session();
  const response = http.post(`${origin}/api/requests`, JSON.stringify({
    equipment_id: borrower.equipment_id,
    borrow_at: fixture.borrow_at,
    due_at: fixture.due_at,
    purpose: 'Synthetic MIS 215 performance trial',
  }), borrower.params);
  record(response, 201, (body) => body.status === 'pending' && body.equipment_id === borrower.equipment_id);
}
