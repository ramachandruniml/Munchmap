"""recipe embeddings

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-15
"""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("recipes", sa.Column("embedding", Vector(384), nullable=True))


def downgrade() -> None:
    op.drop_column("recipes", "embedding")
    op.execute("DROP EXTENSION IF EXISTS vector")
