"""Allow rebooking cancelled slots."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260527_0002"
down_revision: str | None = "20260527_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply migration."""
    op.drop_constraint("appointments_time_slot_id_key", "appointments", type_="unique")
    op.create_index(
        "ix_appointments_active_time_slot_id",
        "appointments",
        ["time_slot_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    """Rollback migration."""
    op.drop_index(
        "ix_appointments_active_time_slot_id",
        table_name="appointments",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_unique_constraint(
        "appointments_time_slot_id_key",
        "appointments",
        ["time_slot_id"],
    )
