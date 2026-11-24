"""Add expiring recovery tokens and shared per-address delivery limits."""
from pathlib import Path

from alembic import op

revision = "0003_password_reset"
down_revision = "0002_sessions"
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().exec_driver_sql(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Destructive downgrade disabled. Restore a reviewed backup instead.")
