"""Create users, drivers, and vehicles tables

Revision ID: 0001_initial
Revises: 
Create Date: 2026-09-24 00:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("RIDER", "DRIVER", "ADMIN", name="user_role", native_enum=False),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("phone"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_phone"), "users", ["phone"], unique=True)

    # 2. Drivers table
    op.create_table(
        "drivers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("license_number", sa.String(length=50), nullable=False),
        sa.Column(
            "status",
            sa.Enum("OFFLINE", "AVAILABLE", "BUSY", name="driver_status", native_enum=False),
            nullable=False,
        ),
        sa.Column("current_latitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("current_longitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column(
            "rating_average",
            sa.Numeric(precision=3, scale=2),
            server_default=sa.text("5.00"),
            nullable=False,
        ),
        sa.Column("total_rides", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("license_number"),
    )
    op.create_index(
        op.f("ix_drivers_license_number"), "drivers", ["license_number"], unique=True
    )

    # 3. Vehicles table
    op.create_table(
        "vehicles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("driver_id", sa.Uuid(), nullable=False),
        sa.Column(
            "vehicle_type",
            sa.Enum("BIKE", "AUTO", "SEDAN", "SUV", name="vehicle_type", native_enum=False),
            nullable=False,
        ),
        sa.Column("registration_number", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=50), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("registration_number"),
    )
    op.create_index(
        op.f("ix_vehicles_registration_number"),
        "vehicles",
        ["registration_number"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_vehicles_registration_number"), table_name="vehicles")
    op.drop_table("vehicles")
    op.drop_index(op.f("ix_drivers_license_number"), table_name="drivers")
    op.drop_table("drivers")
    op.drop_index(op.f("ix_users_phone"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
