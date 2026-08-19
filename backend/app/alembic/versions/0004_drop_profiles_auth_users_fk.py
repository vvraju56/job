"""Drop profiles.id FK to auth.users.

Revision ID: 0004_drop_profiles_auth_users_fk
Revises: 0003_profiles_hashed_password
Create Date: 2026-08-19

The app manages its own authentication (email/password via hashed_password,
plus Firebase Admin SDK for Google sign-in) and generates profile UUIDs
itself. The schema.sql FK `profiles_id_fkey` referencing `auth.users(id)`
breaks both flows because those ids never exist in auth.users. Drop it.
"""
import sqlalchemy as sa
from alembic import op

revision = "0004_drop_profiles_auth_users_fk"
down_revision = "0003_profiles_hashed_password"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "select conname from pg_constraint "
            "where conrelid='profiles'::regclass and contype='f' "
            "and conname='profiles_id_fkey'"
        )
    ).fetchall()
    if rows:
        op.drop_constraint("profiles_id_fkey", "profiles", type_="foreignkey")


def downgrade() -> None:
    op.create_foreign_key(
        "profiles_id_fkey",
        "profiles",
        "auth.users",
        ["id"],
        ["id"],
        ondelete="CASCADE",
    )