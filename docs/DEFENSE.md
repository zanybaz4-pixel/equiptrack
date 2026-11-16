# EquipTrack defense rehearsal

Follow the 15-minute format in section 10 of the [MIS 215 brief](MIS215_TermProject_Brief.pdf). Use a synthetic borrower, a synthetic custodian, the laptop and a second device on the same private network.

| Time | Show | Evidence |
| --- | --- | --- |
| 0–2 min | The fictional school, its equipment register and need for shared data | Scenario sources and the boundary between the documented practices and the proposed workflow |
| 2–5 min | Browser, FastAPI and PostgreSQL through Nginx | Architecture diagram, ports, HTTPS, sessions and role enforcement |
| 5–11 min | T1 check availability, T2 request an item, T3 approve, T4 release, T5 return | A fresh synthetic request and the matching returned entry in borrower history |
| 11–13 min | Trace the same request | Browser Network entry, X-Request-ID, API trace and PostgreSQL request and audit rows |
| 13–15 min | Performance findings and alternative architecture | Six k6 trials, tier observations, limits and R7B conclusion |

## Rehearse the transaction

1. Check the certificate and app from the second device before presenting. Keep Ubuntu running. On the custodian device, prepare a separate browser profile for the custodian.
2. On the second device, sign in as a borrower, choose a serviceable asset and set a borrowing start close enough to reach during the rehearsal. Record the asset code and request ID. Sign in as the custodian on that device to perform the approval, release and return.
3. When the borrowing window opens, record pickup condition, then return condition. A good return preserves serviceability. Use a separate synthetic asset to demonstrate how a damaged return moves into maintenance.
4. Reopen the borrower history. Record the request ID, outcome, device and certificate behavior. Record a short backup demonstration with the credentials hidden.

## Rehearse the request trace

From Ubuntu, use the same gateway binding and app origin as the LAN session. Enable the optional defense logging overlay before taking the browser trace.

```bash
docker compose -f compose.yaml -f compose.defense.yaml up -d --wait --no-deps edge
docker compose -f compose.yaml -f compose.defense.yaml logs --no-color edge
```

For the browser trace, use Developer Tools **Network** to inspect POST /api/requests. Highlight the 201 status, X-Request-ID and returned request ID. Find that header value in the gateway log. It records only the HTTP method, fixed request path, status and request ID. Use the response's numeric request ID in the following read-only queries.

```sql
SELECT id, equipment_id, status FROM borrowing_requests WHERE id = 1;
SELECT action, entity_id, created_at
FROM audit_logs
WHERE entity_type = 'request' AND entity_id = 1
ORDER BY id;
```

After the trace, restart the gateway with the base Compose file using the active LAN session's environment values.

See the [verified HTTPS trace](phase6-trace.json), [protocol results](phase5-protocol-results.json), and [LAN rehearsal](PHASE5.md).

## Proposal presentation

- **0–1 minute:** Introduce the fictional school and show the DepEd lending and property-accountability sources.
- **1–2 minutes:** Describe the two roles, the five transactions, and why a shared record resolves availability and custody questions.
- **2–4 minutes:** Walk through the three-tier diagram, REST Option A, the selected tools and the requirement for HTTPS.
- **4–6 minutes:** Explain synthetic data and the scope, then show the milestones from approval and Week 14 through evaluation and defense.
