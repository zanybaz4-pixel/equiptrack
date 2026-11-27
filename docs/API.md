# REST API over HTTPS

The [OpenAPI specification](openapi.json) lists the implemented endpoints, methods, path and query parameters, JSON request and response schemas, and status codes. With the Compose stack running, the application serves its live contract at `https://localhost:8443/api/openapi.json` and Swagger UI at `https://localhost:8443/api/docs`.

## Authentication and requests

- Send JSON to `POST /api/auth/login` with the email and password and the configured browser `Origin`. A successful response sets the secure session cookie and returns the user and CSRF token.
- Send the cookie on authenticated reads. `GET /api/auth/me` returns the current user and CSRF token.
- For authenticated writes, send the cookie, the configured `Origin` and the token in `X-CSRF-Token`. Use the operation’s request schema for the body.
- Sign out with `POST /api/auth/logout`. Optional password recovery uses `POST /api/auth/forgot-password` and `POST /api/auth/reset-password`. [Password recovery setup](PASSWORD_RECOVERY.md)

Request cancellation uses `DELETE /api/requests/{request_id}` and retains the history. Custodians decide requests with `PATCH /api/requests/{request_id}/decision`, release equipment with `POST /api/requests/{request_id}/release`, and record returns with `PUT /api/requests/{request_id}/return`.

API errors use the envelope `{"error":{"code":"…","message":"…","request_id":"…"}}`. The operation in OpenAPI lists its applicable failures. For integration and protocol checks, see the [testing guide](TESTING.md).
