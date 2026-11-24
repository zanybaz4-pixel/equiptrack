# Gmail delivery for password resets

The Gmail alternative uses the owner's Google Apps Script project with the `MailApp` send-email scope. It does not read the Gmail inbox or use the owner's Gmail password. Render sends signed HTTPS requests, avoiding SMTP ports blocked by the free hosting plan.

## Setup

1. Create a standalone Apps Script project under the intended sending Google account. Copy [Code.gs](../infra/gmail/Code.gs) and [appsscript.json](../infra/gmail/appsscript.json). Keep the send-email scope explicit. Cloud exception logging remains enabled; the code catches delivery failures and does not log request bodies or secrets.
2. With the owner's specific approval, generate a cryptographically random connection secret of at least 32 bytes. Store it in Google Script Properties as `RELAY_SECRET`, set `APP_ORIGIN` to the exact EquipTrack HTTPS origin without a trailing slash, and set `RELAY_EXPIRES_AT` to a reviewed ISO 8601 expiry timestamp. A missing or expired authorization disables sending.
3. Prepare a **Web app** deployment, executing as the owner and with access **Anyone** so Render can call it without an interactive Google login. This exposes an HTTP endpoint, so obtain explicit approval before changing that access. The code requires a valid private signature on every send request; merely knowing the URL cannot authorize email. Keep the script project itself private.
4. The owner reviews Google's send-email permission. If Google shows a warning or requires account verification, let the owner complete that step directly. Then finish deployment and privately copy the `/macros/s/.../exec` URL.
5. Save these values in the existing Render service's private Environment settings: `RECOVERY_MAIL_PROVIDER=gmail`, `GMAIL_SCRIPT_URL` set to the deployed URL, and `GMAIL_RELAY_SECRET` set to the same secret. Do not put the secret in source, logs, chat, a URL, or screenshots. The existing Brevo settings are unused with the Gmail provider.
6. Deploy the EquipTrack source and perform a controlled mailbox test. Verify inbox delivery separately from API acceptance; have the owner enter any new account password privately.

## Live setup status — November 24, 2026

The owner's Apps Script web app is deployed as `zanybaz4@gmail.com`, executing as the owner with access set to Anyone. Its Script Properties contain the reviewed application origin, the private signing key, and authorization expiry `2026-12-24T23:59:59+08:00`. The same key was saved privately in the existing Render service alongside `RECOVERY_MAIL_PROVIDER=gmail` and the deployed script URL; all six existing environment keys were preserved. No key was saved in this repository.

Render deployment `dep-dc2pniei0phs73bi4v4g` became live at `2026-11-24T14:15:33Z`, using source commit `b8232e3a36046ef8fe9940f8048b08a4e94e1254`. Browser control worked in the continuation chat. The owner created the controlled EquipTrack account with a privately entered initial password; its active Borrower / Student status was confirmed in user management. A fresh live reset request reached the Google relay (Version 3 `doPost`, completed at 22:22:39 Asia/Manila), and the actual reset message was verified in `zanybaz4@gmail.com`'s inbox at 22:22 on November 24. The exact delivered link opened the reset form, with both password fields present and the token removed from the address bar. The owner entered and submitted the new password privately; the Password updated heading and reset-success message were observed afterward. The owner then signed in with the new password; the authenticated borrower dashboard and profile showing the controlled Gmail address were verified. Actual inbox delivery, password-reset completion and subsequent sign-in are verified.

## Security and limits

The relay accepts only the fixed EquipTrack reset template and configured HTTPS reset destination. Each request includes a timestamp, random request ID, recipient and 256-bit reset token, all covered by an HMAC-SHA256 signature. Requests older than five minutes, duplicate request IDs, missing signatures, invalid fields, expired relay authorization and excess sends are rejected. Stored replay markers omit addresses and reset tokens. A script lock serializes replay checks and sending; no more than 30 emails can be attempted per hour, and Google's remaining daily quota is checked. Original account-level limits and one-time reset-token checks remain in PostgreSQL.

Google's consumer-account MailApp allowance is currently 100 recipients per day, shared with other scripts using that account, and may change. The relay's daily quota check is authoritative at send time. This is suitable for a small demonstration; it is not a production delivery guarantee.

Apps Script redirects its response to Google's content host. The backend follows only HTTPS redirects to `script.googleusercontent.com`, retrieves the result with GET, and never forwards the signed POST body to the response URL. A provider failure is logged by exception type without secrets. No email is sent until all private configuration and Google authorization are complete.

Source checks: Python delivery tests cover signature generation, endpoint allowlisting and safe redirects. `node --test tests/gmail-relay.test.cjs` exercises the actual relay source with mocked Google services, covering signatures, replay, freshness, quota, locking, fixed links and expiry. These checks do not prove real Gmail delivery or Google authorization.

References: [MailApp](https://developers.google.com/apps-script/reference/mail/mail-app), [quotas](https://developers.google.com/apps-script/guides/services/quotas), [web app deployment](https://developers.google.com/apps-script/guides/web), [Content Service redirects](https://developers.google.com/apps-script/guides/content).
