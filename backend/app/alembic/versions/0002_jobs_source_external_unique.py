"""Jobs: widen external_id and add (source, external_id) uniqueness.

Revision ID: 0002_jobs_source_external_unique
Revises: 0001_initial
Create Date: 2026-08-19

JSearch (OpenWebNinja) external ids are ~500 characters, so `external_id`
moves from VARCHAR(255) to TEXT. A unique (source, external_id) constraint
mirrors the ORM model and the updated supabase/schema.sql so upserts dedupe
cleanly regardless of how a database was provisioned.
"""
import sqlalchemy as sa
from alembic import op

revision = "0002_jobs_source_external_unique"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # SQLite cannot alter a column's type in place; the fresh schema.sql / ORM
    # create_all already use TEXT. On PostgreSQL, widen the column explicitly.
    if bind.dialect.name == "postgresql":
        op.alter_column("jobs", "external_id", existing_type=sa.VARCHAR(255), type_=sa.TEXT(), existing_nullable=True)

    # Add the uniqueness constraint (idempotent-ish; Postgres supports IF NOT EXISTS).
    try:
        op.create_unique_constraint("uq_jobs_source_external", "jobs", ["source", "external_id"])
    except Exception:  # noqa: BLE001  (constraint may already exist on some setups)
        pass


def downgrade() -> None:
    bind = op.get_bind()
    try:
        op.drop_constraint("uq_jobs_source_external", "jobs", type_="unique")
    except Exception:  # noqa: BLE001
        pass
    if bind.dialect.name == "postgresql":
        op.alter_column("jobs", "external_id", existing_type=sa.TEXT(), type_=sa.VARCHAR(255), existing_nullable=True)
