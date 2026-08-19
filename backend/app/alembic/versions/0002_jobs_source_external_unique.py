"""Jobs: widen external_id and add (source, external_id) uniqueness.

Revision ID: 0002_jobs_source_external_unique
Revises: 0001_initial
Create Date: 2026-08-19

JSearch (OpenWebNinja) external ids are ~500 characters, so `external_id`
moves from VARCHAR(255) to TEXT. A unique (source, external_id) constraint
mirrors the ORM model and the updated supabase/schema.sql so upserts dedupe
cleanly regardless of how a database was provisioned.

Fresh databases are already created by 0001 via `Base.metadata.create_all`
(which uses the current ORM model: TEXT `external_id` + the unique
constraint), so this migration must be idempotent. On PostgreSQL a failed
statement aborts the enclosing transaction, so we inspect the schema first
instead of catching exceptions.
"""
import sqlalchemy as sa
from alembic import op

revision = "0002_jobs_source_external_unique"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if bind.dialect.name == "postgresql":
        columns = {col["name"]: col["type"] for col in inspector.get_columns("jobs")}
        if "external_id" in columns and not isinstance(columns["external_id"], sa.TEXT):
            op.alter_column("jobs", "external_id", existing_type=sa.VARCHAR(255), type_=sa.TEXT(), existing_nullable=True)

    existing = {uc["name"] for uc in inspector.get_unique_constraints("jobs")}
    if "uq_jobs_source_external" not in existing:
        # Seed/test data may contain duplicate (source, external_id) rows from
        # before the constraint existed. Delete duplicates (keep the lowest id)
        # so the unique index can be built.
        op.execute(
            "DELETE FROM jobs a USING jobs b "
            "WHERE a.id > b.id AND a.source = b.source AND "
            "(a.external_id IS NOT DISTINCT FROM b.external_id)"
        )
        op.create_unique_constraint("uq_jobs_source_external", "jobs", ["source", "external_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {uc["name"] for uc in inspector.get_unique_constraints("jobs")}
    if "uq_jobs_source_external" in existing:
        op.drop_constraint("uq_jobs_source_external", "jobs", type_="unique")
    if bind.dialect.name == "postgresql":
        columns = {col["name"]: col["type"] for col in inspector.get_columns("jobs")}
        if "external_id" in columns and isinstance(columns["external_id"], sa.TEXT):
            op.alter_column("jobs", "external_id", existing_type=sa.TEXT(), type_=sa.VARCHAR(255), existing_nullable=True)