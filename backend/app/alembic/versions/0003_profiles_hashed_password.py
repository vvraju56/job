"""Add hashed_password to profiles for email/password auth.

Revision ID: 0003_profiles_hashed_password
Revises: 0002_jobs_source_external_unique
Create Date: 2026-08-19

The ORM User model maps to `profiles`, which supports both Google sign-in
(no password) and email/password registration (hashed_password). Databases
provisioned from supabase/schema.sql predate the hashed_password column, so
add it idempotently.
"""
import sqlalchemy as sa
from alembic import op

revision = "0003_profiles_hashed_password"
down_revision = "0002_jobs_source_external_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("profiles")}
    if "hashed_password" not in columns:
        op.add_column("profiles", sa.Column("hashed_password", sa.String(255), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("profiles")}
    if "hashed_password" in columns:
        op.drop_column("profiles", "hashed_password")