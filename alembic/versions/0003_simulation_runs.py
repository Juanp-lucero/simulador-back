"""Create saved simulation runs.

Revision ID: 0003_simulation_runs
Revises: 0002_aircraft_routes
Create Date: 2026-11-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_simulation_runs"
down_revision: Union[str, None] = "0002_aircraft_routes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("route_ids", sa.JSON(), nullable=False),
        sa.Column("elapsed_s", sa.Float(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "elapsed_s >= 0 AND elapsed_s <= 86400",
            name="ck_simulation_runs_elapsed_range",
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_simulation_runs_owner_id", "simulation_runs", ["owner_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_simulation_runs_owner_id", table_name="simulation_runs")
    op.drop_table("simulation_runs")
