# Password recovery

The sign-in page includes **Forgot password?**. Recovery uses a single-use email link valid for 15 minutes. Users choose an EquipTrack password of 12–128 characters, confirm it, and sign in again. A successful reset invalidates all sessions and outstanding reset links for that account. Other accounts are unaffected.

## Delivery setup

The user chose the [Gmail delivery alternative](GMAIL_DELIVERY.md) after Brevo's phone-verification step could not be completed. That provider uses signed HTTPS requests and Google's send-email permission. The Brevo instructions below remain an optional alternative. Real inbox delivery is pending until the chosen provider is authorized and configured.

The implementation uses Brevo's HTTPS transactional email API. Render's free web services block outbound SMTP ports 25, 465 and 587, so a Gmail SMTP password is not the delivery configuration for this deployment.

1. Create a free Brevo account and complete its required profile. The account owner supplies their own contact/address details privately; the project does not invent a university affiliation or mailing address.
2. Add and verify a sender in Brevo's transactional email settings. Complete any provider-required account or sender approval.
3. Create a dedicated API key for EquipTrack. Save it privately as `BREVO_API_KEY` in the existing Render service's Environment settings, together with `MAIL_FROM_EMAIL` set to the verified sender address. Never paste the key into chat, Git or screenshots. For local Compose, put these values in the ignored `.env` and recreate the API service.
4. Deploy the updated source. The Render runtime passes these delivery settings to FastAPI without passing the migration owner or demo-provisioning passwords.
5. Use a controlled account you own to request a link, check its inbox/spam, open that exact link, choose a new password privately and verify sign-in. Provider acceptance does not prove inbox delivery. Do not reset another person's account as a test.

Until delivery is configured, the request endpoint returns a clear 503 message directing the user to their custodian; it does not falsely claim that an email was sent. The existing `example.invalid` demo addresses cannot receive email. Existing accounts, passwords and business records are not reset during migration or deployment.

## Safeguards

- A random 256-bit token is emailed; only its SHA-256 hash is stored in PostgreSQL. It never appears in an API response or application log.
- The link uses the configured HTTPS application origin, not an untrusted Host or return-URL parameter. The token is in the browser fragment, omitted from HTTP requests and Referer headers, and removed from the address bar when the reset form opens.
- Account-existence responses are identical for active, unknown and delivery-limited addresses. Email delivery runs after the response; provider failures are logged by exception type without email addresses, keys, passwords or reset links.
- Shared PostgreSQL counters permit at most one delivery per minute and five per hour per normalized address. Nginx also limits both recovery routes. Expired tokens and day-old counters are pruned during requests.
- Exact Origin checks protect both anonymous POST routes. Password hashing uses the existing Argon2 implementation and its concurrency bound. User-row locking makes concurrent link consumption and login/session invalidation consistent. No automatic sign-in follows recovery.
- Migration `0003_password_reset` adds two tables and grants only their needed runtime access. No existing table or record is dropped.

## Verification boundary

On November 24, 2026, 44 non-database API/configuration/recovery checks and 14 isolated PostgreSQL workflow checks passed. The PostgreSQL checks include concurrent reset-link use, token expiry and session invalidation using the restricted application role. Email delivery was intercepted for these tests; no real mailbox or existing account password was changed. The test migration owner received `pg_read_all_stats` only inside the disposable database to observe the existing concurrency tests; no production role was granted that permission.

Automated checks use fictional accounts and intercepted email delivery. They cover token hashing, expiry, replay/concurrent consumption, account/session isolation, request cooldown/quotas, invalid input and Origin rejection. Live inbox delivery and the owner-entered new-password flow require the configured Brevo sender and an authorized controlled mailbox; they must be reported separately from automated tests.

References: [Brevo transactional email API](https://developers.brevo.com/docs/send-a-transactional-email), [Render free-service restrictions](https://render.com/docs/free), [OWASP password recovery guidance](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html).
