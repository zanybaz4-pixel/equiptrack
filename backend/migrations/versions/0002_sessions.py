"""Add revocable sessions and the grants required by the lending API."""
from pathlib import Path

from alembic import op

revision = "0002_sessions"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().exec_driver_sql(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Destructive downgrade disabled. Restore a reviewed backup instead.")
