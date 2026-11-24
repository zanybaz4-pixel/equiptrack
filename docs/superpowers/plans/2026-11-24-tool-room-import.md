# Tool Room Directory inventory import

Goal: place all 174 owner-reviewed directory entries in Equipment Inventory on
the existing site. The owner requested available items; use the existing Good /
Serviceable defaults and let the custodian inspect/edit them later. Keep active
custody and reservation records intact.

Implementation:

1. Add regression coverage proving different items can share MT rack codes,
   retain distinct internal identifiers and be searched by rack.
2. Add a separate nullable storage_rack column, backfill existing display values,
   retain unique internal asset codes and legacy API compatibility. Update the
   editor, catalog and request displays to use storage_rack.
3. Apply a transactional one-time data migration for the reviewed 174-row JSON.
   Stable directory keys prevent duplicate imports. Reuse a single unambiguous
   existing name match and keep its ID/history; preserve active loan condition.
   Keep N/A values, record the blank apron location as Not recorded, and retain
   notes identifying unclear handwriting. Do not delete existing inventory.
4. Verify migration from 0004, all imported rows and shared racks, preserved
   borrowing links and conditions, no duplication after another upgrade, normal
   API creation/edit/search, and the existing regression suite in disposable DBs.
5. Review changes, push the existing deployment branch, deploy the same Render
   service, verify readiness, the new bundle and actual live inventory count and
   representative rows. Do not create paid resources or reset any database.

Stack: existing React/Vite, FastAPI/SQLAlchemy, Alembic and PostgreSQL. No new
dependencies, categories or quantity assumptions. Local WSL demo rebuild is out
of scope; its data remains preserved.
