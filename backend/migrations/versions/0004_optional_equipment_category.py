"""Allow equipment entry without a category while preserving existing records."""
from alembic import op
import sqlalchemy as sa

revision = "0004_optional_equipment_category"
down_revision = "0003_password_reset"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("equipment_items", "category_id", existing_type=sa.BigInteger(), nullable=True)


def downgrade():
    raise RuntimeError("Destructive downgrade disabled. Restore a reviewed backup instead.")
