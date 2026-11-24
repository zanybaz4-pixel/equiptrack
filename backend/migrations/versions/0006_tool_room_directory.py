"""Import the owner's reviewed 174-row directory without replacing existing data."""
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from alembic import op
import sqlalchemy as sa

revision = "0006_tool_room_directory"
down_revision = "0005_storage_rack"
branch_labels = None
depends_on = None


def upgrade():
    items = json.loads((Path(__file__).parents[1] / "data/tool_room_directory_2026.json").read_text(encoding="utf-8"))["items"]
    if len(items) != 174 or len({item["key"] for item in items}) != 174:
        raise RuntimeError("The reviewed directory must contain exactly 174 unique rows.")
    for item in items:
        for field, maximum in (("key", 64), ("name", 120), ("storage_rack", 40), ("location", 120)):
            if not isinstance(item[field], str) or not item[field].strip() or len(item[field]) > maximum or "\x00" in item[field]:
                raise RuntimeError("Invalid directory field: " + field)
    db = op.get_bind()
    created = reused = 0
    for item in items:
        if db.scalar(sa.text("SELECT id FROM equipment_items WHERE directory_key=:key"), item) is not None:
            continue
        # Reuse only one unambiguous name match; never guess between duplicates.
        matches = db.execute(sa.text("""SELECT id FROM equipment_items
            WHERE lower(trim(name))=lower(trim(:name)) AND directory_key IS NULL FOR UPDATE"""), item).scalars().all()
        if len(matches) == 1:
            db.execute(sa.text("""UPDATE equipment_items SET storage_rack=:storage_rack,
                location=:location, directory_key=:key WHERE id=:id"""), {**item, "id": matches[0]})
            reused += 1
        else:
            code = "ET-DIR-" + uuid5(NAMESPACE_URL, item["key"]).hex[:24]
            db.execute(sa.text("""INSERT INTO equipment_items
                (asset_code,storage_rack,directory_key,name,location,description,condition,service_status)
                VALUES(:code,:storage_rack,:key,:name,:location,:notes,'good','serviceable')"""), {**item, "code": code})
            created += 1
    # Existing IDs, condition, service state, loans, reservations and audits survive.
    print(f"Tool Room Directory: {created} added, {reused} existing entries linked.")


def downgrade():
    raise RuntimeError("Directory entries may have borrowing history; destructive downgrade disabled.")
