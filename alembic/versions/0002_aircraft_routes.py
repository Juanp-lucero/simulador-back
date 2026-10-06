"""Create aircraft, routes, and route waypoints.

Revision ID: 0002_aircraft_routes
Revises: 0001_create_users
Create Date: 2026-10-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_aircraft_routes"
down_revision: Union[str, None] = "0001_create_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "aircraft",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("registration", sa.String(length=15), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("cruise_speed_mps", sa.Float(), nullable=False),
        sa.Column("max_altitude_m", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "cruise_speed_mps > 0", name="ck_aircraft_speed_positive"
        ),
        sa.CheckConstraint(
            "max_altitude_m > 0", name="ck_aircraft_altitude_positive"
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("registration", name="uq_aircraft_registration"),
    )
    op.create_index("ix_aircraft_owner_id", "aircraft", ["owner_id"])

    op.create_table(
        "routes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("aircraft_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "name", name="uq_routes_owner_name"),
    )
    op.create_index("ix_routes_owner_id", "routes", ["owner_id"])

    op.create_table(
        "route_waypoints",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("route_id", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("latitude_deg", sa.Float(), nullable=False),
        sa.Column("longitude_deg", sa.Float(), nullable=False),
        sa.Column("altitude_m", sa.Float(), nullable=False),
        sa.Column("speed_mps", sa.Float(), nullable=False),
        sa.CheckConstraint(
            "altitude_m >= 0", name="ck_route_waypoints_altitude_nonnegative"
        ),
        sa.CheckConstraint(
            "latitude_deg >= -90 AND latitude_deg <= 90",
            name="ck_route_waypoints_latitude_range",
        ),
        sa.CheckConstraint(
            "longitude_deg >= -180 AND longitude_deg <= 180",
            name="ck_route_waypoints_longitude_range",
        ),
        sa.CheckConstraint(
            "sequence >= 1", name="ck_route_waypoints_sequence_positive"
        ),
        sa.CheckConstraint(
            "speed_mps > 0", name="ck_route_waypoints_speed_positive"
        ),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("route_id", "sequence", name="uq_route_waypoints_sequence"),
    )
    op.create_index("ix_route_waypoints_route_id", "route_waypoints", ["route_id"])


def downgrade() -> None:
    op.drop_index("ix_route_waypoints_route_id", table_name="route_waypoints")
    op.drop_table("route_waypoints")
    op.drop_index("ix_routes_owner_id", table_name="routes")
    op.drop_table("routes")
    op.drop_index("ix_aircraft_owner_id", table_name="aircraft")
    op.drop_table("aircraft")
