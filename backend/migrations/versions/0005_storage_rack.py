"""Separate shared storage racks from unique internal item identifiers."""
from alembic import op
import sqlalchemy as sa

revision = "0005_storage_rack"
down_revision = "0004_optional_equipment_category"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("equipment_items", sa.Column("storage_rack", sa.String(40), nullable=True))
    op.add_column("equipment_items", sa.Column("directory_key", sa.String(64), nullable=True))
    op.create_unique_constraint("equipment_items_directory_key_key", "equipment_items", ["directory_key"])
    op.create_check_constraint("storage_rack_not_blank", "equipment_items", "storage_rack IS NULL OR length(trim(storage_rack)) > 0")
    op.execute("UPDATE equipment_items SET storage_rack = asset_code")


def downgrade():
    raise RuntimeError("Destructive downgrade disabled. Restore a reviewed backup instead.")
