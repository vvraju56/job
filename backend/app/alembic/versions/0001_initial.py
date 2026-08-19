"""Initial Makeable Jobs schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-15

The initial migration creates all tables from the ORM metadata. On a fresh
Supabase database, prefer running supabase/schema.sql (which also configures
RLS, triggers and storage). Alembic is used for incremental schema drift on
PostgreSQL once the base schema exists.
"""
import sqlalchemy as sa
from alembic import op

from app.core.database import Base

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)